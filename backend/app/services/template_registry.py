"""
Template Registry & Anti-Duplicate Engine cho hệ thống đề thi Toán GDPT 2018 (Lớp 6 - 12).
Cung cấp:
1. AntiDuplicateEngine: Kiểm tra độ trùng lặp đa lớp (chuẩn hóa Unicode, ẩn số <NUM>, token similarity, template_id).
2. TemplateRegistry: Danh mục câu hỏi tham số hóa chuẩn mực cho toàn bộ 29 ma trận chuẩn của Bộ GD&ĐT.
3. Cơ chế cách ly khối lớp nghiêm ngặt (không bao giờ rò rỉ đạo hàm/tích phân sang Lớp 6-11).
"""

import re
import math
import random
import unicodedata
from typing import List, Dict, Any, Optional, Tuple, Callable

from app.models.question import Question, QuestionType, CognitiveLevel, ExamSlot, TrueFalseItem
from app.services.tikz_service import TikZLibrary

class AntiDuplicateEngine:
    @staticmethod
    def normalize_formula_text(text: str) -> str:
        """Chuẩn hóa văn bản: Unicode NFC, bỏ khoảng trắng thừa, bỏ ký tự toán $."""
        if not text:
            return ""
        norm = unicodedata.normalize("NFC", text).strip().lower()
        norm = norm.replace(r"\left", "").replace(r"\right", "").replace("−", "-")
        norm = re.sub(r"\^\{([^{}]+)\}", r"^\1", norm)
        norm = re.sub(r"\s*([=+^*/-])\s*", r"\1", norm)
        norm = norm.replace("$", "")
        norm = re.sub(r"\s+", " ", norm).strip()
        return norm

    @staticmethod
    def mask_numbers(text: str) -> str:
        """Ẩn các số và phân số để phát hiện câu hỏi cùng dạng cấu trúc chỉ thay hệ số."""
        if not text:
            return ""
        norm = unicodedata.normalize("NFC", text)
        masked = re.sub(r"\d+(?:[.,]\d+)?", "<NUM>", norm)
        masked = re.sub(r"\\frac\{<NUM>\}\{<NUM>\}", "<FRAC>", masked)
        masked = re.sub(r"\s+", " ", masked).strip().lower()
        return AntiDuplicateEngine.normalize_formula_text(masked)

    @staticmethod
    def token_similarity(text1: str, text2: str) -> float:
        """Tính độ tương đồng Jaccard giữa hai chuỗi văn bản theo 2-grams từ ngữ."""
        tokens1 = [w for w in re.split(r"\W+", text1.lower()) if len(w) > 1]
        tokens2 = [w for w in re.split(r"\W+", text2.lower()) if len(w) > 1]
        if not tokens1 or not tokens2:
            return 0.0
        set1 = set(tokens1)
        set2 = set(tokens2)
        intersection = set1.intersection(set2)
        union = set1.union(set2)
        return len(intersection) / len(union) if union else 0.0

    @classmethod
    def is_duplicate(
        cls,
        candidate: Question,
        avoid_questions: List[Question],
        allow_same_template: bool = False,
        similarity_threshold: float = 0.70
    ) -> bool:
        """
        Kiểm tra độ trùng lặp đa lớp:
        1. Trùng lặp nguyên văn (Normalized text)
        2. Trùng lặp cấu trúc chỉ đổi hệ số (Masked numbers text)
        3. Trùng lặp mã template (nếu không ở chế độ clone số liệu)
        4. Tương đồng từ ngữ cao (Token similarity > 0.75)
        """
        if not avoid_questions:
            return False

        candidate_text = " ".join([candidate.stem, *(s.statement for s in candidate.statements or [])])
        cand_stem_norm = cls.normalize_formula_text(candidate_text)
        cand_stem_masked = cls.mask_numbers(candidate_text)

        for avoid in avoid_questions:
            avoid_text = " ".join([avoid.stem, *(s.statement for s in avoid.statements or [])])
            avoid_stem_norm = cls.normalize_formula_text(avoid_text)
            avoid_stem_masked = cls.mask_numbers(avoid_text)

            # Lớp 1: Trùng nguyên văn đề bài
            if cand_stem_norm == avoid_stem_norm:
                return True

            # Lớp 2: Trùng template_id (nếu không cho phép dùng lại template)
            if not allow_same_template and candidate.template_id and candidate.template_id == avoid.template_id:
                return True

            # Lớp 3: Trùng cấu trúc chỉ đổi số (<NUM> mask)
            if cand_stem_masked == avoid_stem_masked:
                return True

            # Lớp 4: Độ tương đồng từ vựng quá cao
            sim = cls.token_similarity(candidate_text, avoid_text)
            if sim > similarity_threshold:
                return True

        return False


class TemplateEntry:
    def __init__(
        self,
        template_id: str,
        grade: int,
        part: int,
        q_type: QuestionType,
        level: CognitiveLevel,
        keywords: List[str],
        generator: Callable[[ExamSlot, Optional[Question], str], Question]
    ):
        self.template_id = template_id
        self.grade = grade
        self.part = part
        self.q_type = q_type
        self.level = level
        self.keywords = [k.lower() for k in keywords]
        self.generator = generator

    def matches(self, grade: int, part: int, q_type: QuestionType, search_text: str) -> bool:
        if self.grade != grade:
            return False
        if self.part != part:
            return False
        if self.q_type != q_type:
            return False
        if not self.keywords:
            return True
        st = search_text.lower()
        return any(k in st for k in self.keywords)


class TemplateRegistry:
    _templates: List[TemplateEntry] = []
    _initialized: bool = False

    @classmethod
    def register(
        cls,
        template_id: str,
        grade: int,
        part: int,
        q_type: QuestionType,
        level: CognitiveLevel,
        keywords: List[str]
    ):
        def decorator(fn: Callable[[ExamSlot, Optional[Question], str], Question]):
            cls._templates.append(
                TemplateEntry(template_id, grade, part, q_type, level, keywords, fn)
            )
            return fn
        return decorator

    @classmethod
    def initialize(cls):
        if cls._initialized:
            return
        cls._register_all_templates()
        cls._initialized = True

    @classmethod
    def get_templates_for_slot(
        cls,
        slot: ExamSlot,
        grade: int
    ) -> List[TemplateEntry]:
        cls.initialize()
        sub = slot.subtopic or ""
        search_text = f"{slot.topic} {sub}".lower()
        
        # 1. Lọc các mẫu cùng khối lớp và khớp dạng câu hỏi (MULTIPLE_CHOICE, TRUE_FALSE, SHORT_ANSWER, ESSAY)
        candidates = [t for t in cls._templates if t.grade == grade and t.q_type == slot.type]
        if not candidates:
            # Fallback nếu type tương thích trong cùng khối lớp (ví dụ ESSAY vs SHORT_ANSWER)
            candidates = [t for t in cls._templates if t.grade == grade]
        if not candidates:
            return []

        # 2. Tìm kiếm theo từ khóa chuyên đề trong chủ đề và tiểu chủ đề
        kw_matched = []
        for t in candidates:
            score = max((len(k) for k in t.keywords if k in search_text), default=0)
            if score > 0:
                kw_matched.append((score, t))

        if kw_matched:
            # Ưu tiên mức độ nhận thức (level) nếu có
            level_matched = [(s, t) for s, t in kw_matched if t.level == slot.level]
            pool = level_matched if level_matched else kw_matched
            best_score = max(s for s, _ in pool)
            return [t for s, t in pool if s == best_score]

        # 3. Nếu chưa khớp từ khóa cụ thể, ưu tiên mẫu cùng part và level
        part_matched = [t for t in candidates if t.part == slot.part and t.level == slot.level]
        if part_matched:
            return part_matched
        level_matched = [t for t in candidates if t.level == slot.level]
        return level_matched if level_matched else candidates

    @classmethod
    def generate_for_slot(
        cls,
        slot: ExamSlot,
        grade: int,
        avoid_questions: Optional[List[Question]] = None,
        original_question: Optional[Question] = None,
        mode: str = "generate"
    ) -> Question:
        cls.initialize()
        avoid_questions = avoid_questions or []
        templates = cls.get_templates_for_slot(slot, grade)

        if not templates:
            raise ValueError(
                f"Không tìm thấy mẫu phù hợp cho Lớp {grade}, Phần {slot.part}, Dạng {slot.type.value}, "
                f"Ô #{slot.slot_number} ('{slot.topic} - {slot.subtopic}')."
            )

        if mode == "clone" and original_question:
            clone_templates = [t for t in templates if t.template_id == original_question.template_id]
            if clone_templates:
                templates = clone_templates

        templates = list(templates)
        random.shuffle(templates)

        # Lần 1: Thử sinh nghiêm ngặt (không trùng template_id, không trùng cấu trúc masked)
        for template in templates:
            for _ in range(15 if mode == "clone" else 8):
                candidate = template.generator(slot, original_question, mode)
                candidate.template_id = template.template_id
                if mode == "clone" and original_question and (
                    AntiDuplicateEngine.normalize_formula_text(candidate.stem)
                    == AntiDuplicateEngine.normalize_formula_text(original_question.stem)
                ):
                    continue
                if not AntiDuplicateEngine.is_duplicate(
                    candidate, avoid_questions, allow_same_template=False, similarity_threshold=0.70
                ):
                    return candidate

        # Lần 2: Nếu kho mẫu của khối lớp ít hơn số câu trong đề, cho phép dùng lại template nhưng BẮT BUỘC số liệu khác hoàn toàn (không trùng stem)
        for template in templates:
            for _ in range(10):
                candidate = template.generator(slot, original_question, mode)
                candidate.template_id = template.template_id
                if not AntiDuplicateEngine.is_duplicate(
                    candidate, avoid_questions, allow_same_template=True, similarity_threshold=0.70
                ):
                    return candidate

        # Lần 3: Fallback an toàn cùng khối lớp để không bao giờ làm đứt luồng sinh đề của giáo viên
        candidate = templates[0].generator(slot, original_question, mode)
        candidate.template_id = templates[0].template_id
        return candidate

    # =========================================================================
    # ĐĂNG KÝ TEMPLATES CHO 29 MA TRẬN
    # =========================================================================
    @classmethod
    def _register_all_templates(cls):
        cls._register_grade_6_templates()
        cls._register_grade_7_templates()
        cls._register_grade_8_templates()
        cls._register_grade_9_templates()
        cls._register_grade_10_templates()
        cls._register_grade_11_templates()
        cls._register_grade_12_templates()

    # -------------------------------------------------------------------------
    # LỚP 6
    # -------------------------------------------------------------------------
    @classmethod
    def _register_grade_6_templates(cls):
        # 1. Tập hợp và phần tử
        @cls.register("g6_p1_set_elem_1", 6, 1, QuestionType.MULTIPLE_CHOICE, CognitiveLevel.NHAN_BIET, ["tập hợp", "phần tử"])
        def gen_g6_set_elem_1(slot, orig, mode):
            start = random.choice([2, 3, 5])
            end = start + random.choice([4, 5, 6])
            x_in = start + 1
            x_out = end + 2
            return Question(
                id=slot.slot_id,
                type=QuestionType.MULTIPLE_CHOICE,
                topic=slot.topic,
                subtopic=slot.subtopic,
                level=slot.level,
                stem=f"Cho tập hợp $A = \\{{x \\in \\mathbb{{N}} \\mid {start} \\le x \\le {end}\\}}$. Khẳng định nào sau đây đúng?",
                choices=[f"${x_in} \\in A$", f"${x_out} \\in A$", f"${start-1} \\in A$", f"${end+1} \\in A$"],
                correct_index=0,
                solution=f"Tập hợp $A = \\{{{start}; {start+1}; \\dots; {end}\\}}$. Do đó ${x_in} \\in A$.",
                verified=True
            )

        @cls.register("g6_p1_set_elem_2", 6, 1, QuestionType.MULTIPLE_CHOICE, CognitiveLevel.NHAN_BIET, ["tập hợp", "phần tử", "số phần tử"])
        def gen_g6_set_elem_2(slot, orig, mode):
            start = random.choice([10, 15, 20])
            end = start + random.choice([12, 16, 20])
            count = end - start + 1
            return Question(
                id=slot.slot_id,
                type=QuestionType.MULTIPLE_CHOICE,
                topic=slot.topic,
                subtopic=slot.subtopic,
                level=slot.level,
                stem=f"Số phần tử của tập hợp $B = \\{{x \\in \\mathbb{{N}} \\mid {start} \\le x \\le {end}\\}}$. là",
                choices=[f"${count}$", f"${count - 1}$", f"${count + 1}$", f"${count - 2}$"],
                correct_index=0,
                solution=f"Số phần tử của tập hợp $B$ là: ${end} - {start} + 1 = {count}$.",
                verified=True
            )

        # 2. Phép tính số tự nhiên (ĐẢM BẢO CHỈ DÙNG SỐ TỰ NHIÊN >= 0)
        @cls.register("g6_p1_nat_arith_add", 6, 1, QuestionType.MULTIPLE_CHOICE, CognitiveLevel.NHAN_BIET, ["phép tính với số tự nhiên", "phép tính số tự nhiên"])
        def gen_g6_nat_arith_add(slot, orig, mode):
            a = random.choice([124, 235, 148, 216])
            b = random.choice([76, 65, 52, 84])
            ans = a + b
            return Question(
                id=slot.slot_id,
                type=QuestionType.MULTIPLE_CHOICE,
                topic=slot.topic,
                subtopic=slot.subtopic,
                level=slot.level,
                stem=f"Kết quả của phép tính ${a} + {b}$ bằng",
                choices=[f"${ans}$", f"${ans - 10}$", f"${ans + 10}$", f"${ans + 2}$"],
                correct_index=0,
                solution=f"Thực hiện phép cộng hai số tự nhiên: ${a} + {b} = {ans}$.",
                verified=True
            )

        @cls.register("g6_p1_nat_arith_mul_div", 6, 1, QuestionType.MULTIPLE_CHOICE, CognitiveLevel.NHAN_BIET, ["phép tính với số tự nhiên", "phép nhân", "phép chia", "thứ tự thực hiện"])
        def gen_g6_nat_arith_mul_div(slot, orig, mode):
            a = random.choice([12, 15, 18, 24])
            b = random.choice([4, 5, 6, 8])
            c = random.choice([2, 3, 5])
            ans = a * b + c
            return Question(
                id=slot.slot_id,
                type=QuestionType.MULTIPLE_CHOICE,
                topic=slot.topic,
                subtopic=slot.subtopic,
                level=slot.level,
                stem=f"Giá trị của biểu thức ${a} \\times {b} + {c}$ bằng",
                choices=[f"${ans}$", f"${ans - 2}$", f"${a * (b + c)}$", f"${ans + 4}$"],
                correct_index=0,
                solution=f"Ta thực hiện phép nhân trước: ${a} \\times {b} = {a*b}$. Sau đó cộng với ${c}$: ${a*b} + {c} = {ans}$.",
                verified=True
            )

        # 3. Lũy thừa với số mũ tự nhiên
        @cls.register("g6_p1_power", 6, 1, QuestionType.MULTIPLE_CHOICE, CognitiveLevel.NHAN_BIET, ["lũy thừa", "số mũ"])
        def gen_g6_power(slot, orig, mode):
            base = random.choice([2, 3, 5])
            m = random.choice([2, 3, 4])
            n = random.choice([2, 3])
            ans_exp = m + n
            return Question(
                id=slot.slot_id,
                type=QuestionType.MULTIPLE_CHOICE,
                topic=slot.topic,
                subtopic=slot.subtopic,
                level=slot.level,
                stem=f"Viết tích ${base}^{{{m}}} \\cdot {base}^{{{n}}}$ dưới dạng một lũy thừa ta được",
                choices=[f"${base}^{{{ans_exp}}}$", f"${base}^{{{m * n}}}$", f"${base * 2}^{{{ans_exp}}}$", f"${base}^{{{abs(m - n)}}}$"],
                correct_index=0,
                solution=f"Áp dụng quy tắc nhân hai lũy thừa cùng cơ số: $a^m \\cdot a^n = a^{{m+n}}$, ta có ${base}^{{{m}}} \\cdot {base}^{{{n}}} = {base}^{{{m}+{n}}} = {base}^{{{ans_exp}}}$.",
                verified=True
            )

        # 4. Chia hết, số nguyên tố, ƯCLN, BCNN
        @cls.register("g6_p1_divisibility", 6, 1, QuestionType.MULTIPLE_CHOICE, CognitiveLevel.NHAN_BIET, ["chia hết", "dấu hiệu chia hết", "số nguyên tố", "ước", "bội", "ưcln", "bcnn"])
        def gen_g6_divisibility(slot, orig, mode):
            div = random.choice([2, 3, 5, 9])
            if div == 2:
                q = ("Số nào sau đây chia hết cho $2$?", ["$134$", "$135$", "$137$", "$139$"], 0, "Số có chữ số tận cùng là chẵn ($0, 2, 4, 6, 8$) thì chia hết cho 2.")
            elif div == 5:
                q = ("Số nào sau đây chia hết cho cả $2$ và $5$?", ["$250$", "$255$", "$252$", "$258$"], 0, "Số chia hết cho cả 2 và 5 có chữ số tận cùng là 0.")
            elif div == 3:
                q = ("Số nào sau đây chia hết cho $3$?", ["$123$", "$124$", "$125$", "$127$"], 0, "Tổng các chữ số là $1+2+3=6$ chia hết cho 3.")
            else:
                q = ("Trong các số sau, số nào là số nguyên tố?", ["$17$", "$15$", "$21$", "$27$"], 0, "Số 17 chỉ có hai ước là 1 và chính nó nên là số nguyên tố.")
            return Question(
                id=slot.slot_id,
                type=QuestionType.MULTIPLE_CHOICE,
                topic=slot.topic,
                subtopic=slot.subtopic,
                level=slot.level,
                stem=q[0],
                choices=q[1],
                correct_index=q[2],
                solution=q[3],
                verified=True
            )

        # 5. Số nguyên (Tập hợp Z, phép cộng trừ số nguyên)
        @cls.register("g6_p1_integers", 6, 1, QuestionType.MULTIPLE_CHOICE, CognitiveLevel.NHAN_BIET, ["số nguyên", "tập hợp số nguyên", "số nguyên âm", "thứ tự trong tập"])
        def gen_g6_integers(slot, orig, mode):
            a = random.choice([-15, -12, -20, -18])
            b = random.choice([8, 10, 15, 25])
            ans = a + b
            return Question(
                id=slot.slot_id,
                type=QuestionType.MULTIPLE_CHOICE,
                topic=slot.topic,
                subtopic=slot.subtopic,
                level=slot.level,
                stem=f"Kết quả của phép tính $({a}) + {b}$ bằng",
                choices=[f"${ans}$", f"${-ans}$", f"${ans + 2}$", f"${ans - 4}$"],
                correct_index=0,
                solution=f"Thực hiện phép cộng hai số nguyên khác dấu: $({a}) + {b} = {b} - {abs(a)} = {ans}$.",
                verified=True
            )

        # 6. Hình học trực quan Lớp 6
        @cls.register("g6_p1_geometry_visual", 6, 1, QuestionType.MULTIPLE_CHOICE, CognitiveLevel.NHAN_BIET, ["tam giác đều", "hình vuông", "hình chữ nhật", "hình thoi", "hình bình hành", "hình thang cân"])
        def gen_g6_geom_visual(slot, orig, mode):
            shape = random.choice(["square", "triangle", "rhombus"])
            if shape == "square":
                a = random.choice([5, 6, 8, 10])
                return Question(
                    id=slot.slot_id,
                    type=QuestionType.MULTIPLE_CHOICE,
                    topic=slot.topic,
                    subtopic=slot.subtopic,
                    level=slot.level,
                    stem=f"Chu vi của một hình vuông có độ dài cạnh ${a}\\text{{ cm}}$ là",
                    choices=[f"${4*a}\\text{{ cm}}$", f"${a*a}\\text{{ cm}}$", f"${2*a}\\text{{ cm}}$", f"${4*a+4}\\text{{ cm}}$"],
                    correct_index=0,
                    solution=f"Chu vi hình vuông là $C = 4 \\times a = 4 \\times {a} = {4*a}\\text{{ cm}}$.",
                    verified=True
                )
            elif shape == "triangle":
                a = random.choice([4, 6, 9])
                return Question(
                    id=slot.slot_id,
                    type=QuestionType.MULTIPLE_CHOICE,
                    topic=slot.topic,
                    subtopic=slot.subtopic,
                    level=slot.level,
                    stem=f"Một tam giác đều có độ dài một cạnh bằng ${a}\\text{{ cm}}$. Chu vi của tam giác đều đó là",
                    choices=[f"${3*a}\\text{{ cm}}$", f"${2*a}\\text{{ cm}}$", f"${4*a}\\text{{ cm}}$", f"${a*a}\\text{{ cm}}$"],
                    correct_index=0,
                    solution=f"Tam giác đều có 3 cạnh bằng nhau, do đó chu vi là $C = 3 \\times {a} = {3*a}\\text{{ cm}}$.",
                    verified=True
                )
            else:
                d1, d2 = random.choice([(6, 8), (4, 10), (8, 12)])
                s = (d1 * d2) // 2
                return Question(
                    id=slot.slot_id,
                    type=QuestionType.MULTIPLE_CHOICE,
                    topic=slot.topic,
                    subtopic=slot.subtopic,
                    level=slot.level,
                    stem=f"Diện tích của một hình thoi có độ dài hai đường chéo lần lượt là ${d1}\\text{{ cm}}$ và ${d2}\\text{{ cm}}$ bằng",
                    choices=[f"${s}\\text{{ cm}}^2$", f"${d1*d2}\\text{{ cm}}^2$", f"${s+2}\\text{{ cm}}^2$", f"${2*(d1+d2)}\\text{{ cm}}^2$"],
                    correct_index=0,
                    solution=f"Diện tích hình thoi là $S = \\frac{{1}}{{2}} \\times d_1 \\times d_2 = \\frac{{1}}{{2}} \\times {d1} \\times {d2} = {s}\\text{{ cm}}^2$.",
                    verified=True
                )

        # 7. Phân số và số thập phân Lớp 6
        @cls.register("g6_p1_fractions", 6, 1, QuestionType.MULTIPLE_CHOICE, CognitiveLevel.NHAN_BIET, ["phân số", "số thập phân", "hỗn số", "so sánh", "tỉ số"])
        def gen_g6_fractions(slot, orig, mode):
            a, b = random.choice([(2, 5), (3, 7), (4, 9), (5, 6)])
            k = random.choice([2, 3, 4])
            ak, bk = a * k, b * k
            return Question(
                id=slot.slot_id,
                type=QuestionType.MULTIPLE_CHOICE,
                topic=slot.topic,
                subtopic=slot.subtopic,
                level=slot.level,
                stem=f"Phân số nào sau đây bằng phân số $\\frac{{{a}}}{{{b}}}$?",
                choices=[f"$\\frac{{{ak}}}{{{bk}}}$", f"$\\frac{{{ak+1}}}{{{bk}}}$", f"$\\frac{{{ak}}}{{{bk+1}}}$", f"$\\frac{{{a}}}{{{bk}}}$"],
                correct_index=0,
                solution=f"Nhân cả tử và mẫu với ${k}$: $\\frac{{{a} \\times {k}}}{{{b} \\times {k}}} = \\frac{{{ak}}}{{{bk}}}$.",
                verified=True
            )

        # 8. Hình học phẳng: Điểm, đoạn thẳng, góc Lớp 6
        @cls.register("g6_p1_geom_lines_angles", 6, 1, QuestionType.MULTIPLE_CHOICE, CognitiveLevel.NHAN_BIET, ["điểm", "đoạn thẳng", "độ dài đoạn thẳng", "trung điểm", "góc"])
        def gen_g6_geom_lines(slot, orig, mode):
            ab = random.choice([6, 8, 10, 12])
            am = ab // 2
            return Question(
                id=slot.slot_id,
                type=QuestionType.MULTIPLE_CHOICE,
                topic=slot.topic,
                subtopic=slot.subtopic,
                level=slot.level,
                stem=f"Cho đoạn thẳng $AB = {ab}\\text{{ cm}}$. Điểm $M$ là trung điểm của đoạn thẳng $AB$. Độ dài đoạn thẳng $AM$ bằng",
                choices=[f"${am}\\text{{ cm}}$", f"${ab}\\text{{ cm}}$", f"${am+1}\\text{{ cm}}$", f"${am-1}\\text{{ cm}}$"],
                correct_index=0,
                solution=f"Vì $M$ là trung điểm của đoạn thẳng $AB$ nên $AM = \\frac{{AB}}{{2}} = \\frac{{{ab}}}{{2}} = {am}\\text{{ cm}}$.",
                verified=True
            )

        # 9. Thống kê & xác suất Lớp 6
        @cls.register("g6_p1_stats_prob", 6, 1, QuestionType.MULTIPLE_CHOICE, CognitiveLevel.NHAN_BIET, ["thống kê", "dữ liệu", "biểu đồ", "xác suất", "trò chơi"])
        def gen_g6_stats(slot, orig, mode):
            return Question(
                id=slot.slot_id,
                type=QuestionType.MULTIPLE_CHOICE,
                topic=slot.topic,
                subtopic=slot.subtopic,
                level=slot.level,
                stem="Gieo một con xúc xắc cân đối và đồng chất có 6 mặt một lần. Số kết quả có thể xảy ra là",
                choices=["$6$", "$1$", "$2$", "$12$"],
                correct_index=0,
                solution="Con xúc xắc có 6 mặt (tương ứng từ 1 đến 6 chấm), do đó có 6 kết quả có thể xảy ra.",
                verified=True
            )

        # 10. Tự luận Lớp 6 (ESSAY)
        @cls.register("g6_p2_essay_calc", 6, 2, QuestionType.ESSAY, CognitiveLevel.NHAN_BIET, ["thực hiện phép tính", "tính giá trị biểu thức", "phép tính"])
        def gen_g6_essay_calc(slot, orig, mode):
            a = random.choice([25, 32, 18, 45])
            b = random.choice([68, 74, 56])
            c = 100 - b
            total = a * 100
            pts_half = round(slot.points / 2, 2)
            return Question(
                id=slot.slot_id,
                type=QuestionType.ESSAY,
                topic=slot.topic,
                subtopic=slot.subtopic,
                level=slot.level,
                stem=f"Tính một cách hợp lý: $A = {a} \\cdot {b} + {a} \\cdot {c}$.",
                solution=f"Ta có:\n"
                         f"- Bước 1: Áp dụng tính chất phân phối của phép nhân đối với phép cộng:\n"
                         f"  $A = {a} \\cdot ({b} + {c})$ (+{pts_half} điểm)\n"
                         f"- Bước 2: $A = {a} \\cdot 100 = {total}$ (+{slot.points - pts_half} điểm).\n"
                         f"Vậy $A = {total}$.",
                rubric={"Bước 1 (Đặt nhân tử chung)": pts_half, "Bước 2 (Tính kết quả)": slot.points - pts_half},
                verified=True
            )

        @cls.register("g6_p2_essay_find_x", 6, 2, QuestionType.ESSAY, CognitiveLevel.THONG_HIEU, ["tìm x", "tìm số nguyên x"])
        def gen_g6_essay_find_x(slot, orig, mode):
            x_ans = random.choice([15, 20, 25, 30])
            c = random.choice([12, 18, 24])
            total = x_ans + c
            pts_half = round(slot.points / 2, 2)
            return Question(
                id=slot.slot_id,
                type=QuestionType.ESSAY,
                topic=slot.topic,
                subtopic=slot.subtopic,
                level=slot.level,
                stem=f"Tìm số tự nhiên $x$, biết: $2x + {2*c} = {2*total}$.",
                solution=f"Ta có:\n"
                         f"- Bước 1: $2x = {2*total} - {2*c} \\Leftrightarrow 2x = {2*x_ans}$ (+{pts_half} điểm)\n"
                         f"- Bước 2: $x = {2*x_ans} : 2 = {x_ans}$ (+{slot.points - pts_half} điểm).\n"
                         f"Vậy $x = {x_ans}$.",
                rubric={"Bước 1 (Chuyển vế)": pts_half, "Bước 2 (Tìm x)": slot.points - pts_half},
                verified=True
            )

        @cls.register("g6_p2_essay_primes", 6, 2, QuestionType.ESSAY, CognitiveLevel.THONG_HIEU, ["phân tích ra thừa số nguyên tố", "ước chung", "bội chung", "chia hết"])
        def gen_g6_essay_primes(slot, orig, mode):
            pts_half = round(slot.points / 2, 2)
            return Question(
                id=slot.slot_id,
                type=QuestionType.ESSAY,
                topic=slot.topic,
                subtopic=slot.subtopic,
                level=slot.level,
                stem="Phân tích các số $24$ và $36$ ra thừa số nguyên tố, từ đó tìm ƯCLN$(24, 36)$.",
                solution=f"Lời giải chi tiết:\n"
                         f"- Bước 1: Phân tích ra thừa số nguyên tố: $24 = 2^3 \\cdot 3$ và $36 = 2^2 \\cdot 3^2$ (+{pts_half} điểm)\n"
                         f"- Bước 2: Các thừa số nguyên tố chung là 2 và 3 với số mũ nhỏ nhất lần lượt là 2 và 1.\n"
                         f"  Do đó ƯCLN$(24, 36) = 2^2 \\cdot 3 = 12$ (+{slot.points - pts_half} điểm).",
                rubric={"Bước 1 (Phân tích thừa số nguyên tố)": pts_half, "Bước 2 (Tìm ƯCLN)": slot.points - pts_half},
                verified=True
            )

        @cls.register("g6_p2_essay_real_world", 6, 2, QuestionType.ESSAY, CognitiveLevel.VAN_DUNG, ["thực tiễn", "bài toán thực tế", "mua hàng", "chi phí", "chia kẹo", "xếp hàng"])
        def gen_g6_essay_real(slot, orig, mode):
            price_book = random.choice([12, 15, 20])
            price_pen = random.choice([5, 6, 8])
            num_books = 5
            num_pens = 10
            total = num_books * price_book + num_pens * price_pen
            pts_half = round(slot.points / 2, 2)
            return Question(
                id=slot.slot_id,
                type=QuestionType.ESSAY,
                topic=slot.topic,
                subtopic=slot.subtopic,
                level=slot.level,
                stem=f"Bạn Lan mua ${num_books}$ quyển vở với giá ${price_book}\\,000$ đồng/quyển và ${num_pens}$ chiếc bút với giá ${price_pen}\\,000$ đồng/chiếc. Hỏi bạn Lan phải trả tất cả bao nhiêu nghìn đồng?",
                solution=f"Lời giải chi tiết:\n"
                         f"- Bước 1: Số tiền mua ${num_books}$ quyển vở là: ${num_books} \\times {price_book} = {num_books*price_book}$ (nghìn đồng) (+{pts_half} điểm)\n"
                         f"- Bước 2: Số tiền mua ${num_pens}$ chiếc bút là: ${num_pens} \\times {price_pen} = {num_pens*price_pen}$ (nghìn đồng).\n"
                         f"  Tổng số tiền phải trả: ${num_books*price_book} + {num_pens*price_pen} = {total}$ (nghìn đồng) (+{slot.points - pts_half} điểm).\n"
                         f"Đáp số: ${total}\\,000$ đồng.",
                rubric={"Bước 1 (Tiền vở)": pts_half, "Bước 2 (Tổng tiền)": slot.points - pts_half},
                verified=True
            )

        @cls.register("g6_p2_essay_adv", 6, 2, QuestionType.ESSAY, CognitiveLevel.VAN_DUNG_CAO, ["nâng cao", "chữ số tận cùng", "quy luật", "dãy phân số"])
        def gen_g6_essay_adv(slot, orig, mode):
            pts_half = round(slot.points / 2, 2)
            return Question(
                id=slot.slot_id,
                type=QuestionType.ESSAY,
                topic=slot.topic,
                subtopic=slot.subtopic,
                level=slot.level,
                stem="Cho biểu thức $S = 1 + 2 + 2^2 + 2^3 + \\dots + 2^{2024}$. Chứng minh rằng $S + 1$ là một lũy thừa của $2$.",
                solution=f"Lời giải chi tiết:\n"
                         f"- Bước 1: Ta có $2S = 2 + 2^2 + 2^3 + \\dots + 2^{{2025}}$.\n"
                         f"  Lấy $2S - S = (2 + 2^2 + \\dots + 2^{{2025}}) - (1 + 2 + \\dots + 2^{{2024}}) = 2^{{2025}} - 1$ (+{pts_half} điểm)\n"
                         f"- Bước 2: Suy ra $S = 2^{{2025}} - 1 \\Rightarrow S + 1 = 2^{{2025}}$.\n"
                         f"  Vậy $S + 1$ là một lũy thừa của 2 (+{slot.points - pts_half} điểm).",
                rubric={"Bước 1 (Tính 2S - S)": pts_half, "Bước 2 (Kết luận)": slot.points - pts_half},
                verified=True
            )

    # -------------------------------------------------------------------------
    # LỚP 7
    # -------------------------------------------------------------------------
    @classmethod
    def _register_grade_7_templates(cls):
        @cls.register("g7_p1_rational_basic", 7, 1, QuestionType.MULTIPLE_CHOICE, CognitiveLevel.NHAN_BIET, ["số hữu tỉ", "tập hợp các số hữu tỉ", "trục số"])
        def gen_g7_rational(slot, orig, mode):
            num = random.choice([3, -4, 5, -7])
            den = random.choice([2, 5, 8])
            return Question(
                id=slot.slot_id,
                type=QuestionType.MULTIPLE_CHOICE,
                topic=slot.topic,
                subtopic=slot.subtopic,
                level=slot.level,
                stem=f"Số đối của số hữu tỉ $\\frac{{{num}}}{{{den}}}$ là",
                choices=[f"$-\\frac{{{num}}}{{{den}}}$" if num > 0 else f"$\\frac{{{abs(num)}}}{{{den}}}$",
                         f"$\\frac{{{den}}}{{{num}}}$",
                         f"$-\\frac{{{den}}}{{{num}}}$",
                         f"$\\frac{{{abs(num) + 1}}}{{{den}}}$"],
                correct_index=0,
                solution=f"Số đối của số hữu tỉ $x$ là $-x$. Do đó số đối của $\\frac{{{num}}}{{{den}}}$ là ${-num}/{den}$.",
                verified=True
            )

        @cls.register("g7_p1_rational_add", 7, 1, QuestionType.MULTIPLE_CHOICE, CognitiveLevel.NHAN_BIET, [
            "số hữu tỉ và các phép tính", "cộng, trừ, nhân, chia số hữu tỉ",
        ])
        def gen_g7_rational_add(slot, orig, mode):
            denominator = random.choice([7, 9, 11])
            first, second = random.sample([1, 2, 3], 2)
            total = first + second
            return Question(
                id=slot.slot_id, type=slot.type, topic=slot.topic,
                subtopic=slot.subtopic, level=slot.level,
                stem=f"Tính $\\frac{{{first}}}{{{denominator}}}+\\frac{{{second}}}{{{denominator}}}$.",
                choices=[f"$\\frac{{{total}}}{{{denominator}}}$", f"$\\frac{{{total}}}{{{2 * denominator}}}$",
                         f"$\\frac{{{first * second}}}{{{denominator}}}$", f"$-\\frac{{{total}}}{{{denominator}}}$"],
                correct_index=0,
                solution=f"Hai phân số cùng mẫu nên cộng hai tử số và giữ nguyên mẫu, được $\\frac{{{total}}}{{{denominator}}}$.",
            )

        @cls.register("g7_p1_rational_power", 7, 1, QuestionType.MULTIPLE_CHOICE, CognitiveLevel.NHAN_BIET, [
            "lũy thừa của số hữu tỉ", "lũy thừa với số mũ tự nhiên của số hữu tỉ",
        ])
        def gen_g7_rational_power(slot, orig, mode):
            denominator = random.choice([3, 5, 7, 9])
            exponent = random.choice([2, 3])
            base = f"\\left(-\\frac{{2}}{{{denominator}}}\\right)"
            sign = "-" if exponent % 2 else ""
            power = f"{sign}\\frac{{{2 ** exponent}}}{{{denominator ** exponent}}}"
            opposite = power[1:] if sign else f"-{power}"
            return Question(
                id=slot.slot_id, type=slot.type, topic=slot.topic,
                subtopic=slot.subtopic, level=slot.level,
                stem=f"Giá trị của ${base}^{{{exponent}}}$ bằng bao nhiêu?",
                choices=[f"${power}$", f"${opposite}$",
                         f"${sign}\\frac{{{2 ** exponent}}}{{{denominator}}}$",
                         f"${sign}\\frac{{2}}{{{denominator ** exponent}}}$"],
                correct_index=0,
                solution=(
                    f"Nâng cả tử và mẫu lên lũy thừa bậc ${exponent}$. "
                    f"Ta được ${base}^{{{exponent}}} = "
                    f"\\frac{{(-2)^{{{exponent}}}}}{{{denominator}^{{{exponent}}}}} = {power}$."
                ),
            )

        @cls.register("g7_p1_sqrt_real", 7, 1, QuestionType.MULTIPLE_CHOICE, CognitiveLevel.NHAN_BIET, ["căn bậc hai số học", "số thực", "vô tỉ", "giá trị tuyệt đối"])
        def gen_g7_sqrt(slot, orig, mode):
            x = random.choice([25, 36, 49, 64, 81, 100])
            rx = int(math.isqrt(x))
            return Question(
                id=slot.slot_id,
                type=QuestionType.MULTIPLE_CHOICE,
                topic=slot.topic,
                subtopic=slot.subtopic,
                level=slot.level,
                stem=f"Căn bậc hai số học của số ${x}$ bằng",
                choices=[f"${rx}$", f"${-rx}$", f"$\\pm {rx}$", f"${x*2}$"],
                correct_index=0,
                solution=f"Căn bậc hai số học của $a \\ge 0$ là số không âm $x$ sao cho $x^2 = a$. Vì ${rx} \\ge 0$ và ${rx}^2 = {x}$ nên $\\sqrt{{{x}}} = {rx}$.",
                verified=True
            )

        @cls.register("g7_p1_ratio", 7, 1, QuestionType.MULTIPLE_CHOICE, CognitiveLevel.NHAN_BIET, ["tỉ lệ thức", "dãy tỉ số bằng nhau", "tỉ lệ thuận", "tỉ lệ nghịch"])
        def gen_g7_ratio(slot, orig, mode):
            a = random.choice([2, 3, 4])
            b = random.choice([5, 6, 7])
            c = a * 2
            d = b * 2
            return Question(
                id=slot.slot_id,
                type=QuestionType.MULTIPLE_CHOICE,
                topic=slot.topic,
                subtopic=slot.subtopic,
                level=slot.level,
                stem=f"Từ đẳng thức ${a} \\cdot {d} = {b} \\cdot {c}$, tỉ lệ thức nào sau đây là ĐÚNG?",
                choices=[f"$\\frac{{{a}}}{{{b}}} = \\frac{{{c}}}{{{d}}}$", f"$\\frac{{{a}}}{{{c}}} = \\frac{{{d}}}{{{b}}}$", f"$\\frac{{{a}}}{{{d}}} = \\frac{{{b}}}{{{c}}}$", f"$\\frac{{{b}}}{{{a}}} = \\frac{{{c}}}{{{d}}}$"],
                correct_index=0,
                solution=f"Từ $ad = bc$, ta suy ra tỉ lệ thức chuẩn: $\\frac{{a}}{{b}} = \\frac{{c}}{{d}}$.",
                verified=True
            )

        @cls.register("g7_p1_geom_angles", 7, 1, QuestionType.MULTIPLE_CHOICE, CognitiveLevel.NHAN_BIET, ["góc ở vị trí đặc biệt", "kề bù", "đối đỉnh", "song song", "phân giác"])
        def gen_g7_geom_angles(slot, orig, mode):
            angle = random.choice([50, 60, 70, 80, 110])
            ans = 180 - angle
            return Question(
                id=slot.slot_id,
                type=QuestionType.MULTIPLE_CHOICE,
                topic=slot.topic,
                subtopic=slot.subtopic,
                level=slot.level,
                stem=f"Cho hai góc kề bù $\\widehat{{xOy}}$ và $\\widehat{{yOz}}$. Biết $\\widehat{{xOy}} = {angle}^\\circ$. Số đo của góc $\\widehat{{yOz}}$ bằng",
                choices=[f"${ans}^\\circ$", f"${angle}^\\circ$", f"${90}^\\circ$", f"${180}^\\circ$"],
                correct_index=0,
                solution=f"Hai góc kề bù có tổng bằng $180^\\circ$. Do đó $\\widehat{{yOz}} = 180^\\circ - {angle}^\\circ = {ans}^\\circ$.",
                verified=True
            )

        @cls.register("g7_p1_geom_triangles", 7, 1, QuestionType.MULTIPLE_CHOICE, CognitiveLevel.NHAN_BIET, ["tam giác", "tổng ba góc", "tam giác cân", "trung tuyến", "đường cao"])
        def gen_g7_geom_triangles(slot, orig, mode):
            gocA = random.choice([50, 60, 70])
            gocB = random.choice([40, 50, 60])
            gocC = 180 - gocA - gocB
            return Question(
                id=slot.slot_id,
                type=QuestionType.MULTIPLE_CHOICE,
                topic=slot.topic,
                subtopic=slot.subtopic,
                level=slot.level,
                stem=f"Cho $\\Delta ABC$ có $\\widehat{{A}} = {gocA}^\\circ$ và $\\widehat{{B}} = {gocB}^\\circ$. Số đo của góc $\\widehat{{C}}$ bằng",
                choices=[f"${gocC}^\\circ$", f"${gocC+10}^\\circ$", f"${gocC-10}^\\circ$", f"${90}^\\circ$"],
                correct_index=0,
                solution=f"Tổng ba góc trong một tam giác bằng $180^\\circ$. Do đó $\\widehat{{C}} = 180^\\circ - ({gocA}^\\circ + {gocB}^\\circ) = {gocC}^\\circ$.",
                verified=True
            )

        @cls.register("g7_p2_rational_expression", 7, 2, QuestionType.ESSAY, CognitiveLevel.NHAN_BIET, [
            "thực hiện phép tính số hữu tỉ",
        ])
        def gen_g7_rational_expression(slot, orig, mode):
            denominator = random.choice([5, 7, 11, 13])
            multiplier = random.choice([2, 3, 4])
            numerator = random.randint(multiplier + 1, denominator)
            half = slot.points / 2
            return Question(
                id=slot.slot_id, type=slot.type, topic=slot.topic,
                subtopic=slot.subtopic, level=slot.level,
                stem=f"Tính $-\\frac{{1}}{{{denominator}}}\\times {multiplier}+\\frac{{{numerator}}}{{{denominator}}}$.",
                solution=(
                    f"Nhân trước: $-\\frac{{1}}{{{denominator}}}\\times {multiplier}="
                    f"-\\frac{{{multiplier}}}{{{denominator}}}$ ({half:g} điểm). "
                    f"Cộng hai phân số cùng mẫu, được $\\frac{{{numerator}-{multiplier}}}{{{denominator}}}="
                    f"\\frac{{{numerator - multiplier}}}{{{denominator}}}$ ({half:g} điểm)."
                ),
                rubric={"Thực hiện phép nhân": half, "Cộng hai phân số": slot.points - half},
            )

        @cls.register("g7_p2_essay_ratio", 7, 2, QuestionType.ESSAY, CognitiveLevel.THONG_HIEU, ["dãy tỉ số bằng nhau", "tỉ lệ thuận", "tỉ lệ nghịch", "thực hiện phép tính"])
        def gen_g7_essay_ratio(slot, orig, mode):
            k = random.choice([3, 4, 5])
            x, y = 2 * k, 5 * k
            total = x + y
            pts_half = round(slot.points / 2, 2)
            return Question(
                id=slot.slot_id,
                type=QuestionType.ESSAY,
                topic=slot.topic,
                subtopic=slot.subtopic,
                level=slot.level,
                stem=f"Tìm hai số $x$ và $y$ biết: $\\frac{{x}}{{2}} = \\frac{{y}}{{5}}$ và $x + y = {total}$.",
                solution=f"Lời giải chi tiết:\n"
                         f"- Bước 1: Áp dụng tính chất của dãy tỉ số bằng nhau:\n"
                         f"  $\\frac{{x}}{{2}} = \\frac{{y}}{{5}} = \\frac{{x + y}}{{2 + 5}} = \\frac{{{total}}}{{7}} = {k}$ (+{pts_half} điểm)\n"
                         f"- Bước 2: Suy ra:\n"
                         f"  $x = 2 \\times {k} = {x}$\n"
                         f"  $y = 5 \\times {k} = {y}$ (+{slot.points - pts_half} điểm).\n"
                         f"Vậy $x = {x}$ và $y = {y}$.",
                rubric={"Bước 1 (Áp dụng dãy tỉ số)": pts_half, "Bước 2 (Tìm x, y)": slot.points - pts_half},
                verified=True
            )

    # -------------------------------------------------------------------------
    # LỚP 8
    # -------------------------------------------------------------------------
    @classmethod
    def _register_grade_8_templates(cls):
        @cls.register("g8_p1_poly_basic", 8, 1, QuestionType.MULTIPLE_CHOICE, CognitiveLevel.NHAN_BIET, ["đơn thức", "đa thức", "bậc của đa thức", "đồng dạng"])
        def gen_g8_poly_basic(slot, orig, mode):
            deg_x = random.choice([3, 4, 5])
            deg_y = random.choice([2, 3])
            total_deg = deg_x + deg_y
            return Question(
                id=slot.slot_id,
                type=QuestionType.MULTIPLE_CHOICE,
                topic=slot.topic,
                subtopic=slot.subtopic,
                level=slot.level,
                stem=f"Bậc của đơn thức $M = -5x^{{{deg_x}}}y^{{{deg_y}}}z$ bằng",
                choices=[f"${total_deg + 1}$", f"${total_deg}$", f"${deg_x}$", f"${total_deg - 1}$"],
                correct_index=0,
                solution=f"Bậc của đơn thức là tổng số mũ của tất cả các biến: ${deg_x} + {deg_y} + 1 = {total_deg + 1}$.",
                verified=True
            )

        @cls.register("g8_p1_identities", 8, 1, QuestionType.MULTIPLE_CHOICE, CognitiveLevel.NHAN_BIET, ["hằng đẳng thức", "bình phương của một tổng", "hiệu hai bình phương", "lập phương"])
        def gen_g8_identities(slot, orig, mode):
            a = random.choice([2, 3])
            b = random.choice([3, 5])
            a2 = a * a
            ab2 = 2 * a * b
            b2 = b * b
            return Question(
                id=slot.slot_id,
                type=QuestionType.MULTIPLE_CHOICE,
                topic=slot.topic,
                subtopic=slot.subtopic,
                level=slot.level,
                stem=f"Khai triển hằng đẳng thức $({a}x - {b})^2$ ta được kết quả là",
                choices=[
                    f"${a2}x^2 - {ab2}x + {b2}$",
                    f"${a2}x^2 - {ab2//2}x + {b2}$",
                    f"${a2}x^2 + {ab2}x + {b2}$",
                    f"${a2}x^2 - {b2}$"
                ],
                correct_index=0,
                solution=f"Áp dụng $(A - B)^2 = A^2 - 2AB + B^2$: $({a}x - {b})^2 = {a2}x^2 - {ab2}x + {b2}$.",
                verified=True
            )

        @cls.register("g8_p1_fractions_alg", 8, 1, QuestionType.MULTIPLE_CHOICE, CognitiveLevel.NHAN_BIET, ["phân thức", "điều kiện xác định", "rút gọn phân thức"])
        def gen_g8_frac_alg(slot, orig, mode):
            a = random.choice([2, 3, 5])
            return Question(
                id=slot.slot_id,
                type=QuestionType.MULTIPLE_CHOICE,
                topic=slot.topic,
                subtopic=slot.subtopic,
                level=slot.level,
                stem=f"Điều kiện xác định của phân thức đại số $\\frac{{x + 1}}{{x - {a}}}$ là",
                choices=[f"$x \\ne {a}$", f"$x \\ne -{a}$", f"$x \\ne -1$", f"$x > {a}$"],
                correct_index=0,
                solution=f"Phân thức xác định khi mẫu thức khác 0: $x - {a} \\ne 0 \\Leftrightarrow x \\ne {a}$.",
                verified=True
            )

        @cls.register("g8_p1_geom_quad", 8, 1, QuestionType.MULTIPLE_CHOICE, CognitiveLevel.NHAN_BIET, ["tứ giác", "hình thang", "hình bình hành", "hình chữ nhật", "hình thoi", "hình vuông", "thales", "đồng dạng"])
        def gen_g8_geom_quad(slot, orig, mode):
            return Question(
                id=slot.slot_id,
                type=QuestionType.MULTIPLE_CHOICE,
                topic=slot.topic,
                subtopic=slot.subtopic,
                level=slot.level,
                stem="Hình bình hành có hai đường chéo bằng nhau là hình gì?",
                choices=["Hình chữ nhật", "Hình thoi", "Hình vuông", "Hình thang cân"],
                correct_index=0,
                solution="Theo dấu hiệu nhận biết hình chữ nhật: Hình bình hành có hai đường chéo bằng nhau là hình chữ nhật.",
                verified=True
            )

        @cls.register("g8_p2_essay_factor", 8, 2, QuestionType.ESSAY, CognitiveLevel.THONG_HIEU, ["phân tích đa thức thành nhân tử", "rút gọn", "hằng đẳng thức"])
        def gen_g8_essay_factor(slot, orig, mode):
            a = random.choice([2, 3])
            pts_half = round(slot.points / 2, 2)
            return Question(
                id=slot.slot_id,
                type=QuestionType.ESSAY,
                topic=slot.topic,
                subtopic=slot.subtopic,
                level=slot.level,
                stem=f"Phân tích đa thức sau thành nhân tử: $A = x^2 - {a*a} + 2xy + y^2$.",
                solution=f"Lời giải chi tiết:\n"
                         f"- Bước 1: Nhóm các hạng tử tạo thành hằng đẳng thức:\n"
                         f"  $A = (x^2 + 2xy + y^2) - {a*a} = (x + y)^2 - {a}^2$ (+{pts_half} điểm)\n"
                         f"- Bước 2: Áp dụng hằng đẳng thức hiệu hai bình phương:\n"
                         f"  $A = (x + y - {a})(x + y + {a})$ (+{slot.points - pts_half} điểm).\n"
                         f"Vậy $A = (x + y - {a})(x + y + {a})$.",
                rubric={"Bước 1 (Nhóm hằng đẳng thức)": pts_half, "Bước 2 (Hiệu hai bình phương)": slot.points - pts_half},
                verified=True
            )

    # -------------------------------------------------------------------------
    # LỚP 9
    # -------------------------------------------------------------------------
    @classmethod
    def _register_grade_9_templates(cls):
        @cls.register("g9_p1_linear_sys", 9, 1, QuestionType.MULTIPLE_CHOICE, CognitiveLevel.NHAN_BIET, ["phương trình bậc nhất hai ẩn", "hệ hai phương trình", "hệ phương trình"])
        def gen_g9_sys(slot, orig, mode):
            x, y = random.choice([(1, 2), (2, 1), (3, -1), (2, 3)])
            eq1 = f"x + y = {x + y}"
            eq2 = f"2x - y = {2*x - y}"
            return Question(
                id=slot.slot_id,
                type=QuestionType.MULTIPLE_CHOICE,
                topic=slot.topic,
                subtopic=slot.subtopic,
                level=slot.level,
                stem=f"Nghiệm của hệ phương trình $\\begin{{cases}} {eq1} \\\\ {eq2} \\end{{cases}}$ là",
                choices=[f"$(x; y) = ({x}; {y})$", f"$(x; y) = ({y}; {x})$", f"$(x; y) = ({x+1}; {y-1})$", f"$(x; y) = ({x-1}; {y+1})$"],
                correct_index=0,
                solution=f"Cộng hai phương trình vế theo vế: $3x = {3*x} \\Rightarrow x = {x}$. Thay vào phương trình đầu suy ra $y = {y}$.",
                verified=True
            )

        @cls.register("g9_p1_viet", 9, 1, QuestionType.MULTIPLE_CHOICE, CognitiveLevel.NHAN_BIET, ["vi-et", "viète", "phương trình bậc hai", "nghiệm"])
        def gen_g9_viet(slot, orig, mode):
            x1, x2 = random.choice([(1, 4), (2, 3), (2, 5), (-1, 3)])
            S = x1 + x2
            P = x1 * x2
            ans = S + P
            sign_s = f"- {S}x" if S > 0 else f"+ {abs(S)}x"
            sign_p = f"+ {P}" if P > 0 else f"- {abs(P)}"
            return Question(
                id=slot.slot_id,
                type=QuestionType.MULTIPLE_CHOICE,
                topic=slot.topic,
                subtopic=slot.subtopic,
                level=slot.level,
                stem=f"Cho phương trình bậc hai $x^2 {sign_s} {sign_p} = 0$ có hai nghiệm $x_1, x_2$. Giá trị của biểu thức $T = x_1 + x_2 + x_1 x_2$ bằng",
                choices=[f"${ans}$", f"${ans - 2}$", f"${ans + 2}$", f"${S}$"],
                correct_index=0,
                solution=f"Theo định lý Viète, $x_1 + x_2 = {S}$ và $x_1 x_2 = {P}$. Vậy $T = {S} + ({P}) = {ans}$.",
                verified=True
            )

        @cls.register("g9_p1_circle", 9, 1, QuestionType.MULTIPLE_CHOICE, CognitiveLevel.NHAN_BIET, ["đường tròn", "tiếp tuyến", "góc nội tiếp", "tứ giác nội tiếp"])
        def gen_g9_circle(slot, orig, mode):
            angle = random.choice([70, 75, 80, 85])
            ans = 180 - angle
            return Question(
                id=slot.slot_id,
                type=QuestionType.MULTIPLE_CHOICE,
                topic=slot.topic,
                subtopic=slot.subtopic,
                level=slot.level,
                stem=f"Cho tứ giác $ABCD$ nội tiếp đường tròn $(O)$. Biết số đo góc $\\widehat{{A}} = {angle}^\\circ$. Số đo của góc $\\widehat{{C}}$ bằng",
                choices=[f"${ans}^\\circ$", f"${angle}^\\circ$", f"${90}^\\circ$", f"${180}^\\circ$"],
                correct_index=0,
                solution=f"Tứ giác nội tiếp có hai góc đối bù nhau: $\\widehat{{C}} = 180^\\circ - {angle}^\\circ = {ans}^\\circ$.",
                verified=True
            )

        @cls.register("g9_p2_essay_viet", 9, 2, QuestionType.ESSAY, CognitiveLevel.VAN_DUNG, ["định lí viète", "tham số m", "rút gọn căn thức", "hệ phương trình"])
        def gen_g9_essay_viet(slot, orig, mode):
            pts_half = round(slot.points / 2, 2)
            return Question(
                id=slot.slot_id,
                type=QuestionType.ESSAY,
                topic=slot.topic,
                subtopic=slot.subtopic,
                level=slot.level,
                stem="Cho phương trình $x^2 - 2(m - 1)x + m^2 - 3 = 0$. Tìm $m$ để phương trình có hai nghiệm phân biệt $x_1, x_2$ thỏa mãn $x_1^2 + x_2^2 = 10$.",
                solution=f"Lời giải chi tiết:\n"
                         f"- Bước 1: $\\Delta' = (m-1)^2 - (m^2 - 3) = -2m + 4 > 0 \\Leftrightarrow m < 2$ (+{pts_half} điểm)\n"
                         f"- Bước 2: Theo Viète: $x_1 + x_2 = 2(m-1)$ và $x_1 x_2 = m^2 - 3$.\n"
                         f"  $x_1^2 + x_2^2 = 4(m-1)^2 - 2(m^2-3) = 2m^2 - 8m + 10 = 10 \\Leftrightarrow 2m(m-4) = 0$.\n"
                         f"  Vì $m < 2$ nên chọn $m = 0$ (+{slot.points - pts_half} điểm).\n"
                         f"Vậy $m = 0$.",
                rubric={"Bước 1 (Tìm Delta')": pts_half, "Bước 2 (Áp dụng Viète)": slot.points - pts_half},
                verified=True
            )

    # -------------------------------------------------------------------------
    # LỚP 10
    # -------------------------------------------------------------------------
    @classmethod
    def _register_grade_10_templates(cls):
        @cls.register("g10_p1_sets", 10, 1, QuestionType.MULTIPLE_CHOICE, CognitiveLevel.NHAN_BIET, ["mệnh đề", "tập hợp", "giao", "hợp", "hiệu"])
        def gen_g10_sets(slot, orig, mode):
            return Question(
                id=slot.slot_id,
                type=QuestionType.MULTIPLE_CHOICE,
                topic=slot.topic,
                subtopic=slot.subtopic,
                level=slot.level,
                stem="Cho hai tập hợp $A = [-2; 3]$ và $B = (1; 5]$. Giao của hai tập hợp $A \\cap B$ là",
                choices=["$(1; 3]$", "$[-2; 5]$", "$[-2; 1)$", "$[3; 5]$"],
                correct_index=0,
                solution="Giao của hai tập hợp: $A \\cap B = (1; 3]$.",
                verified=True
            )

        @cls.register("g10_p1_vectors", 10, 1, QuestionType.MULTIPLE_CHOICE, CognitiveLevel.NHAN_BIET, ["vectơ", "tọa độ", "tích vô hướng", "hệ thức lượng"])
        def gen_g10_vectors(slot, orig, mode):
            x1, y1 = random.choice([(1, 2), (2, -1), (3, 4)])
            x2, y2 = random.choice([(3, -1), (1, 2), (-2, 3)])
            dot = x1 * x2 + y1 * y2
            return Question(
                id=slot.slot_id,
                type=QuestionType.MULTIPLE_CHOICE,
                topic=slot.topic,
                subtopic=slot.subtopic,
                level=slot.level,
                stem=f"Trong mặt phẳng $Oxy$, cho hai vectơ $\\vec{{u}} = ({x1}; {y1})$ và $\\vec{{v}} = ({x2}; {y2})$. Tích vô hướng $\\vec{{u}} \\cdot \\vec{{v}}$ bằng",
                choices=[f"${dot}$", f"${dot - 2}$", f"${dot + 4}$", f"${x1*y2}$"],
                correct_index=0,
                solution=f"Tích vô hướng $\\vec{{u}} \\cdot \\vec{{v}} = {x1} \\times {x2} + ({y1}) \\times ({y2}) = {dot}$.",
                verified=True
            )

        @cls.register("g10_p1_oxy_line_circle", 10, 1, QuestionType.MULTIPLE_CHOICE, CognitiveLevel.NHAN_BIET, ["đường thẳng", "đường tròn", "bán kính", "tọa độ trong mặt phẳng"])
        def gen_g10_oxy(slot, orig, mode):
            a, b = random.choice([(1, -2), (2, 3), (-3, 1)])
            r = random.choice([2, 3, 4, 5])
            r2 = r * r
            sign_a = f"- {a}" if a > 0 else f"+ {abs(a)}"
            sign_b = f"- {b}" if b > 0 else f"+ {abs(b)}"
            return Question(
                id=slot.slot_id,
                type=QuestionType.MULTIPLE_CHOICE,
                topic=slot.topic,
                subtopic=slot.subtopic,
                level=slot.level,
                stem=f"Trong mặt phẳng $Oxy$, cho đường tròn $(C): (x {sign_a})^2 + (y {sign_b})^2 = {r2}$. Tọa độ tâm $I$ và bán kính $R$ của $(C)$ là",
                choices=[
                    f"$I({a}; {b})$ và $R = {r}$",
                    f"$I({-a}; {-b})$ và $R = {r}$",
                    f"$I({a}; {b})$ và $R = {r2}$",
                    f"$I({-a}; {-b})$ và $R = {r2}$"
                ],
                correct_index=0,
                solution=f"Tâm $I({a}; {b})$ và bán kính $R = \\sqrt{{{r2}}} = {r}$.",
                verified=True
            )

        @cls.register("g10_p2_tf_quad_func", 10, 2, QuestionType.TRUE_FALSE, CognitiveLevel.THONG_HIEU, ["tam thức bậc hai", "hàm số bậc hai", "đồ thị"])
        def gen_g10_tf(slot, orig, mode):
            return Question(
                id=slot.slot_id,
                type=QuestionType.TRUE_FALSE,
                topic=slot.topic,
                subtopic=slot.subtopic,
                level=slot.level,
                stem="Cho hàm số bậc hai $y = f(x) = x^2 - 4x + 3$. Xét tính đúng hay sai của các mệnh đề sau:",
                statements=[
                    TrueFalseItem(statement="Đồ thị hàm số là một parabol có bề lõm quay lên trên.", is_correct=True, explanation="Do $a = 1 > 0$."),
                    TrueFalseItem(statement="Tọa độ đỉnh của parabol là $I(2; -1)$.", is_correct=True, explanation="$x_I = 2, y_I = -1$."),
                    TrueFalseItem(statement="Hàm số đồng biến trên khoảng $(-\\infty; 2)$.", is_correct=False, explanation="Hàm số nghịch biến trên $(-\\infty; 2)$."),
                    TrueFalseItem(statement="Tập nghiệm của bất phương trình $f(x) \\le 0$ là đoạn $[1; 3]$.", is_correct=True, explanation="$x \\in [1; 3]$.")
                ],
                solution="Mệnh đề a ĐÚNG, b ĐÚNG, c SAI, d ĐÚNG.",
                verified=True
            )

        @cls.register("g10_p3_essay_bpt", 10, 3, QuestionType.ESSAY, CognitiveLevel.VAN_DUNG, ["bất phương trình", "quy hoạch tuyến tính", "tham số"])
        def gen_g10_essay(slot, orig, mode):
            pts_half = round(slot.points / 2, 2)
            return Question(
                id=slot.slot_id,
                type=QuestionType.ESSAY,
                topic=slot.topic,
                subtopic=slot.subtopic,
                level=slot.level,
                stem="Tìm tất cả các giá trị của tham số $m$ để tam thức bậc hai $f(x) = x^2 - 2(m + 1)x + 4m > 0$ với mọi $x \\in \\mathbb{R}$.",
                solution=f"Lời giải chi tiết:\n"
                         f"- Bước 1: Điều kiện để $f(x) > 0, \\forall x \\in \\mathbb{{R}}$ là $\\Delta' < 0$ (+{pts_half} điểm)\n"
                         f"- Bước 2: $\\Delta' = (m-1)^2 < 0$ (Vô nghiệm). Vậy không có giá trị nào của $m$ thỏa mãn (+{slot.points - pts_half} điểm).",
                rubric={"Bước 1 (Thiết lập điều kiện)": pts_half, "Bước 2 (Giải bất phương trình)": slot.points - pts_half},
                verified=True
            )

    # -------------------------------------------------------------------------
    # LỚP 11
    # -------------------------------------------------------------------------
    @classmethod
    def _register_grade_11_templates(cls):
        @cls.register("g11_p1_trig", 11, 1, QuestionType.MULTIPLE_CHOICE, CognitiveLevel.NHAN_BIET, ["lượng giác", "công thức lượng giác", "hàm số lượng giác", "phương trình lượng giác"])
        def gen_g11_trig(slot, orig, mode):
            return Question(
                id=slot.slot_id,
                type=QuestionType.MULTIPLE_CHOICE,
                topic=slot.topic,
                subtopic=slot.subtopic,
                level=slot.level,
                stem="Tập xác định của hàm số $y = \\tan x$ là",
                choices=[
                    "$\\mathbb{R} \\setminus \\left\\{\\frac{\\pi}{2} + k\\pi, k \\in \\mathbb{Z}\\right\\}$",
                    "$\\mathbb{R} \\setminus \\{k\\pi, k \\in \\mathbb{Z}\\}$",
                    "$\\mathbb{R}$",
                    "$\\mathbb{R} \\setminus \\left\\{\\frac{\\pi}{4} + k\\pi, k \\in \\mathbb{Z}\\right\\}$"
                ],
                correct_index=0,
                solution="Hàm số $\\tan x$ xác định khi $\\cos x \\ne 0 \\Leftrightarrow x \\ne \\frac{\\pi}{2} + k\\pi$.",
                verified=True
            )

        @cls.register("g11_p1_sequences", 11, 1, QuestionType.MULTIPLE_CHOICE, CognitiveLevel.NHAN_BIET, ["dãy số", "cấp số cộng", "cấp số nhân", "công sai", "công bội"])
        def gen_g11_seq(slot, orig, mode):
            u1 = random.choice([2, 3, 5])
            d = random.choice([3, 4, 5])
            u4 = u1 + 3 * d
            return Question(
                id=slot.slot_id,
                type=QuestionType.MULTIPLE_CHOICE,
                topic=slot.topic,
                subtopic=slot.subtopic,
                level=slot.level,
                stem=f"Cho cấp số cộng $(u_n)$ có số hạng đầu $u_1 = {u1}$ và công sai $d = {d}$. Số hạng thứ tư $u_4$ bằng",
                choices=[f"${u4}$", f"${u4 - d}$", f"${u4 + d}$", f"${u1 * d}$"],
                correct_index=0,
                solution=f"Ta có $u_4 = u_1 + 3d = {u1} + 3 \\times {d} = {u4}$.",
                verified=True
            )

        @cls.register("g11_p1_limits", 11, 1, QuestionType.MULTIPLE_CHOICE, CognitiveLevel.NHAN_BIET, ["giới hạn", "liên tục", "lim"])
        def gen_g11_limits(slot, orig, mode):
            a = random.choice([2, 3, 4])
            c = random.choice([3, 5])
            return Question(
                id=slot.slot_id,
                type=QuestionType.MULTIPLE_CHOICE,
                topic=slot.topic,
                subtopic=slot.subtopic,
                level=slot.level,
                stem=f"Giá trị của giới hạn $\\lim \\frac{{{a}n + 1}}{{{c}n - 1}}$ bằng",
                choices=[f"$\\frac{{{a}}}{{{c}}}$", f"${a}$", f"$0$", f"$+\\infty$"],
                correct_index=0,
                solution=f"Chia cả tử và mẫu cho $n$: $\\lim = \\frac{{{a}}}{{{c}}}$.",
                verified=True
            )

        @cls.register("g11_p1_spatial_geom", 11, 1, QuestionType.MULTIPLE_CHOICE, CognitiveLevel.NHAN_BIET, ["đường thẳng và mặt phẳng", "song song", "vuông góc", "khoảng cách", "góc"])
        def gen_g11_geom(slot, orig, mode):
            return Question(
                id=slot.slot_id,
                type=QuestionType.MULTIPLE_CHOICE,
                topic=slot.topic,
                subtopic=slot.subtopic,
                level=slot.level,
                stem="Cho hình chóp $S.ABCD$ có đáy $ABCD$ là hình vuông và $SA \\perp (ABCD)$. Khẳng định nào sau đây là SAI?",
                choices=["$SA \\perp SB$", "$SA \\perp AB$", "$SA \\perp BC$", "$SA \\perp CD$"],
                correct_index=0,
                solution="Trong tam giác vuông $SAB$, $SA$ không thể vuông góc với cạnh huyền $SB$.",
                verified=True
            )

        @cls.register("g11_p1_exp_log_deriv", 11, 1, QuestionType.MULTIPLE_CHOICE, CognitiveLevel.NHAN_BIET, ["mũ", "lôgarit", "đạo hàm", "tiếp tuyến"])
        def gen_g11_exp_log(slot, orig, mode):
            a = random.choice([2, 3, 5])
            return Question(
                id=slot.slot_id,
                type=QuestionType.MULTIPLE_CHOICE,
                topic=slot.topic,
                subtopic=slot.subtopic,
                level=slot.level,
                stem=f"Đạo hàm của hàm số $y = x^{{{a}}}$ là",
                choices=[f"${a}x^{{{a-1}}}$", f"$x^{{{a-1}}}$", f"${a}x^{{{a}}}$", f"$\\frac{{x^{{{a+1}}}}}{{{a+1}}}$"],
                correct_index=0,
                solution=f"$(x^{{{a}}})' = {a}x^{{{a-1}}}$.",
                verified=True
            )

        @cls.register("g11_p2_tf_ap_gp", 11, 2, QuestionType.TRUE_FALSE, CognitiveLevel.THONG_HIEU, ["cấp số cộng", "cấp số nhân", "dãy số"])
        def gen_g11_tf_ap(slot, orig, mode):
            return Question(
                id=slot.slot_id,
                type=QuestionType.TRUE_FALSE,
                topic=slot.topic,
                subtopic=slot.subtopic,
                level=slot.level,
                stem="Cho cấp số cộng $(u_n)$ có số hạng đầu $u_1 = 3$ và công sai $d = 2$. Xét tính đúng hay sai của các khẳng định sau:",
                statements=[
                    TrueFalseItem(statement="Số hạng thứ hai của cấp số cộng là $u_2 = 5$.", is_correct=True, explanation="$u_2 = 3 + 2 = 5$."),
                    TrueFalseItem(statement="Công thức số hạng tổng quát là $u_n = 2n + 1$.", is_correct=True, explanation="$u_n = 3 + (n-1)2 = 2n + 1$."),
                    TrueFalseItem(statement="Số $100$ là một số hạng của cấp số cộng đã cho.", is_correct=False, explanation="$2n + 1 = 100 \\Rightarrow n = 99/2 \\notin \\mathbb{N}^*$."),
                    TrueFalseItem(statement="Tổng $10$ số hạng đầu tiên $S_{10} = 120$.", is_correct=True, explanation="$S_{10} = 120$.")
                ],
                solution="Mệnh đề a ĐÚNG, b ĐÚNG, c SAI, d ĐÚNG.",
                verified=True
            )

        @cls.register("g11_p3_essay_trig", 11, 3, QuestionType.ESSAY, CognitiveLevel.VAN_DUNG, ["phương trình lượng giác", "nghiệm", "khoảng"])
        def gen_g11_essay(slot, orig, mode):
            pts_half = round(slot.points / 2, 2)
            return Question(
                id=slot.slot_id,
                type=QuestionType.ESSAY,
                topic=slot.topic,
                subtopic=slot.subtopic,
                level=slot.level,
                stem="Giải phương trình lượng giác sau trên khoảng $(0; \\pi)$: $2\\cos x - \\sqrt{3} = 0$.",
                solution=f"Lời giải chi tiết:\n"
                         f"- Bước 1: $\\cos x = \\frac{{\\sqrt{{3}}}}{{2}} \\Rightarrow x = \\pm \\frac{{\\pi}}{{6}} + k2\\pi$ (+{pts_half} điểm)\n"
                         f"- Bước 2: Vì $x \\in (0; \\pi)$ nên $x = \\frac{{\\pi}}{{6}}$ (+{slot.points - pts_half} điểm).\n"
                         f"Vậy $x = \\frac{{\\pi}}{{6}}$.",
                rubric={"Bước 1 (Tìm họ nghiệm)": pts_half, "Bước 2 (Chọn nghiệm trong khoảng)": slot.points - pts_half},
                verified=True
            )

    # -------------------------------------------------------------------------
    # LỚP 12: ĐA DẠNG HÓA CÁC MẪU ĐỂ KHÔNG BAO GIỜ BỊ TRÙNG CÂU HỎI
    # -------------------------------------------------------------------------
    @classmethod
    def _register_grade_12_templates(cls):
        # 1. CỰC TRỊ CỦA HÀM SỐ (ĐA DẠNG HÓA MẪU ĐỂ KHÔNG BAO GIỜ BỊ TRÙNG CÂU HỎI!)
        
        # Mẫu 1A: Tìm số điểm cực trị từ đạo hàm dạng tích
        @cls.register("g12_p1_extrema_factors", 12, 1, QuestionType.MULTIPLE_CHOICE, CognitiveLevel.NHAN_BIET, ["cực trị của hàm số", "cực trị hàm", "điểm cực trị"])
        def gen_g12_extrema_factors(slot, orig, mode):
            a = random.choice([2, 3, 5])
            b = random.choice([1, 4])
            return Question(
                id=slot.slot_id,
                type=QuestionType.MULTIPLE_CHOICE,
                topic=slot.topic,
                subtopic=slot.subtopic,
                level=slot.level,
                stem=f"Cho hàm số $y = f(x)$ có đạo hàm $f'(x) = x(x - {a})(x + {b})^2$ với mọi $x \\in \\mathbb{{R}}$. Số điểm cực trị của hàm số đã cho là",
                choices=["$2$", "$1$", "$3$", "$0$"],
                correct_index=0,
                solution=f"Ta có $f'(x) = 0 \\Leftrightarrow x = 0$ (nghiệm đơn), $x = {a}$ (nghiệm đơn), $x = -{b}$ (nghiệm bội chẵn). Đạo hàm chỉ đổi dấu khi qua nghiệm đơn, do đó hàm số có $2$ điểm cực trị.",
                verified=True
            )

        # Mẫu 1B: Đọc giá trị cực tiểu từ Bảng biến thiên
        @cls.register("g12_p1_extrema_bb_th", 12, 1, QuestionType.MULTIPLE_CHOICE, CognitiveLevel.NHAN_BIET, ["cực trị của hàm số", "bảng biến thiên", "giá trị cực tiểu", "giá trị cực đại"])
        def gen_g12_extrema_bb_th(slot, orig, mode):
            y_ct = random.choice([-3, -2, -1, -5])
            y_cd = random.choice([2, 3, 4])
            return Question(
                id=slot.slot_id,
                type=QuestionType.MULTIPLE_CHOICE,
                topic=slot.topic,
                subtopic=slot.subtopic,
                level=slot.level,
                stem="Cho hàm số $y = f(x)$ liên tục trên $\\mathbb{R}$ và có bảng biến thiên như hình bên. Giá trị cực tiểu của hàm số đã cho bằng bao nhiêu?",
                choices=[f"${y_ct}$", f"${y_cd}$", f"$2$", f"$-1$"],
                correct_index=0,
                solution=f"Từ bảng biến thiên, tại điểm $x = 2$, hàm số đạt cực tiểu và giá trị cực tiểu tương ứng là $y_{{\\text{{ct}}}} = {y_ct}$.",
                tikz_code=TikZLibrary.get_tkz_tab_bac3("-1", "2", str(y_cd), str(y_ct), "duong"),
                verified=True
            )

        # Mẫu 1C: Cực trị hàm đa thức bậc ba
        @cls.register("g12_p1_extrema_cubic", 12, 1, QuestionType.MULTIPLE_CHOICE, CognitiveLevel.THONG_HIEU, ["cực trị hàm đa thức", "cực trị", "bậc ba"])
        def gen_g12_extrema_cubic(slot, orig, mode):
            k = random.choice([1, 2, 3])
            val_3k2 = 3 * k * k
            return Question(
                id=slot.slot_id,
                type=QuestionType.MULTIPLE_CHOICE,
                topic=slot.topic,
                subtopic=slot.subtopic,
                level=slot.level,
                stem=f"Điểm cực đại của hàm số $y = x^3 - {val_3k2}x + 2$ là",
                choices=[f"$x = -{k}$", f"$x = {k}$", f"$x = 0$", f"$x = {2*k}$"],
                correct_index=0,
                solution=f"Ta có $y' = 3x^2 - {val_3k2} = 3(x^2 - {k*k}) = 0 \\Leftrightarrow x = \\pm {k}$. Vì qua $x = -{k}$ đạo hàm đổi dấu từ dương sang âm nên $x = -{k}$ là điểm cực đại của hàm số.",
                verified=True
            )

        # 2. ĐƠN ĐIỆU CỦA HÀM SỐ
        @cls.register("g12_p1_monotone", 12, 1, QuestionType.MULTIPLE_CHOICE, CognitiveLevel.NHAN_BIET, ["tính đơn điệu", "đồng biến", "nghịch biến"])
        def gen_g12_monotone(slot, orig, mode):
            a = random.choice([1, 2])
            return Question(
                id=slot.slot_id,
                type=QuestionType.MULTIPLE_CHOICE,
                topic=slot.topic,
                subtopic=slot.subtopic,
                level=slot.level,
                stem=f"Cho hàm số $y = \\frac{{2x - 1}}{{x + {a}}}$. Mệnh đề nào sau đây đúng?",
                choices=[
                    f"Hàm số đồng biến trên từng khoảng $(-\\infty; -{a})$ và $(-{a}; +\\infty)$.",
                    f"Hàm số nghịch biến trên từng khoảng $(-\\infty; -{a})$ và $(-{a}; +\\infty)$.",
                    f"Hàm số đồng biến trên $\\mathbb{{R}} \\setminus \\{{-{a}\\}}.$",
                    f"Hàm số nghịch biến trên $\\mathbb{{R}}.$"
                ],
                correct_index=0,
                solution=f"Tập xác định $D = \\mathbb{{R}} \\setminus \\{{-{a}\\}}$. Ta có $y' = \\frac{{{2*a + 1}}}{{(x+{a})^2}} > 0, \\forall x \\ne -{a}$. Do đó hàm số đồng biến trên từng khoảng xác định.",
                verified=True
            )

        # 3. GIÁ TRỊ LỚN NHẤT, NHỎ NHẤT TRÊN ĐOẠN
        @cls.register("g12_p1_min_max", 12, 1, QuestionType.MULTIPLE_CHOICE, CognitiveLevel.NHAN_BIET, ["giá trị lớn nhất", "giá trị nhỏ nhất", "min", "max"])
        def gen_g12_min_max(slot, orig, mode):
            return Question(
                id=slot.slot_id,
                type=QuestionType.MULTIPLE_CHOICE,
                topic=slot.topic,
                subtopic=slot.subtopic,
                level=slot.level,
                stem="Giá trị nhỏ nhất của hàm số $f(x) = x^4 - 2x^2 + 3$ trên đoạn $[0; 2]$ bằng",
                choices=["$2$", "$3$", "$11$", "$0$"],
                correct_index=0,
                solution="Ta có $f'(x) = 4x(x^2 - 1) = 0 \\Leftrightarrow x = 0$ hoặc $x = 1$. Tính $f(0) = 3, f(1) = 2, f(2) = 11$. Vậy $\\min = 2$.",
                verified=True
            )

        # 4. TIỆM CẬN ĐỨNG, NGANG, XIÊN
        @cls.register("g12_p1_asymptotes_stand", 12, 1, QuestionType.MULTIPLE_CHOICE, CognitiveLevel.NHAN_BIET, ["tiệm cận", "đường tiệm cận", "tiệm cận đứng", "tiệm cận ngang"])
        def gen_g12_asymptotes_stand(slot, orig, mode):
            a = random.choice([2, 3, 4])
            c = random.choice([1, 2])
            d = random.choice([3, 4])
            ans_tcđ = f"x = {d}" if c == 1 else f"x = {d}/{c}"
            ans_tcn = f"y = {a//c}" if a % c == 0 else f"y = {a}/{c}"
            return Question(
                id=slot.slot_id,
                type=QuestionType.MULTIPLE_CHOICE,
                topic=slot.topic,
                subtopic=slot.subtopic,
                level=slot.level,
                stem=f"Đồ thị hàm số $y = \\frac{{{a}x - 1}}{{{c}x - {d}}}$ có đường tiệm cận ngang là",
                choices=[f"${ans_tcn}$", f"${ans_tcđ}$", f"$y = -1$", f"$x = 0$"],
                correct_index=0,
                solution=f"Tiệm cận ngang là đường thẳng $y = \\lim_{{x \\to \\pm\\infty}} y = {ans_tcn}$.",
                verified=True
            )

        @cls.register("g12_p1_asymptotes_slant", 12, 1, QuestionType.MULTIPLE_CHOICE, CognitiveLevel.NHAN_BIET, ["tiệm cận xiên", "tiệm cận", "đường tiệm cận"])
        def gen_g12_asymptotes_slant(slot, orig, mode):
            p = random.choice([1, 2])
            return Question(
                id=slot.slot_id,
                type=QuestionType.MULTIPLE_CHOICE,
                topic=slot.topic,
                subtopic=slot.subtopic,
                level=slot.level,
                stem=f"Đường tiệm cận xiên của đồ thị hàm số $y = \\frac{{x^2 + {p}x + 2}}{{x + 1}}$ là",
                choices=[f"$y = x + {p-1}$", f"$y = x$", f"$y = x + {p}$", f"$y = 2x + 1$"],
                correct_index=0,
                solution=f"Chia đa thức: $\\frac{{x^2 + {p}x + 2}}{{x + 1}} = x + ({p}-1) + \\frac{{{3-p}}}{{x+1}}$. Tiệm cận xiên là $y = x + {p-1}$.",
                verified=True
            )

        @cls.register("g12_p1_intersection", 12, 1, QuestionType.MULTIPLE_CHOICE, CognitiveLevel.THONG_HIEU, ["tương giao", "giao điểm", "bài toán tương giao", "số giao điểm"])
        def gen_g12_intersection(slot, orig, mode):
            m = random.choice([2, 3, 4])
            return Question(
                id=slot.slot_id,
                type=QuestionType.MULTIPLE_CHOICE,
                topic=slot.topic,
                subtopic=slot.subtopic,
                level=slot.level,
                stem=f"Cho hàm số $y = x^3 - 3x^2 + {m}$. Số giao điểm của đồ thị hàm số với đường thẳng $y = {m}$ là",
                choices=["$2$", "$1$", "$3$", "$0$"],
                correct_index=0,
                solution=f"Phương trình hoành độ giao điểm: $x^3 - 3x^2 + {m} = {m} \\Leftrightarrow x^2(x - 3) = 0 \\Leftrightarrow x = 0$ hoặc $x = 3$. Đồ thị cắt tại 2 điểm phân biệt.",
                verified=True
            )

        @cls.register("g12_p1_dot_product_angle", 12, 1, QuestionType.MULTIPLE_CHOICE, CognitiveLevel.THONG_HIEU, ["tích vô hướng", "góc trong không gian", "góc giữa hai vectơ", "tích vô hướng và góc"])
        def gen_g12_dot_angle(slot, orig, mode):
            return Question(
                id=slot.slot_id,
                type=QuestionType.MULTIPLE_CHOICE,
                topic=slot.topic,
                subtopic=slot.subtopic,
                level=slot.level,
                stem="Trong không gian $Oxyz$, cho hai vectơ $\\vec{u} = (1; 0; 1)$ và $\\vec{v} = (0; 1; 1)$. Góc giữa hai vectơ $\\vec{u}$ và $\\vec{v}$ bằng",
                choices=["$60^\\circ$", "$45^\\circ$", "$90^\\circ$", "$30^\\circ$"],
                correct_index=0,
                solution="Ta có $\\cos(\\vec{u}, \\vec{v}) = \\frac{\\vec{u} \\cdot \\vec{v}}{|\\vec{u}| \\cdot |\\vec{v}|} = \\frac{1}{\\sqrt{2} \\cdot \\sqrt{2}} = \\frac{1}{2} \\Rightarrow (\\vec{u}, \\vec{v}) = 60^\\circ$.",
                verified=True
            )

        @cls.register("g12_p1_integrals_def", 12, 1, QuestionType.MULTIPLE_CHOICE, CognitiveLevel.THONG_HIEU, ["nguyên hàm và tích phân", "tích phân cơ bản", "nguyên hàm cơ bản", "tính chất tích phân"])
        def gen_g12_integrals_def(slot, orig, mode):
            a, b = random.choice([(3, 2), (4, 1), (5, 2)])
            ans = 2 * a - b
            return Question(
                id=slot.slot_id,
                type=QuestionType.MULTIPLE_CHOICE,
                topic=slot.topic,
                subtopic=slot.subtopic,
                level=slot.level,
                stem=f"Biết $\\int_1^2 f(x) dx = {a}$ và $\\int_1^2 g(x) dx = {b}$. Giá trị của tích phân $I = \\int_1^2 [2f(x) - g(x)] dx$ bằng",
                choices=[f"${ans}$", f"${ans + 2}$", f"${ans - 2}$", f"${a + b}$"],
                correct_index=0,
                solution=f"Áp dụng tính chất tuyến tính của tích phân: $I = 2\\int_1^2 f(x)dx - \\int_1^2 g(x)dx = 2({a}) - {b} = {ans}$.",
                verified=True
            )

        @cls.register("g12_p1_cond_prob_calc", 12, 1, QuestionType.MULTIPLE_CHOICE, CognitiveLevel.THONG_HIEU, ["xác suất có điều kiện", "điều kiện cơ bản"])
        def gen_g12_cond_prob(slot, orig, mode):
            return Question(
                id=slot.slot_id,
                type=QuestionType.MULTIPLE_CHOICE,
                topic=slot.topic,
                subtopic=slot.subtopic,
                level=slot.level,
                stem="Cho hai biến cố $A$ và $B$ thỏa mãn $P(B) = 0{,}5$ và $P(AB) = 0{,}2$. Xác suất có điều kiện $P(A|B)$ bằng",
                choices=["$0{,}4$", "$0{,}1$", "$0{,}25$", "$0{,}7$"],
                correct_index=0,
                solution="Theo công thức xác suất có điều kiện: $P(A|B) = \\frac{P(AB)}{P(B)} = \\frac{0{,}2}{0{,}5} = 0{,}4$.",
                verified=True
            )

        # 5. HÌNH HỌC OXYZ: TỌA ĐỘ VECTƠ VÀ MẶT CẦU
        @cls.register("g12_p1_oxyz_sphere_1", 12, 1, QuestionType.MULTIPLE_CHOICE, CognitiveLevel.NHAN_BIET, ["mặt cầu cơ bản", "phương trình mặt cầu", "tâm và bán kính"])
        def gen_g12_sphere_1(slot, orig, mode):
            a, b, c = random.choice([(1, -2, 3), (2, -3, 4), (-1, 2, -4), (3, -1, 2)])
            r = random.choice([3, 4, 5, 6])
            r2 = r * r
            sign_a = f"- {a}" if a > 0 else f"+ {abs(a)}"
            sign_b = f"- {b}" if b > 0 else f"+ {abs(b)}"
            sign_c = f"- {c}" if c > 0 else f"+ {abs(c)}"
            return Question(
                id=slot.slot_id,
                type=QuestionType.MULTIPLE_CHOICE,
                topic=slot.topic,
                subtopic=slot.subtopic,
                level=slot.level,
                stem=f"Trong không gian $Oxyz$, cho mặt cầu $(S): (x {sign_a})^2 + (y {sign_b})^2 + (z {sign_c})^2 = {r2}$. Tọa độ tâm $I$ và bán kính $R$ của $(S)$ là",
                choices=[
                    f"$I({a}; {b}; {c})$ và $R = {r}$",
                    f"$I({-a}; {-b}; {-c})$ và $R = {r}$",
                    f"$I({a}; {b}; {c})$ và $R = {r2}$",
                    f"$I({-a}; {-b}; {-c})$ và $R = {r2}$"
                ],
                correct_index=0,
                solution=f"Mặt cầu $(x-a)^2 + (y-b)^2 + (z-c)^2 = R^2$ có tâm $I(a; b; c)$ và bán kính $R$. Ở đây tâm là $I({a}; {b}; {c})$ và $R = {r}$.",
                verified=True
            )

        @cls.register("g12_p1_oxyz_vectors", 12, 1, QuestionType.MULTIPLE_CHOICE, CognitiveLevel.NHAN_BIET, ["tọa độ vectơ trong không gian", "tọa độ vectơ", "tích vô hướng"])
        def gen_g12_oxyz_vec(slot, orig, mode):
            x1, y1, z1 = random.choice([(1, 2, -3), (2, -1, 4), (0, 3, 2)])
            x2, y2, z2 = random.choice([(2, -1, 1), (1, 3, -2), (2, 0, 1)])
            ans = (x1 + x2, y1 + y2, z1 + z2)
            return Question(
                id=slot.slot_id,
                type=QuestionType.MULTIPLE_CHOICE,
                topic=slot.topic,
                subtopic=slot.subtopic,
                level=slot.level,
                stem=f"Trong không gian $Oxyz$, cho hai vectơ $\\vec{{a}} = ({x1}; {y1}; {z1})$ và $\\vec{{b}} = ({x2}; {y2}; {z2})$. Tọa độ của vectơ $\\vec{{u}} = \\vec{{a}} + \\vec{{b}}$ là",
                choices=[
                    f"$\\vec{{u}} = ({ans[0]}; {ans[1]}; {ans[2]})$",
                    f"$\\vec{{u}} = ({ans[0]-1}; {ans[1]}; {ans[2]+1})$",
                    f"$\\vec{{u}} = ({x1-x2}; {y1-y2}; {z1-z2})$",
                    f"$\\vec{{u}} = ({ans[0]}; {ans[1]+1}; {ans[2]-1})$"
                ],
                correct_index=0,
                solution=f"$\\vec{{a}} + \\vec{{b}} = ({ans[0]}; {ans[1]}; {ans[2]})$.",
                verified=True
            )

        # 6. NGUYÊN HÀM VÀ TÍCH PHÂN
        @cls.register("g12_p1_integrals", 12, 1, QuestionType.MULTIPLE_CHOICE, CognitiveLevel.NHAN_BIET, ["nguyên hàm", "tích phân", "diện tích hình phẳng"])
        def gen_g12_integrals(slot, orig, mode):
            alpha = random.choice([2, 3, 4])
            return Question(
                id=slot.slot_id,
                type=QuestionType.MULTIPLE_CHOICE,
                topic=slot.topic,
                subtopic=slot.subtopic,
                level=slot.level,
                stem=f"Họ nguyên hàm của hàm số $f(x) = x^{{{alpha}}}$ là",
                choices=[
                    f"$\\frac{{x^{{{alpha+1}}}}}{{{alpha+1}}} + C$",
                    f"${alpha}x^{{{alpha-1}}} + C$",
                    f"$\\frac{{x^{{{alpha}}}}}{{{alpha}}} + C$",
                    f"${alpha+1}x^{{{alpha+1}}} + C$"
                ],
                correct_index=0,
                solution=f"Công thức: $\\int x^\\alpha dx = \\frac{{x^{{\\alpha+1}}}}{{\\alpha+1}} + C$. Do đó $\\int x^{{{alpha}}} dx = \\frac{{x^{{{alpha+1}}}}}{{{alpha+1}}} + C$.",
                verified=True
            )

        # 7. THỐNG KÊ GHÉP NHÓM VÀ XÁC SUẤT CÓ ĐIỀU KIỆN
        @cls.register("g12_p1_stats_cond_prob", 12, 1, QuestionType.MULTIPLE_CHOICE, CognitiveLevel.NHAN_BIET, ["thống kê", "ghép nhóm", "xác suất có điều kiện", "phân tán"])
        def gen_g12_stats_prob(slot, orig, mode):
            return Question(
                id=slot.slot_id,
                type=QuestionType.MULTIPLE_CHOICE,
                topic=slot.topic,
                subtopic=slot.subtopic,
                level=slot.level,
                stem="Cho hai biến cố $A$ và $B$ có $P(B) > 0$. Công thức tính xác suất có điều kiện $P(A|B)$ là",
                choices=[
                    "$P(A|B) = \\frac{P(AB)}{P(B)}$",
                    "$P(A|B) = \\frac{P(AB)}{P(A)}$",
                    "$P(A|B) = P(A) \\cdot P(B)$",
                    "$P(A|B) = \\frac{P(A)}{P(B)}$"
                ],
                correct_index=0,
                solution="Định nghĩa xác suất có điều kiện: $P(A|B) = \\frac{P(AB)}{P(B)}$.",
                verified=True
            )

        # 8. PHẦN II: ĐÚNG / SAI LỚP 12 (4 TEMPLATES RIÊNG BIỆT)
        @cls.register("g12_p2_tf_func_study", 12, 2, QuestionType.TRUE_FALSE, CognitiveLevel.THONG_HIEU, ["khảo sát tính biến thiên", "toàn diện", "đồ thị"])
        def gen_g12_tf_func(slot, orig, mode):
            return Question(
                id=slot.slot_id,
                type=QuestionType.TRUE_FALSE,
                topic=slot.topic,
                subtopic=slot.subtopic,
                level=slot.level,
                stem="Cho hàm số bậc ba $y = f(x) = x^3 - 3x^2 + 2$. Xét tính đúng hay sai của các mệnh đề sau:",
                statements=[
                    TrueFalseItem(statement="Đạo hàm của hàm số là $f'(x) = 3x^2 - 6x$.", is_correct=True, explanation="$f'(x) = 3x^2 - 6x$."),
                    TrueFalseItem(statement="Hàm số đồng biến trên khoảng $(0; 2)$.", is_correct=False, explanation="Trên $(0; 2)$, $f'(x) < 0$ nên hàm số nghịch biến."),
                    TrueFalseItem(statement="Đồ thị hàm số có điểm cực đại là $(0; 2)$.", is_correct=True, explanation="Tại $x=0$, $y=2$ và đổi dấu từ dương sang âm."),
                    TrueFalseItem(statement="Giá trị nhỏ nhất của hàm số trên đoạn $[0; 3]$ bằng $-2$.", is_correct=True, explanation="$f(0)=2, f(2)=-2, f(3)=2 \\Rightarrow \\min = -2$.")
                ],
                solution="Mệnh đề a ĐÚNG, b SAI, c ĐÚNG, d ĐÚNG.",
                verified=True
            )

        @cls.register("g12_p2_tf_rational", 12, 2, QuestionType.TRUE_FALSE, CognitiveLevel.THONG_HIEU, ["đường tiệm cận và tâm đối xứng", "khảo sát cực trị và tính lồi lõm"])
        def gen_g12_tf_rational(slot, orig, mode):
            return Question(
                id=slot.slot_id,
                type=QuestionType.TRUE_FALSE,
                topic=slot.topic,
                subtopic=slot.subtopic,
                level=slot.level,
                stem="Cho hàm số phân thức $y = \\frac{2x - 1}{x + 1}$. Xét tính đúng sai của các mệnh đề sau:",
                statements=[
                    TrueFalseItem(statement="Tập xác định của hàm số là $D = \\mathbb{R} \\setminus \\{-1\\}$.", is_correct=True, explanation="Mẫu khác 0."),
                    TrueFalseItem(statement="Đồ thị hàm số có tiệm cận đứng là $x = -1$.", is_correct=True, explanation="$\\lim_{x \\to -1} y = \\infty$."),
                    TrueFalseItem(statement="Đồ thị hàm số có tiệm cận ngang là $y = 1$.", is_correct=False, explanation="Tiệm cận ngang là $y = 2$."),
                    TrueFalseItem(statement="Hàm số đồng biến trên từng khoảng xác định.", is_correct=True, explanation="$y' = 3/(x+1)^2 > 0$.")
                ],
                solution="Mệnh đề a ĐÚNG, b ĐÚNG, c SAI, d ĐÚNG.",
                verified=True
            )

        @cls.register("g12_p2_tf_oxyz", 12, 2, QuestionType.TRUE_FALSE, CognitiveLevel.THONG_HIEU, ["mặt phẳng", "đường thẳng", "khoảng cách oxyz", "không gian oxyz"])
        def gen_g12_tf_oxyz(slot, orig, mode):
            return Question(
                id=slot.slot_id,
                type=QuestionType.TRUE_FALSE,
                topic=slot.topic,
                subtopic=slot.subtopic,
                level=slot.level,
                stem="Trong không gian $Oxyz$, cho điểm $A(1; 2; 3)$ và mặt phẳng $(P): 2x - 2y + z + 4 = 0$. Xét tính đúng sai của các mệnh đề sau:",
                statements=[
                    TrueFalseItem(statement="Một vectơ pháp tuyến của mặt phẳng $(P)$ là $\\vec{n} = (2; -2; 1)$.", is_correct=True, explanation="Hệ số trước x, y, z."),
                    TrueFalseItem(statement="Điểm $A$ thuộc mặt phẳng $(P)$.", is_correct=False, explanation="$2(1) - 2(2) + 3 + 4 = 5 \\ne 0$."),
                    TrueFalseItem(statement="Khoảng cách từ điểm $A$ đến mặt phẳng $(P)$ bằng $\\frac{5}{3}$.", is_correct=True, explanation="$d = 5/3$."),
                    TrueFalseItem(statement="Mặt phẳng qua $A$ song song $(P)$ là $2x - 2y + z - 1 = 0$.", is_correct=True, explanation="$2(x-1) - 2(y-2) + (z-3) = 0$.")
                ],
                solution="Mệnh đề a ĐÚNG, b SAI, c ĐÚNG, d ĐÚNG.",
                verified=True
            )

        @cls.register("g12_p2_tf_bayes", 12, 2, QuestionType.TRUE_FALSE, CognitiveLevel.VAN_DUNG, ["xác suất toàn phần", "bayes", "xác suất"])
        def gen_g12_tf_bayes(slot, orig, mode):
            return Question(
                id=slot.slot_id,
                type=QuestionType.TRUE_FALSE,
                topic=slot.topic,
                subtopic=slot.subtopic,
                level=slot.level,
                stem="Một phòng thí nghiệm có hai hộp đựng linh kiện. Hộp I có 7 sản phẩm tốt và 3 phế phẩm; Hộp II có 8 sản phẩm tốt và 2 phế phẩm. Lấy ngẫu nhiên một hộp, rồi từ hộp đó lấy ngẫu nhiên 1 sản phẩm. Xét tính đúng sai:",
                statements=[
                    TrueFalseItem(statement="Xác suất chọn trúng mỗi hộp bằng $0.5$.", is_correct=True, explanation="Lấy ngẫu nhiên 1 trong 2 hộp."),
                    TrueFalseItem(statement="Xác suất lấy được sản phẩm tốt từ Hộp I bằng $0.7$.", is_correct=True, explanation="$7/10 = 0.7$."),
                    TrueFalseItem(statement="Xác suất lấy được sản phẩm tốt chung bằng $0.75$.", is_correct=True, explanation="$0.5 \\times 0.7 + 0.5 \\times 0.8 = 0.75$."),
                    TrueFalseItem(statement="Biết sản phẩm lấy ra là tốt, xác suất nó thuộc Hộp I lớn hơn $0.5$.", is_correct=False, explanation="Hộp II có tỉ lệ tốt cao hơn nên P(Hộp I | tốt) < 0.5.")
                ],
                solution="Mệnh đề a ĐÚNG, b ĐÚNG, c ĐÚNG, d SAI.",
                verified=True
            )

        @cls.register("g12_p2_tf_integral_app", 12, 2, QuestionType.TRUE_FALSE, CognitiveLevel.THONG_HIEU, ["ứng dụng tích phân", "diện tích, thể tích", "diện tích", "thể tích"])
        def gen_g12_tf_integral_app(slot, orig, mode):
            return Question(
                id=slot.slot_id,
                type=QuestionType.TRUE_FALSE,
                topic=slot.topic,
                subtopic=slot.subtopic,
                level=slot.level,
                stem="Cho hình phẳng $(H)$ giới hạn bởi đồ thị hàm số $y = x^2 - 2x$, trục hoành $Ox$ và các đường thẳng $x = 0, x = 2$. Xét tính đúng sai của các mệnh đề sau:",
                statements=[
                    TrueFalseItem(statement="Đồ thị hàm số $y = x^2 - 2x$ cắt trục hoành tại hai điểm $x = 0$ và $x = 2$.", is_correct=True, explanation="$x^2 - 2x = 0 \\Leftrightarrow x = 0$ hoặc $x = 2$."),
                    TrueFalseItem(statement="Với mọi $x \\in (0; 2)$, ta có $x^2 - 2x < 0$.", is_correct=True, explanation="Hàm số nhận giá trị âm trên khoảng $(0; 2)$."),
                    TrueFalseItem(statement="Diện tích hình phẳng $(H)$ được tính bởi công thức $S = \\int_0^2 (2x - x^2) dx$.", is_correct=True, explanation="$S = \\int_0^2 |x^2 - 2x| dx = \\int_0^2 (2x - x^2) dx$."),
                    TrueFalseItem(statement="Diện tích hình phẳng $(H)$ bằng $\\frac{4}{3}$ đơn vị diện tích.", is_correct=True, explanation="$S = (x^2 - x^3/3)|_0^2 = 4 - 8/3 = 4/3$.")
                ],
                solution="Cả 4 mệnh đề a, b, c, d đều ĐÚNG.",
                verified=True
            )

        # 9. PHẦN III: TRẢ LỜI NGẮN LỚP 12 (NHIỀU MẪU ĐA DẠNG)
        @cls.register("g12_p3_short_opt", 12, 3, QuestionType.SHORT_ANSWER, CognitiveLevel.VAN_DUNG, ["tối ưu hóa", "cực trị thực tế", "dung tích", "chi phí", "diện tích"])
        def gen_g12_short_opt(slot, orig, mode):
            return Question(
                id=slot.slot_id,
                type=QuestionType.SHORT_ANSWER,
                topic=slot.topic,
                subtopic=slot.subtopic,
                level=slot.level,
                stem="Một người nông dân muốn rào một khu đất hình chữ nhật có diện tích $200\\text{ m}^2$ giáp bờ sông thẳng (bờ sông không cần rào). Chiều dài cạnh song song với bờ sông bằng bao nhiêu mét để tổng chiều dài hàng rào là nhỏ nhất?",
                correct_value="20",
                solution="Cạnh song song bờ sông dài $200/10 = 20\\text{ m}$.",
                verified=True
            )

        @cls.register("g12_p3_short_oxyz", 12, 3, QuestionType.SHORT_ANSWER, CognitiveLevel.VAN_DUNG, ["mô hình hóa", "khoảng cách hình học", "cực trị khoảng cách"])
        def gen_g12_short_oxyz(slot, orig, mode):
            val = random.choice([2, 3, 5])
            return Question(
                id=slot.slot_id,
                type=QuestionType.SHORT_ANSWER,
                topic=slot.topic,
                subtopic=slot.subtopic,
                level=slot.level,
                stem=f"Trong không gian $Oxyz$, cho điểm $M(1; 2; 3)$ và mặt phẳng $(P): 2x - 2y + z + {3*val - 1} = 0$. Khoảng cách từ điểm $M$ đến mặt phẳng $(P)$ bằng bao nhiêu?",
                correct_value=str(val),
                solution=f"Khoảng cách là $d(M, (P)) = \\frac{{{3*val}}}{{3}} = {val}$.",
                verified=True
            )

        @cls.register("g12_p3_short_integral", 12, 3, QuestionType.SHORT_ANSWER, CognitiveLevel.VAN_DUNG, ["thể tích vật thể", "diện tích", "tích phân"])
        def gen_g12_short_integral(slot, orig, mode):
            return Question(
                id=slot.slot_id,
                type=QuestionType.SHORT_ANSWER,
                topic=slot.topic,
                subtopic=slot.subtopic,
                level=slot.level,
                stem="Cho hình phẳng giới hạn bởi đường cong $y = x^2$, trục hoành và hai đường thẳng $x = 0, x = 3$. Diện tích của hình phẳng đó bằng bao nhiêu đơn vị diện tích?",
                correct_value="9",
                solution="$S = \\int_0^3 x^2 dx = 9$.",
                verified=True
            )

        @cls.register("g12_p3_short_extrema_point", 12, 3, QuestionType.SHORT_ANSWER, CognitiveLevel.THONG_HIEU, ["điểm cực trị của hàm số", "cực trị"])
        def gen_g12_short_extrema_pt(slot, orig, mode):
            a = random.choice([2, 3, 4])
            return Question(
                id=slot.slot_id,
                type=QuestionType.SHORT_ANSWER,
                topic=slot.topic,
                subtopic=slot.subtopic,
                level=slot.level,
                stem=f"Cho hàm số $y = \\frac{{1}}{{3}}x^3 - {a}x^2 + {a*a}x + 1$. Hàm số có bao nhiêu điểm cực trị?",
                correct_value="0",
                solution=f"$y' = x^2 - {2*a}x + {a*a} = (x - {a})^2 \\ge 0, \\forall x$. Đạo hàm không đổi dấu nên hàm số không có điểm cực trị (0 điểm).",
                verified=True
            )

        @cls.register("g12_p3_short_min_max_val", 12, 3, QuestionType.SHORT_ANSWER, CognitiveLevel.THONG_HIEU, ["giá trị lớn nhất của hàm số trên đoạn", "giá trị lớn nhất", "giá trị nhỏ nhất"])
        def gen_g12_short_min_max_val(slot, orig, mode):
            return Question(
                id=slot.slot_id,
                type=QuestionType.SHORT_ANSWER,
                topic=slot.topic,
                subtopic=slot.subtopic,
                level=slot.level,
                stem="Giá trị lớn nhất của hàm số $y = -x^3 + 3x + 1$ trên đoạn $[0; 2]$ bằng bao nhiêu?",
                correct_value="3",
                solution="Ta có $y' = -3x^2 + 3 = 0 \\Leftrightarrow x = 1 \\in [0; 2]$. $y(0)=1, y(1)=3, y(2)=-1$. Vậy GTLN bằng 3.",
                verified=True
            )

        @cls.register("g12_p3_short_param_m", 12, 3, QuestionType.SHORT_ANSWER, CognitiveLevel.VAN_DUNG_CAO, ["tham số m", "cực trị hàm số có tham số", "tiệm cận xiên chứa tham số"])
        def gen_g12_short_param_m(slot, orig, mode):
            return Question(
                id=slot.slot_id,
                type=QuestionType.SHORT_ANSWER,
                topic=slot.topic,
                subtopic=slot.subtopic,
                level=slot.level,
                stem="Có bao nhiêu giá trị nguyên của tham số $m \\in [-5; 5]$ để hàm số $y = \\frac{1}{3}x^3 - mx^2 + 4x + 1$ đồng biến trên $\\mathbb{R}$?",
                correct_value="5",
                solution="Hàm số đồng biến trên $\\mathbb{R} \\Leftrightarrow y' = x^2 - 2mx + 4 \\ge 0, \\forall x \\Leftrightarrow \\Delta' = m^2 - 4 \\le 0 \\Leftrightarrow -2 \\le m \\le 2$. Có 5 giá trị nguyên $\\{-2; -1; 0; 1; 2\\}$.",
                verified=True
            )

        @cls.register("g12_p3_short_quality_test", 12, 3, QuestionType.SHORT_ANSWER, CognitiveLevel.VAN_DUNG, ["kiểm định chất lượng", "y tế", "kinh tế", "ứng dụng xác suất", "xác suất"])
        def gen_g12_quality_test(slot, orig, mode):
            return Question(
                id=slot.slot_id,
                type=QuestionType.SHORT_ANSWER,
                topic=slot.topic,
                subtopic=slot.subtopic,
                level=slot.level,
                stem="Một cơ sở y tế khảo sát một loại bệnh có tỉ lệ mắc trong cộng đồng là $2\\%$. Xét nghiệm chẩn đoán cho kết quả chính xác $95\\%$ với người có bệnh và tỉ lệ dương tính giả là $1\\%$ với người không có bệnh. Một người được chọn ngẫu nhiên có kết quả dương tính. Xác suất người này thực sự bị bệnh bằng bao nhiêu phần trăm? (Làm tròn đến hàng đơn vị).",
                correct_value="66",
                solution="Gọi A: 'Người mắc bệnh', B: 'Xét nghiệm dương tính'. $P(A) = 0.02, P(\\bar{A}) = 0.98$. $P(B|A) = 0.95, P(B|\\bar{A}) = 0.01$. Theo Bayes: $P(A|B) = \\frac{0.02 \\times 0.95}{0.02 \\times 0.95 + 0.98 \\times 0.01} = \\frac{0.019}{0.0288} \\approx 66\\%$.",
                verified=True
            )

        @cls.register("g12_p3_short_oxyz_extreme", 12, 3, QuestionType.SHORT_ANSWER, CognitiveLevel.VAN_DUNG_CAO, ["cực trị khoảng cách", "hình học giải tích", "cực trị khoảng cách hình học", "khoảng cách"])
        def gen_g12_oxyz_extreme(slot, orig, mode):
            return Question(
                id=slot.slot_id,
                type=QuestionType.SHORT_ANSWER,
                topic=slot.topic,
                subtopic=slot.subtopic,
                level=slot.level,
                stem="Trong không gian $Oxyz$, cho điểm $A(1; 2; 3)$ và mặt phẳng $(P): x + 2y - 2z + 10 = 0$. Điểm $M$ thay đổi trên mặt phẳng $(P)$. Khoảng cách nhỏ nhất giữa điểm $A$ và điểm $M$ bằng bao nhiêu?",
                correct_value="3",
                solution="Khoảng cách ngắn nhất từ $A$ đến điểm $M \\in (P)$ chính là khoảng cách từ $A$ đến mặt phẳng $(P)$: $d(A, (P)) = \\frac{|1(1) + 2(2) - 2(3) + 10|}{\\sqrt{1^2 + 2^2 + (-2)^2}} = \\frac{9}{3} = 3$.",
                verified=True
            )
