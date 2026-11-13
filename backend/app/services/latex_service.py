import re
from typing import List, Dict, Any, Optional
from app.models.question import Question, QuestionType, ExamPaper

class LaTeXService:
    """
    Dịch vụ chuyển đổi cấu trúc Question và ExamPaper sang mã nguồn LaTeX chuẩn `ex_test.sty`
    Đảm bảo không lỗi cú pháp, cân bằng dấu ngoặc {}, hỗ trợ đầy đủ 4 dạng thức thi 2025.
    """

    @classmethod
    def clean_math_text(cls, text: str) -> str:
        """Chuẩn hóa ký tự công thức toán học nếu cần."""
        if not text:
            return ""
        def format_infinity(part: str) -> str:
            return re.sub(
                r"(?:\\+infty(?![a-zA-Z])|∞)",
                lambda _: r"\infty" if part.startswith("$") else r"\ensuremath{\infty}",
                part,
            )

        parts = re.split(r"(\$\$[\s\S]*?\$\$|\$[^$]+\$)", text.strip())
        return "".join(format_infinity(part) for part in parts)

    @classmethod
    def question_to_latex(cls, q: Question, include_solution: bool = True) -> str:
        """Chuyển đổi 1 câu hỏi sang LaTeX dạng \\begin{ex}...\\end{ex} hoặc \\begin{bt}."""
        lines = []
        is_essay = (q.type == QuestionType.ESSAY)
        env = "bt" if is_essay else "ex"

        lines.append(f"\\begin{{{env}}}")
        
        # Đề bài
        stem_text = cls.clean_math_text(q.stem)
        lines.append(stem_text)

        # Nếu có hình vẽ hoặc bảng biến thiên TikZ/tkz-tab
        if q.tikz_code and q.tikz_code.strip():
            lines.append("")
            lines.append(q.tikz_code.strip())
            lines.append("")

        # Phần phương án theo từng dạng câu
        if q.type == QuestionType.MULTIPLE_CHOICE:
            choices = q.choices or ["", "", "", ""]
            # Đảm bảo đủ 4 phương án
            while len(choices) < 4:
                choices.append("")
            
            c_lines = []
            for i in range(4):
                c_text = cls.clean_math_text(choices[i])
                if q.correct_index == i:
                    c_lines.append(f"  {{\\True {c_text}}}")
                else:
                    c_lines.append(f"  {{{c_text}}}")
            
            lines.append("\\choice")
            lines.extend(c_lines)

        elif q.type == QuestionType.TRUE_FALSE:
            statements = q.statements or []
            s_lines = []
            for i, st in enumerate(statements[:4]):
                text = cls.clean_math_text(st.statement)
                if st.is_correct:
                    s_lines.append(f"  {{\\True {text}}}")
                else:
                    s_lines.append(f"  {{{text}}}")
            
            # Nếu chưa đủ 4 ý thì bù thêm
            labels = ["a", "b", "c", "d"]
            while len(s_lines) < 4:
                idx = len(s_lines)
                s_lines.append(f"  {{Mệnh đề {labels[idx]}}}")

            lines.append("\\choiceTF")
            lines.extend(s_lines)

        elif q.type == QuestionType.SHORT_ANSWER:
            ans_val = cls.clean_math_text(q.correct_value or "")
            lines.append(f"\\shortans{{{ans_val}}}")

        # Lời giải chi tiết
        if include_solution and q.solution and q.solution.strip():
            sol_text = cls.clean_math_text(q.solution)
            lines.append("\\loigiai{")
            lines.append(sol_text)
            lines.append("}")

        lines.append(f"\\end{{{env}}}")
        return "\n".join(lines)

    @classmethod
    def generate_full_exam_latex(cls, paper: ExamPaper, include_solution: bool = True) -> str:
        """Tạo toàn bộ file .tex hoàn chỉnh sẵn sàng biên dịch sang PDF."""
        # Phân loại câu hỏi theo từng phần
        part1_questions = [q for q in paper.questions if q.type == QuestionType.MULTIPLE_CHOICE]
        part2_questions = [q for q in paper.questions if q.type == QuestionType.TRUE_FALSE]
        part3_questions = [q for q in paper.questions if q.type == QuestionType.SHORT_ANSWER]
        part4_questions = [q for q in paper.questions if q.type == QuestionType.ESSAY]

        # Tiền tố (Preamble)
        preamble = r"""\documentclass[12pt,a4paper]{article}
\usepackage[utf8]{vietnam}
\usepackage{amsmath,amssymb,amsfonts}
\usepackage{graphicx}
\usepackage{tikz}
\usepackage{tkz-tab}
\usepackage[top=1.5cm,bottom=1.5cm,left=1.5cm,right=1.5cm]{geometry}
\usepackage{multicol}
\usepackage{enumitem}
\usepackage{calc}

% Định nghĩa môi trường nếu chưa có ex_test.sty
\makeatletter
\@ifpackageloaded{ex_test}{}{
  \newcounter{excounter}
  \setcounter{excounter}{0}
  \newcommand{\True}{\textbf{\textsf{[Đúng]}} }
  \newcommand{\loigiai}[1]{\par\noindent\textbf{\textit{Lời giải:}}\par ##1\vspace{0.5em}}
  \newenvironment{ex}{%
    \refstepcounter{excounter}%
    \par\penalty -200\vspace{0.5em}\noindent\textbf{Câu \theexcounter.} %
  }{\par\vspace{0.3em}}
  \newenvironment{bt}{%
    \refstepcounter{excounter}%
    \par\penalty -200\vspace{0.5em}\noindent\textbf{Bài \theexcounter.} %
  }{\par\vspace{0.3em}}
  
  % Tự động đo chiều dài để phân phối phương án A, B, C, D thành 4 cột, 2 cột hoặc 1 cột vừa vặn trang A4
  \newlength{\choice@wd}
  \newlength{\choice@maxwd}
  \newcommand{\choice}[4]{%
    \par\vspace{0.2em}%
    \nopagebreak%
    \settowidth{\choice@maxwd}{\textbf{A.}~##1}%
    \settowidth{\choice@wd}{\textbf{B.}~##2}%
    \ifdim\choice@wd>\choice@maxwd \setlength{\choice@maxwd}{\choice@wd}\fi%
    \settowidth{\choice@wd}{\textbf{C.}~##3}%
    \ifdim\choice@wd>\choice@maxwd \setlength{\choice@maxwd}{\choice@wd}\fi%
    \settowidth{\choice@wd}{\textbf{D.}~##4}%
    \ifdim\choice@wd>\choice@maxwd \setlength{\choice@maxwd}{\choice@wd}\fi%
    \noindent%
    \ifdim\choice@maxwd<0.22\linewidth% 1 hàng 4 cột
      \begin{tabular*}{\linewidth}{@{\extracolsep{\fill}}llll}%
        \textbf{A.}~##1 & \textbf{B.}~##2 & \textbf{C.}~##3 & \textbf{D.}~##4%
      \end{tabular*}%
    \else\ifdim\choice@maxwd<0.46\linewidth% 2 hàng 2 cột
      \begin{tabular*}{\linewidth}{@{\extracolsep{\fill}}ll}%
        \textbf{A.}~##1 & \textbf{B.}~##2 \\%
        \textbf{C.}~##3 & \textbf{D.}~##4%
      \end{tabular*}%
    \else% 4 hàng 1 cột
      \begin{tabular*}{\linewidth}{@{\extracolsep{\fill}}l}%
        \textbf{A.}~##1 \\%
        \textbf{B.}~##2 \\%
        \textbf{C.}~##3 \\%
        \textbf{D.}~##4%
      \end{tabular*}%
    \fi\fi%
    \par\vspace{0.2em}%
  }
  \newcommand{\choiceTF}[4]{%
    \par\vspace{0.2em}%
    \nopagebreak%
    \begin{enumerate}[label=\textbf{\alph*)}, leftmargin=1.8em, itemsep=0.1em, topsep=0.1em]
      \item ##1
      \item ##2
      \item ##3
      \item ##4
    \end{enumerate}%
  }
  \newcommand{\shortans}[1]{%
    \par\vspace{0.2em}\nopagebreak\noindent\textbf{Đáp số:} \framebox[2.5cm]{\rule{0pt}{1.2em}\textbf{##1}}\par
  }
}
\makeatother

\begin{document}
"""

        # Header đề thi
        header = f"""
\\noindent
\\begin{{minipage}}[t]{{0.45\\textwidth}}
  \\centering
  \\textbf{{{paper.school_name}}}\\\\
  \\textbf{{{paper.exam_name}}}\\\\
  \\textit{{Năm học: {paper.academic_year}}}
\\end{{minipage}}
\\hfill
\\begin{{minipage}}[t]{{0.5\\textwidth}}
  \\centering
  \\textbf{{{paper.title}}}\\\\
  \\textit{{Thời gian làm bài: {paper.time_minutes} phút (không kể thời gian phát đề)}}\\\\
  \\textbf{{Mã đề thi: {paper.exam_code}}}
\\end{{minipage}}

\\vspace{{0.5em}}
\\noindent\\rule{{\\textwidth}}{{0.4pt}}
\\vspace{{0.5em}}
"""

        body_parts = []
        part_idx = 1
        roman_map = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V"}

        # Trắc nghiệm nhiều phương án lựa chọn
        if part1_questions:
            roman = roman_map.get(part_idx, str(part_idx))
            body_parts.append(rf"""
\noindent\textbf{{\large PHẦN {roman}. Câu trắc nghiệm nhiều phương án lựa chọn.}}
\textit{{Thí sinh trả lời từ câu 1 đến câu {len(part1_questions)}. Mỗi câu hỏi thí sinh chỉ chọn một phương án.}}
\vspace{{0.5em}}
""")
            for q in part1_questions:
                body_parts.append(cls.question_to_latex(q, include_solution=include_solution))
            part_idx += 1

        # Trắc nghiệm đúng sai
        if part2_questions:
            roman = roman_map.get(part_idx, str(part_idx))
            body_parts.append(rf"""
\vspace{{1em}}
\noindent\textbf{{\large PHẦN {roman}. Câu trắc nghiệm đúng sai.}}
\textit{{Thí sinh trả lời từ câu 1 đến câu {len(part2_questions)}. Trong mỗi ý a), b), c), d) ở mỗi câu, thí sinh chọn đúng hoặc sai.}}
\vspace{{0.5em}}
""")
            for q in part2_questions:
                body_parts.append(cls.question_to_latex(q, include_solution=include_solution))
            part_idx += 1

        # Trắc nghiệm trả lời ngắn
        if part3_questions:
            roman = roman_map.get(part_idx, str(part_idx))
            body_parts.append(rf"""
\vspace{{1em}}
\noindent\textbf{{\large PHẦN {roman}. Câu trắc nghiệm trả lời ngắn.}}
\textit{{Thí sinh trả lời từ câu 1 đến câu {len(part3_questions)}.}}
\vspace{{0.5em}}
""")
            for q in part3_questions:
                body_parts.append(cls.question_to_latex(q, include_solution=include_solution))
            part_idx += 1

        # Tự luận
        if part4_questions:
            roman = roman_map.get(part_idx, str(part_idx))
            title_str = f"PHẦN {roman}. Tự luận." if (part1_questions or part2_questions or part3_questions) else "PHẦN TỰ LUẬN."
            body_parts.append(rf"""
\vspace{{1em}}
\noindent\textbf{{\large {title_str}}}
\textit{{Thí sinh trình bày chi tiết các bước giải và lập luận trên giấy làm bài.}}
\vspace{{0.5em}}
""")
            for q in part4_questions:
                body_parts.append(cls.question_to_latex(q, include_solution=include_solution))
            part_idx += 1

        # BẢNG ĐÁP ÁN TỔNG HỢP (NẾU CÓ)
        answer_key = cls._generate_answer_key_table(paper)

        footer = r"""
\vspace{1.5em}
\centerline{---------- \textbf{HẾT} ----------}
\end{document}
"""

        return preamble + header + "\n".join(body_parts) + answer_key + footer

    @classmethod
    def _generate_answer_key_table(cls, paper: ExamPaper) -> str:
        """Tạo bảng tra cứu đáp án ở cuối đề thi."""
        part1 = [q for q in paper.questions if q.type == QuestionType.MULTIPLE_CHOICE]
        part2 = [q for q in paper.questions if q.type == QuestionType.TRUE_FALSE]
        part3 = [q for q in paper.questions if q.type == QuestionType.SHORT_ANSWER]

        letters = ["A", "B", "C", "D"]
        out = [r"""
\newpage
\noindent\textbf{\Large BẢNG ĐÁP ÁN THAM KHẢO}
\vspace{0.8em}
"""]

        # Bảng phần I
        if part1:
            out.append(r"\noindent\textbf{1. Bảng đáp án Phần I:}")
            out.append(r"\begin{center}")
            out.append(r"\begin{tabular}{|" + "c|" * min(len(part1), 12) + "}")
            out.append(r"\hline")
            cols_header = " & ".join([f"\\textbf{{Câu {i+1}}}" for i in range(len(part1))])
            cols_ans = " & ".join([letters[q.correct_index] if q.correct_index is not None and 0 <= q.correct_index < 4 else "-" for q in part1])
            out.append(cols_header + r" \\ \hline")
            out.append(cols_ans + r" \\ \hline")
            out.append(r"\end{tabular}")
            out.append(r"\end{center}")

        # Bảng phần II
        if part2:
            out.append(r"\vspace{0.5em}")
            out.append(r"\noindent\textbf{2. Bảng đáp án Phần II (Đ/S):}")
            out.append(r"\begin{center}")
            out.append(r"\begin{tabular}{|c|c|c|c|c|}")
            out.append(r"\hline")
            out.append(r"\textbf{Câu} & \textbf{Ý a} & \textbf{Ý b} & \textbf{Ý c} & \textbf{Ý d} \\ \hline")
            for idx, q in enumerate(part2):
                st = q.statements or []
                symbols = []
                for s in st[:4]:
                    symbols.append("Đ" if s.is_correct else "S")
                while len(symbols) < 4:
                    symbols.append("-")
                out.append(f"Câu {idx+1} & " + " & ".join(symbols) + r" \\ \hline")
            out.append(r"\end{tabular}")
            out.append(r"\end{center}")

        # Bảng phần III
        if part3:
            out.append(r"\vspace{0.5em}")
            out.append(r"\noindent\textbf{3. Bảng đáp án Phần III (Trả lời ngắn):}")
            out.append(r"\begin{center}")
            out.append(r"\begin{tabular}{|" + "c|" * min(len(part3), 6) + "}")
            out.append(r"\hline")
            cols_header = " & ".join([f"\\textbf{{Câu {i+1}}}" for i in range(len(part3))])
            cols_ans = " & ".join([f"${q.correct_value}$" if q.correct_value else "-" for q in part3])
            out.append(cols_header + r" \\ \hline")
            out.append(cols_ans + r" \\ \hline")
            out.append(r"\end{tabular}")
            out.append(r"\end{center}")

        return "\n".join(out)
