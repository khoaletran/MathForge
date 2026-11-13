import io
import unittest

from docx import Document
from docx.oxml.ns import qn

from app.models.question import ExamPaper, Question, QuestionType, CognitiveLevel
from app.services.docx_service import create_docx, readable_math, _choice_columns


class DocxExportTest(unittest.TestCase):
    def test_matches_preview_header_and_choice_rows(self):
        question = Question(
            id="q1", type=QuestionType.MULTIPLE_CHOICE, topic="Tập hợp",
            level=CognitiveLevel.NHAN_BIET,
            stem=r"Cho tập hợp $A=\{12;15;18;21\}$. $15\in A$?",
            choices=[r"$10\in A$", r"$15\in A$", r"$14\in A$", r"$20\in A$"],
            correct_index=1, solution="15 thuộc A",
        )
        paper = ExamPaper(
            id="sample", title="ĐỀ KIỂM TRA CUỐI HỌC KỲ 1 - TOÁN 6",
            exam_name="ĐỀ KIỂM TRA CUỐI HỌC KỲ 1 - TOÁN 6",
            questions=[question],
        )
        document = Document(io.BytesIO(create_docx(paper, False)))
        self.assertEqual(len(document.tables), 2)
        self.assertEqual(len(document.tables[0].columns), 2)
        self.assertEqual(len(document.tables[1].rows), 1)
        self.assertEqual(len(document.tables[1].columns), 4)
        self.assertEqual(document.tables[1].cell(0, 1).text, "B. 15∈ A")
        self.assertIn("A={12;15;18;21}", " ".join(p.text for p in document.paragraphs))
        self.assertEqual(sum(p.text == paper.title for p in document.paragraphs), 0)
        self.assertEqual(len(document.tables[0].cell(0, 0).text.splitlines()), 3)

    def test_math_symbols_and_long_choices(self):
        self.assertEqual(readable_math(r"$-3^\circ C$, $x^2$, $\frac{7}{8}$"), "-3°C, x², (7)/(8)")
        self.assertEqual(readable_math("Nhiệt độ là -3^{°}C, tăng thêm 7^{°}C."),
                         "Nhiệt độ là -3°C, tăng thêm 7°C.")
        self.assertEqual(readable_math(r"$4^{\circ}C$"), "4°C")
        self.assertEqual(readable_math(r"$\infty$, $\notin$"), "∞, ∉")
        self.assertEqual(_choice_columns(["Một phương án có nội dung rất dài để cần xuống dòng"] * 4, "auto"), 1)

    def test_two_column_document(self):
        paper = ExamPaper(id="sample", title="Đề kiểm tra", questions=[])
        document = Document(io.BytesIO(create_docx(paper, True, column_mode=2)))
        self.assertEqual(document.sections[1]._sectPr.xpath("./w:cols")[0].get(qn("w:num")), "2")
        self.assertEqual(document.sections[-1]._sectPr.xpath("./w:cols")[0].get(qn("w:num")), "1")


if __name__ == "__main__":
    unittest.main()
