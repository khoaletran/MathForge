"""Export an editable exam paper as a Word document."""

import io
import re

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.section import WD_SECTION_START
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

from app.models.question import ExamPaper, QuestionType


def readable_math(text: str) -> str:
    """Keep formulas editable while displaying common LaTeX notation in Word."""
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = text.replace("$$", "").replace("$", "")
    text = re.sub(r"\\frac\{([^{}]+)\}\{([^{}]+)\}", r"(\1)/(\2)", text)
    text = re.sub(r"\\sqrt\{([^{}]+)\}", r"√(\1)", text)
    text = re.sub(r"\\sqrt\[([^]]+)\]\{([^{}]+)\}", r"\1√(\2)", text)
    commands = {
        "infty": "∞", "times": "×", "cdot": "·", "div": "÷",
        "le": "≤", "leq": "≤", "ge": "≥", "geq": "≥", "neq": "≠",
        "pi": "π", "alpha": "α", "beta": "β", "theta": "θ",
        "circ": "°", "notin": "∉", "in": "∈", "mathbb{R}": "ℝ", "mathbb{N}": "ℕ",
    }
    for command, symbol in commands.items():
        text = re.sub(r"\\" + re.escape(command) + r"(?![A-Za-z])", lambda _: symbol, text)
    text = text.replace(r"\{", "{").replace(r"\}", "}")
    text = text.replace("\\,", " ").replace("\\;", " ")
    text = text.replace("\\left", "").replace("\\right", "")
    text = re.sub(r"\^\{\s*°\s*\}|\^°", "°", text)
    text = re.sub(r"°\s*C\b", "°C", text)
    superscripts = str.maketrans("0123456789+-=n", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼ⁿ")
    text = re.sub(r"\^\{([0-9+\-=n]+)\}|\^([0-9+\-=n])",
                  lambda m: (m.group(1) or m.group(2)).translate(superscripts), text)
    text = re.sub(r"_\{([^{}]+)\}", r"_\1", text)
    return text


def _choice_columns(choices: list[str], layout: str) -> int:
    if layout in ("1col", "2col", "4col"):
        return int(layout[0])
    longest = max((len(choice.strip()) for choice in choices), default=0)
    return 4 if longest <= 18 else 2 if longest <= 42 else 1


def _add_choices(document: Document, choices: list[str], layout: str, column_mode: int) -> None:
    if not choices:
        return
    columns = _choice_columns(choices, layout)
    table = document.add_table(rows=(len(choices) + columns - 1) // columns, cols=columns)
    table.autofit = False
    width = Cm((8.5 if column_mode == 2 else 17.4) / columns)
    for column in table.columns:
        column.width = width
    for row in table.rows:
        for cell in row.cells:
            cell.width = width
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            cell.paragraphs[0].paragraph_format.space_after = Pt(1)
    for index, choice in enumerate(choices):
        paragraph = table.cell(index // columns, index % columns).paragraphs[0]
        paragraph.add_run(f"{'ABCD'[index]}. ").bold = True
        paragraph.add_run(readable_math(choice))


def create_docx(paper: ExamPaper, include_solution: bool, *,
                choice_layout: str = "auto", font_size: str = "sm",
                density: str = "normal", column_mode: int = 1) -> bytes:
    document = Document()
    section = document.sections[0]
    section.page_width, section.page_height = Cm(21), Cm(29.7)
    section.top_margin = section.bottom_margin = Cm(1.5)
    section.left_margin = section.right_margin = Cm(1.8)
    normal = document.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt({"sm": 11, "base": 12, "lg": 13}.get(font_size, 11))
    normal.paragraph_format.space_after = Pt(2)

    header = document.add_table(rows=1, cols=2)
    header.autofit = False
    for cell in header.rows[0].cells:
        cell.width = Cm(8.7)
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.TOP
        tc_pr = cell._tc.get_or_add_tcPr()
        borders = OxmlElement("w:tcBorders")
        bottom = OxmlElement("w:bottom")
        bottom.set(qn("w:val"), "single")
        bottom.set(qn("w:sz"), "5")
        borders.append(bottom)
        tc_pr.append(borders)
    for cell, lines in (
        (header.cell(0, 0), [(paper.school_name, True, False), (paper.exam_name, True, False), (f"Năm học: {paper.academic_year}", False, True)]),
        (header.cell(0, 1), [(paper.title, True, False), (f"Thời gian làm bài: {paper.time_minutes} phút", False, True), (f"Mã đề thi: {paper.exam_code}", True, False)]),
    ):
        for line_index, (text, bold, italic) in enumerate(lines):
            paragraph = cell.paragraphs[0] if line_index == 0 else cell.add_paragraph()
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            paragraph.paragraph_format.space_after = Pt(0)
            run = paragraph.add_run(text)
            run.bold, run.italic = bold, italic

    if column_mode == 2:
        content_section = document.add_section(WD_SECTION_START.CONTINUOUS)
        columns = content_section._sectPr.xpath("./w:cols")[0]
        columns.set(qn("w:num"), "2")
        columns.set(qn("w:space"), "425")

    current_type = None
    part_number = 0
    part_titles = {
        QuestionType.MULTIPLE_CHOICE: "Trắc nghiệm nhiều phương án lựa chọn",
        QuestionType.TRUE_FALSE: "Trắc nghiệm đúng sai",
        QuestionType.SHORT_ANSWER: "Trả lời ngắn",
        QuestionType.ESSAY: "Tự luận",
    }
    for index, question in enumerate(paper.questions, start=1):
        if question.type != current_type:
            current_type = question.type
            part_number += 1
            descriptions = {
                QuestionType.MULTIPLE_CHOICE: "Thí sinh trả lời từng câu hỏi. Mỗi câu hỏi thí sinh chỉ chọn một phương án.",
                QuestionType.TRUE_FALSE: "Trong mỗi ý a), b), c), d) ở mỗi câu, thí sinh chọn đúng hoặc sai.",
                QuestionType.SHORT_ANSWER: "Thí sinh điền kết quả vào ô tương ứng.",
                QuestionType.ESSAY: "Thí sinh trình bày chi tiết các bước giải và lập luận trên giấy làm bài.",
            }
            paragraph = document.add_paragraph()
            paragraph.paragraph_format.space_before = Pt(9)
            paragraph.paragraph_format.space_after = Pt(0)
            paragraph.paragraph_format.keep_with_next = True
            paragraph.add_run(f"PHẦN {('I', 'II', 'III', 'IV')[part_number - 1]}. {part_titles[question.type]}.").bold = True
            paragraph = document.add_paragraph()
            paragraph.paragraph_format.space_after = Pt(4)
            paragraph.paragraph_format.keep_with_next = True
            paragraph.add_run(descriptions[question.type]).italic = True
        paragraph = document.add_paragraph()
        paragraph.paragraph_format.space_before = Pt({"compact": 3, "normal": 5, "spacious": 8}.get(density, 5))
        paragraph.paragraph_format.space_after = Pt(2)
        paragraph.paragraph_format.keep_with_next = question.type in (QuestionType.MULTIPLE_CHOICE, QuestionType.TRUE_FALSE)
        paragraph.add_run(f"Câu {index}. ").bold = True
        paragraph.add_run(readable_math(question.stem))
        if question.type == QuestionType.MULTIPLE_CHOICE:
            _add_choices(document, question.choices or [], choice_layout, column_mode)
        elif question.type == QuestionType.TRUE_FALSE:
            for letter, item in zip("abcd", question.statements or []):
                item_paragraph = document.add_paragraph()
                item_paragraph.paragraph_format.left_indent = Cm(0.6)
                item_paragraph.add_run(f"{letter}) ").bold = True
                item_paragraph.add_run(readable_math(item.statement))
        elif question.type == QuestionType.SHORT_ANSWER:
            document.add_paragraph("Đáp số: [..........]")

    end = document.add_paragraph("---------- HẾT ----------")
    end.alignment = WD_ALIGN_PARAGRAPH.CENTER
    end.paragraph_format.space_before = Pt(9)
    end.runs[0].bold = True
    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    footer.add_run("Trang ")
    page = OxmlElement("w:fldSimple")
    page.set(qn("w:instr"), "PAGE")
    footer._p.append(page)

    if include_solution:
        if column_mode == 2:
            solution_section = document.add_section(WD_SECTION_START.NEW_PAGE)
            solution_section._sectPr.xpath("./w:cols")[0].set(qn("w:num"), "1")
        else:
            document.add_page_break()
        document.add_paragraph("ĐÁP ÁN VÀ LỜI GIẢI", style="Heading 1")
        for index, question in enumerate(paper.questions, start=1):
            paragraph = document.add_paragraph()
            paragraph.add_run(f"Câu {index}. ").bold = True
            if question.type == QuestionType.MULTIPLE_CHOICE and question.correct_index is not None:
                paragraph.add_run(f"Đáp án {'ABCD'[question.correct_index]}. ")
            elif question.type == QuestionType.SHORT_ANSWER and question.correct_value:
                paragraph.add_run(f"Đáp số {question.correct_value}. ")
            elif question.type == QuestionType.TRUE_FALSE:
                paragraph.add_run("; ".join(
                    f"{letter}) {'Đúng' if item.is_correct else 'Sai'}"
                    for letter, item in zip("abcd", question.statements or [])
                ) + ". ")
            paragraph.add_run(readable_math(question.solution))

    output = io.BytesIO()
    document.save(output)
    return output.getvalue()
