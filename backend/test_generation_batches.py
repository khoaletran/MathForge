import json
import unittest
from unittest.mock import patch
from types import SimpleNamespace

from app.models.question import CognitiveLevel, ExamSlot, QuestionType
from app.services.ai_service import AIService
from app.services.matrix_service import MatrixService


def make_slot(slot_id, topic="Hình học không gian"):
    return ExamSlot(
        slot_id=slot_id, slot_number=int(slot_id), topic=topic,
        type=QuestionType.MULTIPLE_CHOICE, level=CognitiveLevel.NHAN_BIET,
    )


def answer(slot_id, stem):
    return {
        "slot_id": slot_id, "variation_angle": "Xác định đối tượng",
        "stem": stem, "solution": "Lời giải", "choices": ["A", "B", "C", "D"],
        "correct_index": 0,
    }


class FakeGemini:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.requests = []
        self.models = []

    def generate_content(self, **kwargs):
        self.models.append(kwargs["model"])
        self.requests.append((json.loads(kwargs["contents"]), kwargs["config"]))
        response = next(self.responses)
        if isinstance(response, Exception):
            raise response
        return SimpleNamespace(text=json.dumps(response))


class GenerationBatchTests(unittest.TestCase):
    def setUp(self):
        from app.services.ai_service import _research_lock, _research_cache, _research_quota_until

        with _research_lock:
            _research_cache.clear()
            _research_quota_until.clear()

    def test_batches_retry_only_rejected_slots_and_keep_matrix_order(self):
        pyramid = "Cho hình chóp $S.ABCD$. Tìm giao tuyến của hai mặt phẳng đã cho."
        cube = "Trong hình lập phương, cạnh nào vuông góc với đáy?"
        arithmetic = "Tính tổng hai số hạng đầu của cấp số cộng."
        fake = FakeGemini([
            [answer("3", pyramid), answer("1", pyramid), answer("9", pyramid)],
            [{"slot_id": "1", "accepted": True, "reason": ""}],
            [answer("3", cube)],
            [{"slot_id": "3", "accepted": True, "reason": ""}],
            [answer("2", arithmetic)],
            [{"slot_id": "2", "accepted": True, "reason": ""}],
        ])
        service = AIService()
        service.client = SimpleNamespace(models=fake)
        slots = [make_slot("1"), make_slot("2", "Dãy số"), make_slot("3")]
        questions = service.generate_questions(slots, 11)

        self.assertEqual([q.id for q in questions], ["1", "2", "3"])
        self.assertEqual([q.stem for q in questions], [pyramid, arithmetic, cube])
        generation_calls = [(p, c) for p, c in fake.requests if "quantity" in p]
        self.assertEqual([p["quantity"] for p, _ in generation_calls], [2, 1, 1])
        self.assertEqual([s["slot_id"] for s in generation_calls[1][0]["slots"]], ["3"])
        self.assertIn(pyramid, generation_calls[2][0]["excluded_stems"])
        self.assertEqual(generation_calls[0][1].temperature, 0.8)
        schema = generation_calls[0][1].response_json_schema
        self.assertIn("variation_angle", schema["items"]["required"])

    def test_grade_mismatch_and_bad_options_retry_then_use_local_template(self):
        slot = MatrixService.get_matrix_6_gk1().slots[0]
        invalid = answer(slot.slot_id, "Chọn phần tử của tập hợp A.")
        invalid["choices"] = ["A", "A", "C", "D"]
        fake = FakeGemini([
            [answer(slot.slot_id, "Tính đạo hàm của hàm số.")],
            [invalid],
            RuntimeError("API unavailable"),
        ])
        service = AIService()
        service.client = SimpleNamespace(models=fake)
        result = service.generate_questions([slot], 6)[0]

        self.assertTrue(result.template_id.startswith("g6_p1_set_elem_"))
        self.assertEqual(len(fake.requests), 3)

    def test_rejects_numeric_variants_even_with_the_same_slot_id(self):
        from app.services.template_registry import AntiDuplicateEngine

        slot = make_slot("1")
        service = AIService()
        first = service._parse_question(slot, answer("1", "Tính giá trị của $x^{2}$."), 11)
        second = service._parse_question(slot, answer("1", "Tính giá trị của $x^5$."), 11)
        self.assertTrue(AntiDuplicateEngine.is_duplicate(second, [first], similarity_threshold=1))

    def test_unreviewed_question_uses_local_template(self):
        slot = MatrixService.get_matrix_6_gk1().slots[0]
        for verdict in ([], RuntimeError("Không có kết quả rà soát")):
            with self.subTest(verdict=verdict):
                fake = FakeGemini([[answer(slot.slot_id, "Chọn phần tử của tập hợp A.")], verdict])
                service = AIService()
                service.client = SimpleNamespace(models=fake)
                result = service.generate_question(slot, 6, attempts=1)
                self.assertTrue(result.template_id.startswith("g6_p1_set_elem_"))

    def test_local_missing_template_fails_with_slot_details(self):
        service = AIService()
        service.client = None
        slot = make_slot("2", "Nội dung tự tạo chưa được hỗ trợ")
        with patch("app.services.ai_service.TemplateRegistry.get_templates_for_slot", return_value=[]):
            with self.assertRaisesRegex(ValueError, "Lớp 6.*Ô #2"):
                service.generate_question(slot, 6)


    def test_review_rejects_wrong_topic_and_retry_receives_reason(self):
        slot = MatrixService.get_matrix_6_gk1().slots[0]
        correct = "Cho tập hợp $A=\\{1,2,3\\}$. Số nào thuộc tập hợp $A$?"
        fake = FakeGemini([
            [answer(slot.slot_id, "Tính tổng hai số tự nhiên.")],
            [{"slot_id": slot.slot_id, "accepted": False, "reason": "Sai chủ đề."}],
            [answer(slot.slot_id, correct)],
            [{"slot_id": slot.slot_id, "accepted": True, "reason": ""}],
        ])
        service = AIService()
        service.client = SimpleNamespace(models=fake)
        self.assertEqual(service.generate_questions([slot], 6)[0].stem, correct)
        self.assertEqual(fake.requests[2][0]["feedback"], "Sai chủ đề.")

    def test_grade_7_rational_arithmetic_and_powers_have_distinct_templates(self):
        service = AIService()
        service.client = None
        for matrix, start in (
            (MatrixService.get_matrix_7_ck1(), 0),
            (MatrixService.get_matrix_7_gk1(), 1),
        ):
            slots = matrix.slots[start:start + 2]
            questions = service.generate_questions(slots, matrix.grade)
            self.assertEqual([q.id for q in questions], [s.slot_id for s in slots])
            self.assertEqual([q.template_id for q in questions], [
                "g7_p1_rational_add", "g7_p1_rational_power",
            ])
            for question in questions:
                self.assertEqual(len(set(question.choices)), 4)


    def test_provider_client_error_stops_requests_and_surfaces_http_status(self):
        from google.genai import errors
        from app.services.ai_service import GeminiUnavailable

        fake = FakeGemini([errors.ClientError(429, {"error": {
            "message": "Sensitive provider response", "status": "RESOURCE_EXHAUSTED",
        }})])
        service = AIService()
        service.backup_model = None
        service.client = SimpleNamespace(models=fake)
        local_slot = MatrixService.get_matrix_6_gk1().slots[0]
        self.assertTrue(service.generate_question(local_slot, 6).template_id)
        with patch("app.services.ai_service.TemplateRegistry.get_templates_for_slot", return_value=[]):
            with self.assertRaisesRegex(GeminiUnavailable, r"HTTP 429.*Sinh cục bộ") as context:
                service.generate_question(make_slot("99", "Chủ đề chưa có mẫu"), 6)
        self.assertNotIn("Sensitive", str(context.exception))
        self.assertEqual(len(fake.requests), 1)


    def test_server_errors_retry_with_backoff_then_fall_back(self):
        from unittest.mock import patch
        from google.genai import errors
        from app.services.ai_service import GeminiUnavailable

        fake = FakeGemini([errors.ServerError(503, {"error": {"message": "Unavailable"}})] * 3)
        service = AIService()
        service.backup_model = None
        service.client = SimpleNamespace(models=fake)
        local_slot = MatrixService.get_matrix_6_gk1().slots[0]
        with patch("app.services.ai_service.time.sleep") as sleep:
            self.assertTrue(service.generate_question(local_slot, 6).template_id)
        self.assertEqual([call.args[0] for call in sleep.call_args_list], [1, 2])
        with patch("app.services.ai_service.TemplateRegistry.get_templates_for_slot", return_value=[]):
            with self.assertRaisesRegex(GeminiUnavailable, "HTTP 503"):
                service.generate_question(make_slot("99", "Chủ đề chưa có mẫu"), 6)
        self.assertEqual(len(fake.requests), 3)

    def test_backup_model_serves_the_rest_of_the_request(self):
        from unittest.mock import patch
        from google.genai import errors

        slot = MatrixService.get_matrix_6_gk1().slots[0]
        fake = FakeGemini(
            [errors.ServerError(503, {"error": {"message": "Unavailable"}})] * 3
            + [[answer(slot.slot_id, "Chọn phần tử thuộc tập hợp A.")],
               [{"slot_id": slot.slot_id, "accepted": True, "reason": ""}]]
        )
        service = AIService()
        service.model = "gemini-3.8-flash"
        service.backup_model = "gemini-3.5-flash-lite"
        service.client = SimpleNamespace(models=fake)
        with patch("app.services.ai_service.time.sleep"):
            self.assertEqual(service.generate_question(slot, 6).id, slot.slot_id)
        self.assertEqual(fake.models, ["gemini-3.8-flash"] * 3 + ["gemini-3.5-flash-lite"] * 2)


    def test_missing_model_switches_to_backup_without_repeating_404(self):
        from google.genai import errors

        slot = MatrixService.get_matrix_6_gk1().slots[0]
        fake = FakeGemini([
            errors.ClientError(404, {"error": {"message": "Model unavailable"}}),
            [answer(slot.slot_id, "Chọn phần tử thuộc tập hợp A.")],
            [{"slot_id": slot.slot_id, "accepted": True, "reason": ""}],
        ])
        service = AIService()
        service.model = "primary"
        service.backup_model = "backup"
        service.client = SimpleNamespace(models=fake)
        self.assertEqual(service.generate_question(slot, 6).id, slot.slot_id)
        self.assertEqual(fake.models, ["primary", "backup", "backup"])


    def test_grade_7_rational_expression_essay_has_a_local_template(self):
        service = AIService()
        service.client = None
        for matrix in (MatrixService.get_matrix_7_gk1(), MatrixService.get_matrix_7_ck1()):
            slot = matrix.slots[12]
            for _ in range(30):
                result = service.generate_question(slot, 7)
                self.assertEqual(result.template_id, "g7_p2_rational_expression")
                self.assertEqual(sum(result.rubric.values()), slot.points)

    def test_default_quota_error_switches_to_flash_lite_backup(self):
        from unittest.mock import patch
        from google.genai import errors

        slot = MatrixService.get_matrix_6_gk1().slots[0]
        fake = FakeGemini([
            errors.ClientError(429, {"error": {"message": "Quota exceeded"}}),
            [answer(slot.slot_id, "Chọn phần tử thuộc tập hợp A.")],
            [{"slot_id": slot.slot_id, "accepted": True, "reason": ""}],
        ])
        with patch.dict("os.environ", {"GEMINI_MODEL": ""}):
            service = AIService()
        service.client = SimpleNamespace(models=fake)
        self.assertEqual(service.generate_question(slot, 6).id, slot.slot_id)
        self.assertEqual(fake.models, ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3.1-flash-lite"])

    def test_rolling_rpm_limit_is_shared_and_isolated_by_model(self):
        from app.services.ai_service import _wait_for_gemini_capacity

        with patch("app.services.ai_service.time.monotonic", side_effect=[0] * 7 + [60]), \
             patch("app.services.ai_service.time.sleep") as sleep:
            for _ in range(5):
                _wait_for_gemini_capacity(b"quota-regression", "gemini-3.8-flash")
            _wait_for_gemini_capacity(b"quota-regression", "gemini-3.5-flash-lite")
            _wait_for_gemini_capacity(b"quota-regression", "gemini-3.8-flash")
            sleep.assert_called_once_with(60)

    def test_web_reference_requires_grounded_sources(self):
        service = AIService()
        matrix = MatrixService.get_matrix_6_gk1()
        calls = []
        web = SimpleNamespace(uri="https://example.org/exam", title="De Toan 6")
        metadata = SimpleNamespace(
            grounding_supports=[SimpleNamespace(grounding_chunk_indices=[0])],
            grounding_chunks=[SimpleNamespace(web=web)],
        )
        def generate_content(**kwargs):
            calls.append(kwargs["model"])
            return SimpleNamespace(
                text="Referenced difficulty summary",
                candidates=[SimpleNamespace(grounding_metadata=metadata)],
            )

        generate = SimpleNamespace(generate_content=generate_content)
        service.client = SimpleNamespace(models=generate)
        service.research_exam(matrix)
        self.assertEqual(service.exam_reference, "Referenced difficulty summary")
        self.assertEqual(service.reference_sources, [{"url": web.uri, "title": web.title}])
        another_service = AIService()
        another_service.client = service.client
        another_service.research_exam(matrix)
        self.assertEqual(another_service.reference_sources, service.reference_sources)
        self.assertEqual(len(calls), 1)

    def test_web_reference_switches_model_on_quota_error(self):
        from google.genai import errors

        service = AIService()
        service.model = "main"
        service.backup_model = "backup"
        models = []

        def generate_content(**kwargs):
            models.append(kwargs["model"])
            if kwargs["model"] == "main":
                raise errors.ClientError(429, {"error": {"message": "Search quota exceeded"}})
            return SimpleNamespace(text="Summary", candidates=[SimpleNamespace(
                grounding_metadata=SimpleNamespace(
                    grounding_supports=[SimpleNamespace(grounding_chunk_indices=[0])],
                    grounding_chunks=[SimpleNamespace(web=SimpleNamespace(
                        uri="https://example.org/exam", title="De Toan 6",
                    ))],
                ),
            )])

        service.client = SimpleNamespace(models=SimpleNamespace(generate_content=generate_content))
        service.research_exam(MatrixService.get_matrix_6_gk1())
        self.assertEqual(models, ["main", "backup"])
        self.assertEqual(service.model, "main")
        self.assertEqual(service.reference_sources[0]["url"], "https://example.org/exam")

    def test_web_research_reuses_sources_and_pauses_after_quota_errors(self):
        from google.genai import errors

        calls = []

        def quota_error(**kwargs):
            calls.append(kwargs["model"])
            raise errors.ClientError(429, {"error": {"message": "Quota exceeded"}})

        matrix = MatrixService.get_matrix_6_gk1()
        service = AIService()
        service.client = SimpleNamespace(models=SimpleNamespace(generate_content=quota_error))
        service.research_exam(matrix)
        second = AIService()
        second.client = service.client
        second.research_exam(matrix)
        self.assertEqual(calls, [service.model, service.backup_model])
        self.assertEqual(second.reference_sources, [])

    def test_generated_vietnamese_and_fraction_format(self):
        service = AIService()
        slot = make_slot("1")
        malformed = answer("1", "Cho ham so $y=-x^3+3x^2-1$. Viet phuong trinh tiep tuyen tai $x_0=2$.")
        with self.assertRaisesRegex(ValueError, "tiếng Việt không dấu"):
            service._parse_question(slot, malformed, 11)

        for stem in (
            "Trong cac so sau, so nao la so nguyen to?",
            "Số nguyên biểu thị nhiet độ dưới $0^\\circ C$ là $5^\\circ C$ được viết là:",
        ):
            with self.subTest(stem=stem), self.assertRaisesRegex(ValueError, "tiếng Việt không dấu"):
                service._parse_question(slot, answer("1", stem), 6)
        service._parse_question(slot, answer("1", "Trong các số sau, số nào là số nguyên tố?"), 6)

        formatted = answer("1", "Cho hàm số $y=-x^3+3x^2-1$. Viết phương trình tiếp tuyến tại $x_0=2$.")
        formatted["choices"] = [r"\frac{3}{8}", r"**\frac{7}{8}**", r"$\frac{5}{8}$", r"\frac{1}{2}"]
        question = service._parse_question(slot, formatted, 11)
        self.assertEqual(question.choices, [r"$\frac{3}{8}$", r"$\frac{7}{8}$", r"$\frac{5}{8}$", r"$\frac{1}{2}$"])

        formatted["choices"][0] = "Chọn `\\frac{3}{8}`"
        with self.assertRaisesRegex(ValueError, "Markdown"):
            service._parse_question(slot, formatted, 11)

        formatted["choices"][0] = r"\frac{3}{8}"
        formatted["stem"] = "Cho hàm số $y=-x3+3x2-1$. Viết phương trình tiếp tuyến."
        with self.assertRaisesRegex(ValueError, "số mũ"):
            service._parse_question(slot, formatted, 11)
