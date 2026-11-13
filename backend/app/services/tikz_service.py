"""
Thư viện mẫu TikZ & tkz-tab chuẩn dành cho giáo viên Toán Việt Nam.
Giúp tránh việc AI sinh bừa code TikZ bị lỗi biên dịch.
"""
from typing import Dict, Any, Optional

class TikZLibrary:

    @staticmethod
    def get_tkz_tab_bac3(x1: str = "-1", x2: str = "2", y1: str = "4", y2: str = "-1", a_sign: str = "duong") -> str:
        """
        Bảng biến thiên hàm số bậc 3 có 2 điểm cực trị x1, x2.
        Nếu a_sign == 'duong': cực đại trước, cực tiểu sau (+ - +).
        Nếu a_sign == 'am': cực tiểu trước, cực đại sau (- + -).
        """
        if a_sign == "duong":
            return f"""\\begin{{center}}
\\begin{{tikzpicture}}
\\tkzTabInit[lgt=1.5,espcl=2.5]
{{$x$ /1, $y'$ /1, $y$ /2}}
{{$-\\infty$, ${x1}$, ${x2}$, $+\\infty$}}
\\tkzTabLine{{,+,0,-,0,+,}}
\\tkzTabVar{{-/ $-\\infty$, +/ ${y1}$, -/ ${y2}$, +/ $+\\infty$}}
\\end{{tikzpicture}}
\\end{{center}}"""
        else:
            return f"""\\begin{{center}}
\\begin{{tikzpicture}}
\\tkzTabInit[lgt=1.5,espcl=2.5]
{{$x$ /1, $y'$ /1, $y$ /2}}
{{$-\\infty$, ${x1}$, ${x2}$, $+\\infty$}}
\\tkzTabLine{{,-,0,+,0,-,}}
\\tkzTabVar{{+/ $+\\infty$, -/ ${y1}$, +/ ${y2}$, -/ $-\\infty$}}
\\end{{tikzpicture}}
\\end{{center}}"""

    @staticmethod
    def get_tkz_tab_phanthuc(x0: str = "2", y_tc: str = "1", y_prime_sign: str = "-") -> str:
        """
        Bảng biến thiên hàm phân thức bậc 1 / bậc 1: y = (ax+b)/(cx+d).
        Có tiệm cận đứng x = x0 và tiệm cận ngang y = y_tc.
        """
        if y_prime_sign == "-":
            return f"""\\begin{{center}}
\\begin{{tikzpicture}}
\\tkzTabInit[lgt=1.5,espcl=2.5]
{{$x$ /1, $y'$ /1, $y$ /2}}
{{$-\\infty$, ${x0}$, $+\\infty$}}
\\tkzTabLine{{,-,d,-,}}
\\tkzTabVar{{+/ ${y_tc}$, -D+/ $-\\infty$ / $+\\infty$, -/ ${y_tc}$}}
\\end{{tikzpicture}}
\\end{{center}}"""
        else:
            return f"""\\begin{{center}}
\\begin{{tikzpicture}}
\\tkzTabInit[lgt=1.5,espcl=2.5]
{{$x$ /1, $y'$ /1, $y$ /2}}
{{$-\\infty$, ${x0}$, $+\\infty$}}
\\tkzTabLine{{,+,d,+,}}
\\tkzTabVar{{-/ ${y_tc}$, +D-/ $+\\infty$ / $-\\infty$, +/ ${y_tc}$}}
\\end{{tikzpicture}}
\\end{{center}}"""

    @staticmethod
    def get_tkz_tab_bac4(x0: str = "-1", x1: str = "0", x2: str = "1", y_ct: str = "-2", y_cd: str = "1") -> str:
        """Bảng biến thiên hàm số trùng phương bậc 4 (3 cực trị)."""
        return f"""\\begin{{center}}
\\begin{{tikzpicture}}
\\tkzTabInit[lgt=1.5,espcl=2]
{{$x$ /1, $y'$ /1, $y$ /2}}
{{$-\\infty$, ${x0}$, ${x1}$, ${x2}$, $+\\infty$}}
\\tkzTabLine{{,-,0,+,0,-,0,+,}}
\\tkzTabVar{{+/ $+\\infty$, -/ ${y_ct}$, +/ ${y_cd}$, -/ ${y_ct}$, +/ $+\\infty$}}
\\end{{tikzpicture}}
\\end{{center}}"""

    @staticmethod
    def get_tikz_chop_tam_giac(sa_vuong_day: bool = True) -> str:
        """Hình vẽ chóp tam giác S.ABC với SA vuông góc với đáy."""
        return """\\begin{center}
\\begin{tikzpicture}[scale=0.8, >=stealth]
  \\coordinate (A) at (0,0);
  \\coordinate (B) at (-1.5,-1.5);
  \\coordinate (C) at (3.5,-1.2);
  \\coordinate (S) at (0,3.5);
  \\draw[dashed] (A) -- (B) (A) -- (C) (S) -- (A);
  \\draw (S) -- (B) -- (C) -- (S);
  \\foreach \\p/\\pos in {S/above, A/left, B/below left, C/right}
    \\fill (\\p) circle (1.5pt) node[\\pos] {$\\p$};
  \\draw (0,0.3) -- (0.3,0.3) -- (0.3,0);
\\end{tikzpicture}
\\end{center}"""

    @staticmethod
    def get_tikz_chop_tu_giac() -> str:
        """Hình vẽ chóp tứ giác S.ABCD với đáy ABCD là hình bình hành, SA vuông góc với đáy."""
        return """\\begin{center}
\\begin{tikzpicture}[scale=0.8, >=stealth]
  \\coordinate (A) at (0,0);
  \\coordinate (B) at (-1.5,-1.5);
  \\coordinate (C) at (2.5,-1.5);
  \\coordinate (D) at (4,0);
  \\coordinate (S) at (0,3.5);
  \\draw[dashed] (A) -- (B) (A) -- (D) (S) -- (A);
  \\draw (B) -- (C) -- (D) (S) -- (B) (S) -- (C) (S) -- (D);
  \\foreach \\p/\\pos in {S/above, A/left, B/below left, C/below right, D/right}
    \\fill (\\p) circle (1.5pt) node[\\pos] {$\\p$};
  \\draw (0,0.3) -- (0.3,0.3) -- (0.3,0);
\\end{tikzpicture}
\\end{center}"""

    @staticmethod
    def get_tikz_lang_tru_tam_giac() -> str:
        """Hình vẽ lăng trụ tam giác ABC.A'B'C'."""
        return """\\begin{center}
\\begin{tikzpicture}[scale=0.8, >=stealth]
  \\coordinate (A) at (0,0);
  \\coordinate (B) at (-1.5,-1.2);
  \\coordinate (C) at (2.5,-1.0);
  \\coordinate (A1) at (0,3.2);
  \\coordinate (B1) at (-1.5,2.0);
  \\coordinate (C1) at (2.5,2.2);
  \\draw[dashed] (A) -- (B) (A) -- (C) (A) -- (A1);
  \\draw (B) -- (C) (B) -- (B1) (C) -- (C1);
  \\draw (A1) -- (B1) -- (C1) -- (A1);
  \\foreach \\p/\\pos in {A/left, B/below left, C/right, A1/above left, B1/left, C1/right}
    \\fill (\\p) circle (1.5pt) node[\\pos] {$\\p$};
\\end{tikzpicture}
\\end{center}"""
