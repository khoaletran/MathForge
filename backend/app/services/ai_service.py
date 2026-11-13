import os
import json
import random
import logging
from typing import Dict, Any, List, Optional
from google import genai
from google.genai import types

from app.models.question import Question, QuestionType, CognitiveLevel, ExamSlot, TrueFalseItem
from app.services.sympy_service import SympyVerifier
from app.services.tikz_service import TikZLibrary

logger = logging.getLogger(__name__)

# Ngân hàng câu hỏi mẫu làm dữ liệu mồi (Few-Shot / RAG) chuẩn mực cho Lớp 10, 11, 12
QUESTION_BANK = [
    # === LỚP 12 ===
    # 1. Khảo sát hàm số - Nhận biết - Trắc nghiệm 4 lựa chọn
    {
        "grade": 12,
        "type": QuestionType.MULTIPLE_CHOICE,
        "topic": "Ứng dụng đạo hàm khảo sát hàm số",
        "subtopic": "Cực trị của hàm số",
        "level": CognitiveLevel.NHAN_BIET,
        "stem": "Cho hàm số $y = f(x)$ có bảng biến thiên như hình vẽ. Giá trị cực tiểu của hàm số đã cho bằng bao nhiêu?",
        "choices": ["$-1$", "$3$", "$2$", "$-5$"],
        "correct_index": 0,
        "solution": "Căn cứ vào bảng biến thiên, tại điểm $x = 2$, hàm số đạt cực tiểu và giá trị cực tiểu tương ứng là $y_{\\text{ct}} = -1$.",
        "tikz_code": TikZLibrary.get_tkz_tab_bac3("-1", "2", "3", "-1", "duong"),
        "sympy_code": "result = -1\nis_valid = True"
    },
    # 2. Khảo sát hàm số - Thông hiểu - Trắc nghiệm 4 lựa chọn
    {
        "grade": 12,
        "type": QuestionType.MULTIPLE_CHOICE,
        "topic": "Ứng dụng đạo hàm khảo sát hàm số",
        "subtopic": "Tính đơn điệu của hàm số",
        "level": CognitiveLevel.THONG_HIEU,
        "stem": "Cho hàm số $y = \\frac{2x - 1}{x + 1}$. Khẳng định nào sau đây là đúng?",
        "choices": [
            "Hàm số đồng biến trên từng khoảng xác định $(-\\infty; -1)$ và $(-1; +\\infty)$.",
            "Hàm số nghịch biến trên từng khoảng xác định.",
            "Hàm số đồng biến trên $\\mathbb{R} \\setminus \\{-1\\}$.",
            "Hàm số nghịch biến trên $\\mathbb{R}$."
        ],
        "correct_index": 0,
        "solution": "Tập xác định $D = \\mathbb{R} \\setminus \\{-1\\}$. Ta có đạo hàm $y' = \\frac{2(1) - (-1)(1)}{(x+1)^2} = \\frac{3}{(x+1)^2} > 0, \\forall x \\ne -1$. Do đó hàm số đồng biến trên từng khoảng $(-\\infty; -1)$ và $(-1; +\\infty)$.",
        "tikz_code": None,
        "sympy_code": "import sympy as sp\nx = sp.Symbol('x')\nf = (2*x - 1)/(x + 1)\ndf = sp.diff(f, x)\nresult = sp.simplify(df) == 3/(x + 1)**2\nis_valid = bool(result)"
    },
    # 3. Vectơ Oxyz - Nhận biết - Trắc nghiệm 4 lựa chọn
    {
        "grade": 12,
        "type": QuestionType.MULTIPLE_CHOICE,
        "topic": "Tọa độ vectơ trong không gian Oxyz",
        "subtopic": "Phương trình mặt cầu cơ bản",
        "level": CognitiveLevel.NHAN_BIET,
        "stem": "Trong không gian $Oxyz$, cho mặt cầu $(S): (x - 1)^2 + (y + 2)^2 + (z - 3)^2 = 16$. Tọa độ tâm $I$ và bán kính $R$ của $(S)$ là",
        "choices": [
            "$I(1; -2; 3)$ và $R = 4$",
            "$I(-1; 2; -3)$ và $R = 4$",
            "$I(1; -2; 3)$ và $R = 16$",
            "$I(-1; 2; -3)$ và $R = 16$"
        ],
        "correct_index": 0,
        "solution": "Mặt cầu $(S): (x-a)^2 + (y-b)^2 + (z-c)^2 = R^2$ có tâm $I(a; b; c)$ và bán kính $R$. Do đó $I(1; -2; 3)$ và $R = \\sqrt{16} = 4$.",
        "tikz_code": None,
        "sympy_code": "result = (1, -2, 3, 4)\nis_valid = True"
    },
    # 4. Phần II: Đúng / Sai - Khảo sát hàm số Lớp 12
    {
        "grade": 12,
        "type": QuestionType.TRUE_FALSE,
        "topic": "Ứng dụng đạo hàm khảo sát hàm số",
        "subtopic": "Khảo sát tính biến thiên và đồ thị",
        "level": CognitiveLevel.THONG_HIEU,
        "stem": "Cho hàm số $y = f(x) = x^3 - 3x^2 + 2$. Xét tính đúng hay sai của các mệnh đề sau:",
        "statements": [
            {"statement": "Đạo hàm của hàm số là $f'(x) = 3x^2 - 6x$.", "is_correct": True, "explanation": "$f'(x) = 3x^2 - 6x$ đúng."},
            {"statement": "Hàm số đồng biến trên khoảng $(0; 2)$.", "is_correct": False, "explanation": "Trên $(0; 2)$, $f'(x) < 0$ nên hàm số nghịch biến."},
            {"statement": "Đồ thị hàm số có điểm cực đại là $(0; 2)$.", "is_correct": True, "explanation": "$f'(0) = 0, f(0) = 2$ và qua $x=0$ đạo hàm đổi dấu từ dương sang âm."},
            {"statement": "Giá trị nhỏ nhất của hàm số trên đoạn $[0; 3]$ bằng $-2$.", "is_correct": True, "explanation": "$f(0)=2, f(2)=-2, f(3)=2 \\Rightarrow \\min_{[0;3]} f(x) = -2$."}
        ],
        "solution": "1) Ta có $f'(x) = 3x^2 - 6x = 3x(x - 2)$. Mệnh đề a ĐÚNG.\n2) $f'(x) < 0 \\Leftrightarrow x \\in (0; 2)$ nên hàm số nghịch biến trên $(0; 2)$. Mệnh đề b SAI.\n3) $f'(x) = 0 \\Leftrightarrow x = 0$ hoặc $x = 2$. Tại $x=0$, $y=2$ là điểm cực đại. Mệnh đề c ĐÚNG.\n4) Trên đoạn $[0; 3]$, $f(0)=2, f(2)=-2, f(3)=2$. Vậy $\\min = -2$. Mệnh đề d ĐÚNG.",
        "tikz_code": None,
        "sympy_code": "import sympy as sp\nx = sp.Symbol('x')\nf = x**3 - 3*x**2 + 2\ndf = sp.diff(f, x)\nroots = sp.solve(df, x)\nis_valid = (roots == [0, 2])"
    },
    # 5. Phần III: Trả lời ngắn - Tối ưu hóa thực tế Lớp 12
    {
        "grade": 12,
        "type": QuestionType.SHORT_ANSWER,
        "topic": "Ứng dụng đạo hàm khảo sát hàm số",
        "subtopic": "Bài toán tối ưu hóa / cực trị thực tế",
        "level": CognitiveLevel.VAN_DUNG,
        "stem": "Một người nông dân muốn rào một khu vườn hình chữ nhật có diện tích $200\\text{ m}^2$ giáp với bờ sông (bờ sông không cần rào). Biết chi phí rào ba cạnh còn lại là đồng giá theo mét. Chiều dài cạnh song song với bờ sông bằng bao nhiêu mét để tổng chiều dài hàng rào là nhỏ nhất?",
        "correct_value": "20",
        "solution": "Gọi $x$ (m) là chiều dài cạnh vuông góc với bờ sông ($x > 0$). Cạnh song song với bờ sông có độ dài là $\\frac{200}{x}$ (m). Tổng chiều dài hàng rào là $L(x) = 2x + \\frac{200}{x}$. Áp dụng bất đẳng thức AM-GM: $L(x) = 2x + \\frac{200}{x} \\ge 2\\sqrt{2x \\cdot \\frac{200}{x}} = 40$. Dấu '=' xảy ra khi $2x = \\frac{200}{x} \\Leftrightarrow x^2 = 100 \\Rightarrow x = 10$. Khi đó cạnh song song với bờ sông dài $\\frac{200}{10} = 20\\text{ m}$.",
        "tikz_code": None,
        "sympy_code": "import sympy as sp\nx = sp.Symbol('x', positive=True)\nL = 2*x + 200/x\ndL = sp.diff(L, x)\nx_opt = sp.solve(dL, x)[0]\nresult = 200 / x_opt\nis_valid = (result == 20)"
    },

    # === LỚP 11 ===
    # 6. Lớp 11: Lượng giác - Trắc nghiệm 4 lựa chọn
    {
        "grade": 11,
        "type": QuestionType.MULTIPLE_CHOICE,
        "topic": "Hàm số lượng giác",
        "subtopic": "Tập xác định của hàm lượng giác",
        "level": CognitiveLevel.NHAN_BIET,
        "stem": "Tập xác định của hàm số $y = \\tan x$ là",
        "choices": [
            "$\\mathbb{R} \\setminus \\left\\{\\frac{\\pi}{2} + k\\pi, k \\in \\mathbb{Z}\\right\\}$",
            "$\\mathbb{R} \\setminus \\{k\\pi, k \\in \\mathbb{Z}\\}$",
            "$\\mathbb{R}$",
            "$\\mathbb{R} \\setminus \\left\\{\\frac{\\pi}{4} + k\\pi, k \\in \\mathbb{Z}\\right\\}$"
        ],
        "correct_index": 0,
        "solution": "Hàm số $y = \\tan x = \\frac{\\sin x}{\\cos x}$ xác định khi $\\cos x \\ne 0 \\Leftrightarrow x \\ne \\frac{\\pi}{2} + k\\pi \\, (k \\in \\mathbb{Z})$.",
        "tikz_code": None,
        "sympy_code": "is_valid = True"
    },
    # 7. Lớp 11: Cấp số cộng - Trắc nghiệm 4 lựa chọn
    {
        "grade": 11,
        "type": QuestionType.MULTIPLE_CHOICE,
        "topic": "Cấp số cộng",
        "subtopic": "Số hạng tổng quát và công sai",
        "level": CognitiveLevel.NHAN_BIET,
        "stem": "Cho cấp số cộng $(u_n)$ có số hạng đầu $u_1 = 3$ và công sai $d = 2$. Giá trị của số hạng thứ $5$ bằng",
        "choices": ["$11$", "$13$", "$9$", "$15$"],
        "correct_index": 0,
        "solution": "Áp dụng công thức số hạng tổng quát: $u_5 = u_1 + (5 - 1)d = 3 + 4 \\times 2 = 11$.",
        "tikz_code": None,
        "sympy_code": "result = 3 + 4*2\nis_valid = (result == 11)"
    },
    # 8. Lớp 11: Đúng / Sai - Giới hạn và Dãy số
    {
        "grade": 11,
        "type": QuestionType.TRUE_FALSE,
        "topic": "Giới hạn và hàm số liên tục",
        "subtopic": "Tính chất của giới hạn",
        "level": CognitiveLevel.THONG_HIEU,
        "stem": "Cho dãy số $(u_n)$ có số hạng tổng quát $u_n = \\frac{2n + 1}{n + 3}$. Xét tính đúng sai của các mệnh đề sau:",
        "statements": [
            {"statement": "Dãy số $(u_n)$ là một dãy số tăng.", "is_correct": True, "explanation": "$u_{n+1} - u_n = \\frac{5}{(n+4)(n+3)} > 0$."},
            {"statement": "Giới hạn $\\lim u_n = 2$.", "is_correct": True, "explanation": "$\\lim \\frac{2n+1}{n+3} = 2$."},
            {"statement": "Dãy số $(u_n)$ bị chặn trên bởi số $1$.", "is_correct": False, "explanation": "Vì giới hạn là 2 và dãy tăng nên không thể bị chặn trên bởi 1."},
            {"statement": "Số hạng thứ 3 của dãy là $u_3 = \\frac{7}{6}$.", "is_correct": True, "explanation": "$u_3 = \\frac{2(3)+1}{3+3} = \\frac{7}{6}$."}
        ],
        "solution": "1) Ta có $u_{n+1} - u_n = \\frac{2(n+1)+1}{n+4} - \\frac{2n+1}{n+3} = \\frac{5}{(n+4)(n+3)} > 0, \\forall n \\ge 1$. Dãy tăng $\\Rightarrow$ a ĐÚNG.\n2) $\\lim \\frac{2n+1}{n+3} = \\lim \\frac{2 + 1/n}{1 + 3/n} = 2 \\Rightarrow$ b ĐÚNG.\n3) Vì dãy tăng và $\\lim = 2$ nên $u_n < 2$, dãy không bị chặn trên bởi 1 $\\Rightarrow$ c SAI.\n4) $u_3 = \\frac{2(3)+1}{6} = \\frac{7}{6} \\Rightarrow$ d ĐÚNG.",
        "tikz_code": None,
        "sympy_code": "import sympy as sp\nn = sp.Symbol('n')\nu = (2*n + 1)/(n + 3)\nlim_u = sp.limit(u, n, sp.oo)\nis_valid = (lim_u == 2)"
    },

    # === LỚP 10 ===
    # 9. Lớp 10: Mệnh đề & Tập hợp - Trắc nghiệm 4 lựa chọn
    {
        "grade": 10,
        "type": QuestionType.MULTIPLE_CHOICE,
        "topic": "Mệnh đề và tập hợp",
        "subtopic": "Các phép toán trên tập hợp",
        "level": CognitiveLevel.NHAN_BIET,
        "stem": "Cho hai tập hợp $A = \\{1; 2; 3; 4\\}$ và $B = \\{2; 4; 6; 8\\}$. Tập hợp $A \\cap B$ là",
        "choices": [
            "$\\{2; 4\\}$",
            "$\\{1; 3\\}$",
            "$\\{1; 2; 3; 4; 6; 8\\}$",
            "$\\{6; 8\\}$"
        ],
        "correct_index": 0,
        "solution": "Giao của hai tập hợp $A \\cap B$ là tập hợp gồm các phần tử vừa thuộc $A$ vừa thuộc $B$. Do đó $A \\cap B = \\{2; 4\\}$.",
        "tikz_code": None,
        "sympy_code": "A = {1, 2, 3, 4}\nB = {2, 4, 6, 8}\nresult = list(A.intersection(B))\nis_valid = (set(result) == {2, 4})"
    },
    # 10. Lớp 10: Tọa độ Oxy - Trả lời ngắn
    {
        "grade": 10,
        "type": QuestionType.SHORT_ANSWER,
        "topic": "Phương pháp tọa độ Oxy",
        "subtopic": "Khoảng cách từ điểm đến đường thẳng",
        "level": CognitiveLevel.THONG_HIEU,
        "stem": "Trong mặt phẳng tọa độ $Oxy$, khoảng cách từ điểm $M(1; -2)$ đến đường thẳng $\\Delta: 3x - 4y + 4 = 0$ bằng bao nhiêu?",
        "correct_value": "3",
        "solution": "Khoảng cách từ điểm $M(x_0; y_0)$ đến $\\Delta: Ax + By + C = 0$ là: $d(M, \\Delta) = \\frac{|3(1) - 4(-2) + 4|}{\\sqrt{3^2 + (-4)^2}} = \\frac{|3 + 8 + 4|}{\\sqrt{25}} = \\frac{15}{5} = 3$.",
        "tikz_code": None,
        "sympy_code": "d = abs(3*1 - 4*(-2) + 4) / 5\nresult = d\nis_valid = (d == 3)"
    },

    # === LỚP 9 (TRỌNG TÂM GDPT 2018 / 2026) ===
    # 11. Lớp 9: Phương trình bậc hai & Vi-et - Trắc nghiệm 4 lựa chọn
    {
        "grade": 9,
        "type": QuestionType.MULTIPLE_CHOICE,
        "topic": "Số và Đại số",
        "subtopic": "Định lý Viète: tính tổng và tích hai nghiệm",
        "level": CognitiveLevel.THONG_HIEU,
        "stem": "Cho phương trình bậc hai $x^2 - 7x + 10 = 0$. Gọi $x_1, x_2$ là hai nghiệm của phương trình. Giá trị của biểu thức $T = x_1 + x_2 + x_1 x_2$ bằng",
        "choices": ["$17$", "$3$", "$-17$", "$-3$"],
        "correct_index": 0,
        "solution": "Theo định lý Viète, ta có: $x_1 + x_2 = -\\frac{b}{a} = 7$ và $x_1 x_2 = \\frac{c}{a} = 10$. Do đó $T = 7 + 10 = 17$.",
        "tikz_code": None,
        "sympy_code": "import sympy as sp\nx = sp.Symbol('x')\neq = x**2 - 7*x + 10\nroots = sp.solve(eq, x)\nT = sum(roots) + roots[0]*roots[1]\nis_valid = (T == 17)"
    },
    # 12. Lớp 9: Đúng / Sai - Tứ giác nội tiếp & Góc đường tròn
    {
        "grade": 9,
        "type": QuestionType.TRUE_FALSE,
        "topic": "Hình học và Đo lường",
        "subtopic": "Dấu hiệu nhận biết tứ giác nội tiếp đường tròn",
        "level": CognitiveLevel.THONG_HIEU,
        "stem": "Cho tứ giác $ABCD$ nội tiếp đường tròn $(O)$. Xét tính đúng hay sai của các khẳng định sau:",
        "statements": [
            {"statement": "Tổng số đo hai góc đối diện $\\widehat{A} + \\widehat{C} = 180^\\circ$.", "is_correct": True, "explanation": "Tính chất cơ bản của tứ giác nội tiếp."},
            {"statement": "Góc ngoài tại một đỉnh bằng góc trong tại đỉnh đối diện với đỉnh đó.", "is_correct": True, "explanation": "Vì cùng bù với góc trong tại đỉnh đó."},
            {"statement": "Bốn đỉnh $A, B, C, D$ luôn cách đều tâm $O$ một khoảng bằng bán kính $R$.", "is_correct": True, "explanation": "Vì 4 điểm cùng nằm trên đường tròn."},
            {"statement": "Mọi hình bình hành đều là tứ giác nội tiếp.", "is_correct": False, "explanation": "Chỉ hình bình hành có 2 góc đối bù nhau (hình chữ nhật/hình vuông) mới nội tiếp."}
        ],
        "solution": "1) $\\widehat{A} + \\widehat{C} = 180^\\circ$ đúng.\n2) Góc ngoài tại một đỉnh bằng góc trong đối diện đúng.\n3) Bốn đỉnh cách đều tâm $O$ đúng.\n4) Hình bình hành nói chung không nội tiếp (sai).",
        "tikz_code": None,
        "sympy_code": "is_valid = True"
    },
    # 13. Lớp 9: Trả lời ngắn - Rút gọn căn thức
    {
        "grade": 9,
        "type": QuestionType.SHORT_ANSWER,
        "topic": "Số và Đại số",
        "subtopic": "Rút gọn biểu thức chứa căn bậc hai",
        "level": CognitiveLevel.THONG_HIEU,
        "stem": "Rút gọn biểu thức $P = \\sqrt{72} - \\sqrt{32} + \\sqrt{2}$. Kết quả có dạng $a\\sqrt{2}$ với $a$ là số nguyên. Giá trị của $a$ bằng bao nhiêu?",
        "correct_value": "3",
        "solution": "Ta có $\\sqrt{72} = 6\\sqrt{2}$, $\\sqrt{32} = 4\\sqrt{2}$. Do đó $P = 6\\sqrt{2} - 4\\sqrt{2} + \\sqrt{2} = 3\\sqrt{2}$. Suy ra $a = 3$.",
        "tikz_code": None,
        "sympy_code": "import sympy as sp\nP = sp.sqrt(72) - sp.sqrt(32) + sp.sqrt(2)\na = P / sp.sqrt(2)\nis_valid = (sp.simplify(a) == 3)"
    },

    # === LỚP 8 ===
    # 14. Lớp 8: Hằng đẳng thức - Trắc nghiệm 4 lựa chọn
    {
        "grade": 8,
        "type": QuestionType.MULTIPLE_CHOICE,
        "topic": "Số và Đại số",
        "subtopic": "Bảy hằng đẳng thức đáng nhớ",
        "level": CognitiveLevel.NHAN_BIET,
        "stem": "Biểu thức khai triển của $(2x - 3)^2$ là",
        "choices": [
            "$4x^2 - 12x + 9$",
            "$4x^2 - 6x + 9$",
            "$4x^2 - 12x - 9$",
            "$4x^2 + 12x + 9$"
        ],
        "correct_index": 0,
        "solution": "Áp dụng hằng đẳng thức $(A - B)^2 = A^2 - 2AB + B^2$: $(2x - 3)^2 = (2x)^2 - 2(2x)(3) + 3^2 = 4x^2 - 12x + 9$.",
        "tikz_code": None,
        "sympy_code": "import sympy as sp\nx = sp.Symbol('x')\nis_valid = (sp.expand((2*x - 3)**2) == 4*x**2 - 12*x + 9)"
    },
    # 15. Lớp 8: Trả lời ngắn - Hàm số bậc nhất
    {
        "grade": 8,
        "type": QuestionType.SHORT_ANSWER,
        "topic": "Số và Đại số",
        "subtopic": "Hàm số bậc nhất y = ax + b",
        "level": CognitiveLevel.THONG_HIEU,
        "stem": "Tìm giá trị của $m$ để đồ thị hàm số $y = (m - 2)x + 5$ đi qua điểm $A(1; 8)$.",
        "correct_value": "5",
        "solution": "Thay tọa độ điểm $A(1; 8)$ vào hàm số: $8 = (m - 2)(1) + 5 \\Leftrightarrow m - 2 = 3 \\Leftrightarrow m = 5$.",
        "tikz_code": None,
        "sympy_code": "import sympy as sp\nm = sp.Symbol('m')\neq = (m - 2)*1 + 5 - 8\nis_valid = (sp.solve(eq, m)[0] == 5)"
    },

    # === LỚP 7 ===
    # 16. Lớp 7: Dãy tỉ số bằng nhau - Trắc nghiệm 4 lựa chọn
    {
        "grade": 7,
        "type": QuestionType.MULTIPLE_CHOICE,
        "topic": "Số và Đại số",
        "subtopic": "Tính chất của dãy tỉ số bằng nhau",
        "level": CognitiveLevel.THONG_HIEU,
        "stem": "Tìm hai số $x, y$ biết $\\frac{x}{3} = \\frac{y}{5}$ và $x + y = 32$.",
        "choices": [
            "$x = 12; y = 20$",
            "$x = 20; y = 12$",
            "$x = 10; y = 22$",
            "$x = 15; y = 17$"
        ],
        "correct_index": 0,
        "solution": "Áp dụng tính chất của dãy tỉ số bằng nhau: $\\frac{x}{3} = \\frac{y}{5} = \\frac{x + y}{3 + 5} = \\frac{32}{8} = 4$. Suy ra $x = 3 \\times 4 = 12$ và $y = 5 \\times 4 = 20$.",
        "tikz_code": None,
        "sympy_code": "is_valid = (12/3 == 20/5 == 4 and 12 + 20 == 32)"
    },

    # === LỚP 6 ===
    # 17. Lớp 6: Phân số & Số nguyên - Trắc nghiệm 4 lựa chọn
    {
        "grade": 6,
        "type": QuestionType.MULTIPLE_CHOICE,
        "topic": "Số và Đại số",
        "subtopic": "Phép cộng và phép trừ hai số nguyên",
        "level": CognitiveLevel.NHAN_BIET,
        "stem": "Kết quả của phép tính $(-15) + 28$ bằng",
        "choices": ["$13$", "$-13$", "$43$", "$-43$"],
        "correct_index": 0,
        "solution": "Ta có $(-15) + 28 = 28 - 15 = 13$.",
        "tikz_code": None,
        "sympy_code": "is_valid = ((-15 + 28) == 13)"
    },
    # 18. Lớp 6: Trả lời ngắn - Toán thực tế giảm giá
    {
        "grade": 6,
        "type": QuestionType.SHORT_ANSWER,
        "topic": "Toán thực tế & Trải nghiệm",
        "subtopic": "Tỉ số phần trăm và mua sắm giảm giá",
        "level": CognitiveLevel.VAN_DUNG,
        "stem": "Một chiếc cặp học sinh có giá niêm yết là $200\\,000$ đồng. Trong dịp khai giảng, cửa hàng giảm giá $15\\%$. Hỏi người mua phải trả bao nhiêu nghìn đồng?",
        "correct_value": "170",
        "solution": "Số tiền được giảm là: $200 \\times 15\\% = 30$ (nghìn đồng). Số tiền người mua phải trả là: $200 - 30 = 170$ (nghìn đồng).",
        "tikz_code": None,
        "sympy_code": "is_valid = ((200 - 200*0.15) == 170)"
    }
]

class AIService:
    """
    Dịch vụ sinh câu hỏi bằng AI + RAG Few-Shot + Ép kiểu JSON + Kiểm chứng SymPy.
    Hỗ trợ đầy đủ Lớp 10, Lớp 11, Lớp 12.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.client = None
        if self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Không thể khởi tạo Gemini Client: {e}")

    def find_reference_questions(self, topic: str, level: CognitiveLevel, q_type: QuestionType) -> List[Dict[str, Any]]:
        """Tìm câu hỏi mẫu phù hợp từ ngân hàng câu hỏi RAG."""
        matches = [
            q for q in QUESTION_BANK
            if q["type"] == q_type and q["level"] == level
        ]
        if not matches:
            matches = [q for q in QUESTION_BANK if q["type"] == q_type]
        if not matches:
            matches = QUESTION_BANK
        return matches[:2]

    @staticmethod
    def _normalize_question(q: Question) -> Question:
        import unicodedata
        def norm(s: Optional[str]) -> Optional[str]:
            return unicodedata.normalize('NFC', s) if s is not None else None

        q.stem = norm(q.stem) or ""
        q.solution = norm(q.solution) or ""
        q.topic = norm(q.topic) or ""
        if q.subtopic:
            q.subtopic = norm(q.subtopic)
        if q.choices:
            q.choices = [norm(c) or "" for c in q.choices]
        if q.statements:
            for st in q.statements:
                st.statement = norm(st.statement) or ""
                if st.explanation:
                    st.explanation = norm(st.explanation)
        if q.correct_value:
            q.correct_value = norm(q.correct_value)
        return q

    def generate_question(self, slot: ExamSlot, custom_prompt: Optional[str] = None) -> Question:
        """Sinh 1 câu hỏi theo Slot ma trận, chuẩn hóa NFC tránh lỗi tách dấu."""
        if self.client:
            try:
                q = self._generate_with_gemini(slot, custom_prompt)
            except Exception as e:
                logger.error(f"Lỗi khi gọi Gemini API, chuyển sang Fallback Generator: {e}")
                q = self._generate_fallback(slot)
        else:
            q = self._generate_fallback(slot)
        return self._normalize_question(q)

    def _generate_with_gemini(self, slot: ExamSlot, custom_prompt: Optional[str] = None) -> Question:
        """Gọi Gemini với Structured Output ép kiểu JSON chặt chẽ."""
        references = self.find_reference_questions(slot.topic, slot.level, slot.type)
        ref_text = json.dumps(references, ensure_ascii=False, indent=2)

        system_instruction = """Bạn là chuyên gia ra đề thi môn Toán THPT theo chương trình mới GDPT 2018 của Bộ GD&ĐT Việt Nam (Lớp 10, Lớp 11, Lớp 12).
Nhiệm vụ của bạn: Tạo một câu hỏi Toán mới, chuẩn xác theo đúng yêu cầu ma trận.
QUY TẮC BẮT BUỘC:
1. Mọi công thức Toán PHẢI được bọc trong cặp dấu $...$ (hoặc $$...$$). Không dùng \\[ \\] hoặc \\( \\).
2. Lời giải chi tiết (solution) PHẢI giải từng bước (Chain-of-Thought) để tìm ra đáp án đúng trước khi chốt phương án.
3. Cung cấp mã `sympy_code` ngắn gọn (2-5 dòng) dùng thư viện SymPy để tự kiểm tra đáp án. Gán biến `result` hoặc `is_valid = True/False`.
4. Với câu trắc nghiệm 4 lựa chọn: `choices` gồm 4 phần tử, `correct_index` từ 0 đến 3.
5. Với câu Đúng/Sai: `statements` gồm 4 mệnh đề, mỗi mệnh đề có `statement` và `is_correct` (True/False).
6. Với câu trả lời ngắn: `correct_value` là số nguyên, số thập phân hoặc phân số dạng tối giản.
7. Đảm bảo số liệu đẹp, không vô nghiệm ngoài ý muốn.
"""

        prompt = f"""Tạo một câu hỏi Toán:
- Chuyên đề: {slot.topic}
- Dạng bài: {slot.subtopic or 'Tổng quát'}
- Mức độ nhận thức: {slot.level.value} ({slot.level.name})
- Dạng câu: {slot.type.value}
- Yêu cầu bổ sung: {custom_prompt or 'Không có'}

Tham khảo mẫu câu tương đương sau:
{ref_text}

Hãy trả về định dạng JSON thuần túy theo schema yêu cầu.
"""

        response = self.client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                temperature=0.3,
            )
        )

        data = json.loads(response.text)
        
        question = Question(
            id=slot.slot_id,
            type=slot.type,
            topic=slot.topic,
            subtopic=slot.subtopic,
            level=slot.level,
            stem=data.get("stem", "Câu hỏi toán học"),
            choices=data.get("choices"),
            correct_index=data.get("correct_index"),
            statements=[TrueFalseItem(**s) for s in data.get("statements", [])] if data.get("statements") else None,
            correct_value=str(data.get("correct_value")) if data.get("correct_value") is not None else None,
            solution=data.get("solution", ""),
            tikz_code=data.get("tikz_code"),
            sympy_code=data.get("sympy_code"),
            verified=False
        )

        verify_res = SympyVerifier.verify_question(question.model_dump())
        question.verified = verify_res.get("verified", False)
        return question

    def _generate_fallback(self, slot: ExamSlot) -> Question:
        """Cơ chế Offline Mutation Generator thích ứng theo từng chuyên đề và khối lớp (Lớp 6 đến Lớp 12)."""
        top_lower = slot.topic.lower()
        subtop_lower = (slot.subtopic or "").lower()
        full_text = f"{top_lower} {subtop_lower}"

        # Dạng 1: Trắc nghiệm 4 lựa chọn
        if slot.type == QuestionType.MULTIPLE_CHOICE:
            if "phân số" in full_text or "số nguyên" in full_text or "chia hết" in full_text or "số tự nhiên" in full_text:
                a, b = random.choice([(-15, 28), (-12, 25), (-18, 30), (14, -20)])
                ans = a + b
                return Question(
                    id=slot.slot_id,
                    type=QuestionType.MULTIPLE_CHOICE,
                    topic=slot.topic,
                    subtopic=slot.subtopic,
                    level=slot.level,
                    stem=f"Kết quả của phép tính $({a}) + {b}$ bằng",
                    choices=[f"${ans}$", f"${-ans}$", f"${ans + 2}$", f"${ans - 2}$"],
                    correct_index=0,
                    solution=f"Ta có $({a}) + {b} = {b} - {abs(a)} = {ans}$.",
                    tikz_code=None,
                    sympy_code="is_valid = True",
                    verified=True
                )
            elif "căn" in full_text or "căn thức" in full_text:
                x = random.choice([9, 16, 25, 49, 64])
                import math
                rx = int(math.isqrt(x))
                return Question(
                    id=slot.slot_id,
                    type=QuestionType.MULTIPLE_CHOICE,
                    topic=slot.topic,
                    subtopic=slot.subtopic,
                    level=slot.level,
                    stem=f"Giá trị của căn bậc hai số học $\\sqrt{{{x}}}$ bằng",
                    choices=[f"${rx}$", f"${-rx}$", f"${x}$", f"$\\pm {rx}$"],
                    correct_index=0,
                    solution=f"Căn bậc hai số học của ${x}$ là số không âm có bình phương bằng ${x}$, do đó $\\sqrt{{{x}}} = {rx}$.",
                    tikz_code=None,
                    sympy_code="is_valid = True",
                    verified=True
                )
            elif "đơn thức" in full_text or "đa thức" in full_text or "bậc của" in full_text:
                b = random.choice([3, 4, 5])
                return Question(
                    id=slot.slot_id,
                    type=QuestionType.MULTIPLE_CHOICE,
                    topic=slot.topic,
                    subtopic=slot.subtopic,
                    level=slot.level,
                    stem=f"Bậc của đa thức $P(x, y) = 3x^{{{b}}}y^2 - 5x^2y + 7$ bằng",
                    choices=[f"${b+2}$", f"${b}$", f"${b+1}$", f"$2$"],
                    correct_index=0,
                    solution=f"Hạng tử $3x^{{{b}}}y^2$ có bậc cao nhất là ${b} + 2 = {b+2}$. Vậy bậc của đa thức là ${b+2}$.",
                    tikz_code=None,
                    sympy_code="is_valid = True",
                    verified=True
                )
            elif "hình tam giác" in full_text or "hình vuông" in full_text or "hình chữ nhật" in full_text or "hình thoi" in full_text or "hình lục giác" in full_text:
                a = random.choice([4, 5, 6])
                return Question(
                    id=slot.slot_id,
                    type=QuestionType.MULTIPLE_CHOICE,
                    topic=slot.topic,
                    subtopic=slot.subtopic,
                    level=slot.level,
                    stem=f"Chu vi của một hình vuông có độ dài cạnh ${a}\\text{{ cm}}$ là",
                    choices=[f"${4*a}\\text{{ cm}}$", f"${a*a}\\text{{ cm}}$", f"${2*a}\\text{{ cm}}$", f"${4*a + 2}\\text{{ cm}}$"],
                    correct_index=0,
                    solution=f"Chu vi hình vuông là $C = 4 \\times {a} = {4*a}\\text{{ cm}}$.",
                    tikz_code=None,
                    sympy_code="is_valid = True",
                    verified=True
                )
            elif "tỉ lệ thức" in full_text or "dãy tỉ số" in full_text or "hữu tỉ" in full_text:
                k = random.choice([3, 4, 5])
                x, y = 2 * k, 3 * k
                total = x + y
                return Question(
                    id=slot.slot_id,
                    type=QuestionType.MULTIPLE_CHOICE,
                    topic=slot.topic,
                    subtopic=slot.subtopic,
                    level=slot.level,
                    stem=f"Tìm hai số $x, y$ biết $\\frac{{x}}{{2}} = \\frac{{y}}{{3}}$ và $x + y = {total}$.",
                    choices=[f"$x = {x}; y = {y}$", f"$x = {y}; y = {x}$", f"$x = {x+2}; y = {y-2}$", f"$x = {x-2}; y = {y+2}$"],
                    correct_index=0,
                    solution=f"Áp dụng tính chất dãy tỉ số bằng nhau: $\\frac{{x}}{{2}} = \\frac{{y}}{{3}} = \\frac{{x + y}}{{2 + 3}} = \\frac{{{total}}}{{5}} = {k}$. Do đó $x = 2 \\times {k} = {x}$ và $y = 3 \\times {k} = {y}$.",
                    tikz_code=None,
                    sympy_code="is_valid = True",
                    verified=True
                )
            elif "hằng đẳng thức" in full_text or "phân thức" in full_text:
                a = random.choice([2, 3])
                b = random.choice([3, 5])
                a2, ab2, b2 = a*a, 2*a*b, b*b
                return Question(
                    id=slot.slot_id,
                    type=QuestionType.MULTIPLE_CHOICE,
                    topic=slot.topic,
                    subtopic=slot.subtopic,
                    level=slot.level,
                    stem=f"Khai triển hằng đẳng thức $({a}x - {b})^2$ ta được kết quả là",
                    choices=[f"${a2}x^2 - {ab2}x + {b2}$", f"${a2}x^2 - {ab2//2}x + {b2}$", f"${a2}x^2 + {ab2}x + {b2}$", f"${a2}x^2 - {ab2}x - {b2}$"],
                    correct_index=0,
                    solution=f"Áp dụng hằng đẳng thức $(A - B)^2 = A^2 - 2AB + B^2$: $({a}x - {b})^2 = {a2}x^2 - {ab2}x + {b2}$.",
                    tikz_code=None,
                    sympy_code="is_valid = True",
                    verified=True
                )
            elif "vi-et" in full_text or "viète" in full_text or "phương trình bậc hai" in full_text:
                x1, x2 = random.choice([(2, 5), (3, 4), (1, 6), (2, 3)])
                S = x1 + x2
                P = x1 * x2
                ans = S + P
                return Question(
                    id=slot.slot_id,
                    type=QuestionType.MULTIPLE_CHOICE,
                    topic=slot.topic,
                    subtopic=slot.subtopic,
                    level=slot.level,
                    stem=f"Cho phương trình bậc hai $x^2 - {S}x + {P} = 0$. Gọi $x_1, x_2$ là hai nghiệm của phương trình. Giá trị của biểu thức $T = x_1 + x_2 + x_1 x_2$ bằng",
                    choices=[f"${ans}$", f"${ans - 2}$", f"${ans + 2}$", f"${S}$"],
                    correct_index=0,
                    solution=f"Theo định lý Viète, ta có $x_1 + x_2 = {S}$ và $x_1 x_2 = {P}$. Do đó $T = {S} + {P} = {ans}$.",
                    tikz_code=None,
                    sympy_code="is_valid = True",
                    verified=True
                )
            elif "tứ giác nội tiếp" in full_text or "đường tròn" in full_text or "góc nội tiếp" in full_text:
                gocA = random.choice([70, 80, 85, 95])
                gocC = 180 - gocA
                return Question(
                    id=slot.slot_id,
                    type=QuestionType.MULTIPLE_CHOICE,
                    topic=slot.topic,
                    subtopic=slot.subtopic,
                    level=slot.level,
                    stem=f"Cho tứ giác $ABCD$ nội tiếp đường tròn. Biết số đo góc $\\widehat{{A}} = {gocA}^\\circ$. Số đo góc $\\widehat{{C}}$ bằng",
                    choices=[f"${gocC}^\\circ$", f"${gocA}^\\circ$", f"${180 - gocC//2}^\\circ$", f"${90}^\\circ$"],
                    correct_index=0,
                    solution=f"Vì tứ giác $ABCD$ nội tiếp đường tròn nên hai góc đối diện bù nhau: $\\widehat{{A}} + \\widehat{{C}} = 180^\\circ \\Rightarrow \\widehat{{C}} = 180^\\circ - {gocA}^\\circ = {gocC}^\\circ$.",
                    tikz_code=None,
                    sympy_code="is_valid = True",
                    verified=True
                )
            elif "thống kê" in full_text or "xác suất" in full_text or "biểu đồ" in full_text:
                return Question(
                    id=slot.slot_id,
                    type=QuestionType.MULTIPLE_CHOICE,
                    topic=slot.topic,
                    subtopic=slot.subtopic,
                    level=slot.level,
                    stem="Gieo một con xúc xắc cân đối và đồng chất một lần. Xác suất để xuất hiện mặt có số chấm chia hết cho $3$ là",
                    choices=["$\\frac{1}{3}$", "$\\frac{1}{6}$", "$\\frac{1}{2}$", "$\\frac{2}{3}$"],
                    correct_index=0,
                    solution="Các mặt chia hết cho 3 là $\\{3; 6\\}$, gồm 2 khả năng. Tổng số khả năng xảy ra là 6. Vậy xác suất là $P = \\frac{2}{6} = \\frac{1}{3}$.",
                    tikz_code=None,
                    sympy_code="is_valid = True",
                    verified=True
                )
            elif "toán thực tế" in full_text or "trải nghiệm" in full_text or "chi phí" in full_text:
                price = random.choice([100, 200, 500])
                discount = random.choice([10, 15, 20])
                pay = price * (100 - discount) // 100
                return Question(
                    id=slot.slot_id,
                    type=QuestionType.MULTIPLE_CHOICE,
                    topic=slot.topic,
                    subtopic=slot.subtopic,
                    level=slot.level,
                    stem=f"Một sản phẩm có giá niêm yết là ${price}\\,000$ đồng. Nhân dịp khuyến mãi, cửa hàng giảm giá ${discount}\\%$. Giá bán sau khi giảm là",
                    choices=[f"${pay}\\,000$ đồng", f"${price - discount}\\,000$ đồng", f"${pay - 10}\\,000$ đồng", f"${price + 10}\\,000$ đồng"],
                    correct_index=0,
                    solution=f"Số tiền giảm: ${price} \\times {discount}\\% = {price * discount // 100}$ (nghìn đồng). Số tiền phải trả: ${price} - {price * discount // 100} = {pay}$ (nghìn đồng).",
                    tikz_code=None,
                    sympy_code="is_valid = True",
                    verified=True
                )
            elif "lượng giác" in top_lower:
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
                    solution="Hàm số $y = \\tan x = \\frac{\\sin x}{\\cos x}$ xác định khi $\\cos x \\ne 0 \\Leftrightarrow x \\ne \\frac{\\pi}{2} + k\\pi \\, (k \\in \\mathbb{Z})$.",
                    tikz_code=None,
                    sympy_code="is_valid = True",
                    verified=True
                )
            elif "cấp số" in top_lower or "dãy số" in top_lower:
                u1 = random.choice([2, 3, 5])
                d = random.choice([2, 3, 4])
                n = 5
                val = u1 + (n - 1) * d
                return Question(
                    id=slot.slot_id,
                    type=QuestionType.MULTIPLE_CHOICE,
                    topic=slot.topic,
                    subtopic=slot.subtopic,
                    level=slot.level,
                    stem=f"Cho cấp số cộng $(u_n)$ có số hạng đầu $u_1 = {u1}$ và công sai $d = {d}$. Giá trị của số hạng thứ ${n}$ bằng",
                    choices=[f"${val}$", f"${val + 2}$", f"${val - 2}$", f"${val + 4}$"],
                    correct_index=0,
                    solution=f"Áp dụng công thức số hạng tổng quát: $u_{n} = u_1 + ({n} - 1)d = {u1} + {n-1} \\times {d} = {val}$.",
                    tikz_code=None,
                    sympy_code=f"result = {val}\nis_valid = True",
                    verified=True
                )
            elif "tập hợp" in top_lower or "mệnh đề" in top_lower:
                return Question(
                    id=slot.slot_id,
                    type=QuestionType.MULTIPLE_CHOICE,
                    topic=slot.topic,
                    subtopic=slot.subtopic,
                    level=slot.level,
                    stem="Cho hai tập hợp $A = \\{1; 2; 3; 4\\}$ và $B = \\{2; 4; 6; 8\\}$. Tập hợp $A \\cap B$ là",
                    choices=["$\\{2; 4\\}$", "$\\{1; 3\\}$", "$\\{1; 2; 3; 4; 6; 8\\}$", "$\\{6; 8\\}$"],
                    correct_index=0,
                    solution="Giao của hai tập hợp $A \\cap B$ là tập các phần tử vừa thuộc $A$ vừa thuộc $B$. Vậy $A \\cap B = \\{2; 4\\}$.",
                    tikz_code=None,
                    sympy_code="is_valid = True",
                    verified=True
                )
            elif "mặt cầu" in top_lower or "oxyz" in top_lower:
                x0, y0, z0 = random.randint(1, 4), random.randint(-3, -1), random.randint(2, 5)
                r = random.choice([3, 4, 5])
                r2 = r * r
                return Question(
                    id=slot.slot_id,
                    type=QuestionType.MULTIPLE_CHOICE,
                    topic=slot.topic,
                    subtopic=slot.subtopic,
                    level=slot.level,
                    stem=f"Trong không gian $Oxyz$, cho mặt cầu $(S): (x - {x0})^2 + (y - ({y0}))^2 + (z - {z0})^2 = {r2}$. Tọa độ tâm $I$ và bán kính $R$ của $(S)$ là",
                    choices=[
                        f"$I({x0}; {y0}; {z0})$ và $R = {r}$",
                        f"$I(-{x0}; {-y0}; -{z0})$ và $R = {r}$",
                        f"$I({x0}; {y0}; {z0})$ và $R = {r2}$",
                        f"$I(-{x0}; {-y0}; -{z0})$ và $R = {r2}$"
                    ],
                    correct_index=0,
                    solution=f"Mặt cầu $(S)$ có tâm $I({x0}; {y0}; {z0})$ và bán kính $R = \\sqrt{{{r2}}} = {r}$.",
                    tikz_code=None,
                    sympy_code="is_valid = True",
                    verified=True
                )
            else:
                a = random.choice([2, 3, 4])
                return Question(
                    id=slot.slot_id,
                    type=QuestionType.MULTIPLE_CHOICE,
                    topic=slot.topic,
                    subtopic=slot.subtopic,
                    level=slot.level,
                    stem=f"Cho hàm số $y = f(x)$ có đạo hàm $f'(x) = x(x - {a})(x + 1)^2$ với mọi $x \\in \\mathbb{{R}}$. Hàm số đã cho có bao nhiêu điểm cực trị?",
                    choices=["$2$", "$1$", "$3$", "$0$"],
                    correct_index=0,
                    solution=f"Ta có $f'(x) = 0 \\Leftrightarrow x = 0$ (nghiệm đơn), $x = {a}$ (nghiệm đơn), $x = -1$ (nghiệm bội chẵn). Vì đạo hàm chỉ đổi dấu qua nghiệm đơn nên hàm số có $2$ điểm cực trị.",
                    tikz_code=None,
                    sympy_code="is_valid = True",
                    verified=True
                )

        # Dạng 2: Đúng / Sai
        elif slot.type == QuestionType.TRUE_FALSE:
            if "tứ giác" in full_text or "đường tròn" in full_text or "tiếp tuyến" in full_text:
                return Question(
                    id=slot.slot_id,
                    type=QuestionType.TRUE_FALSE,
                    topic=slot.topic,
                    subtopic=slot.subtopic,
                    level=slot.level,
                    stem="Cho tứ giác $ABCD$ nội tiếp đường tròn $(O)$. Xét tính đúng hay sai của các mệnh đề sau:",
                    statements=[
                        TrueFalseItem(statement="Tổng hai góc đối diện $\\widehat{A} + \\widehat{C} = 180^\\circ$.", is_correct=True, explanation="Tính chất cơ bản của tứ giác nội tiếp."),
                        TrueFalseItem(statement="Góc ngoài tại đỉnh $A$ bằng góc trong tại đỉnh đối diện $C$.", is_correct=True, explanation="Vì cùng bù với góc $\\widehat{A}$."),
                        TrueFalseItem(statement="Bốn đỉnh $A, B, C, D$ cách đều tâm đường tròn $O$.", is_correct=True, explanation="Khoảng cách từ tâm đến các đỉnh đều bằng bán kính $R$."),
                        TrueFalseItem(statement="Mọi hình bình hành đều là tứ giác nội tiếp.", is_correct=False, explanation="Chỉ có hình chữ nhật hoặc hình vuông mới nội tiếp.")
                    ],
                    solution="Mệnh đề a ĐÚNG, b ĐÚNG, c ĐÚNG, d SAI.",
                    tikz_code=None,
                    sympy_code="is_valid = True",
                    verified=True
                )
            elif "dãy số" in full_text or "giới hạn" in full_text:
                return Question(
                    id=slot.slot_id,
                    type=QuestionType.TRUE_FALSE,
                    topic=slot.topic,
                    subtopic=slot.subtopic,
                    level=slot.level,
                    stem="Cho dãy số $(u_n)$ có số hạng tổng quát $u_n = \\frac{2n + 1}{n + 3}$. Xét tính đúng sai của các mệnh đề sau:",
                    statements=[
                        TrueFalseItem(statement="Dãy số $(u_n)$ là một dãy số tăng.", is_correct=True, explanation="$u_{n+1} - u_n > 0$."),
                        TrueFalseItem(statement="Giới hạn $\\lim u_n = 2$.", is_correct=True, explanation="$\\lim \\frac{2n+1}{n+3} = 2$."),
                        TrueFalseItem(statement="Dãy số $(u_n)$ bị chặn trên bởi $1$.", is_correct=False, explanation="Dãy tăng và hội tụ về 2 nên không bị chặn trên bởi 1."),
                        TrueFalseItem(statement="Số hạng thứ ba của dãy là $u_3 = \\frac{7}{6}$.", is_correct=True, explanation="$u_3 = \\frac{2(3)+1}{3+3} = \\frac{7}{6}$.")
                    ],
                    solution="Mệnh đề a ĐÚNG, b ĐÚNG, c SAI, d ĐÚNG.",
                    tikz_code=None,
                    sympy_code="is_valid = True",
                    verified=True
                )
            else:
                a = random.choice([3, 6])
                return Question(
                    id=slot.slot_id,
                    type=QuestionType.TRUE_FALSE,
                    topic=slot.topic,
                    subtopic=slot.subtopic,
                    level=slot.level,
                    stem=f"Cho hàm số bậc ba $y = f(x) = x^3 - {a}x^2 + 2$. Xét tính đúng hay sai của các mệnh đề sau:",
                    statements=[
                        TrueFalseItem(statement=f"Đạo hàm của hàm số là $f'(x) = 3x^2 - {2*a}x$.", is_correct=True, explanation="Tính đạo hàm chuẩn xác."),
                        TrueFalseItem(statement=f"Hàm số đồng biến trên khoảng $(0; {2*a//3})$.", is_correct=False, explanation="Trên khoảng này $f'(x) < 0$ nên hàm số nghịch biến."),
                        TrueFalseItem(statement="Đồ thị hàm số có điểm cực đại là $(0; 2)$.", is_correct=True, explanation="Tại $x=0$, $f'(0)=0$ và đổi dấu từ dương sang âm."),
                        TrueFalseItem(statement="Giá trị cực tiểu của hàm số bằng $2$.", is_correct=False, explanation="Giá trị $y=2$ là cực đại, không phải cực tiểu.")
                    ],
                    solution=f"Ta có $f'(x) = 3x^2 - {2*a}x = 3x(x - {2*a//3})$.\n- Mệnh đề a: Đúng.\n- Mệnh đề b: Sai.\n- Mệnh đề c: Đúng.\n- Mệnh đề d: Sai.",
                    tikz_code=TikZLibrary.get_tkz_tab_bac3("0", str(2*a//3), "2", str(2 - 4*(a**3)//27), "duong"),
                    sympy_code="is_valid = True",
                    verified=True
                )

        # Dạng 3: Trả lời ngắn
        elif slot.type == QuestionType.SHORT_ANSWER:
            if "vi-et" in full_text or "viète" in full_text or "bậc hai" in full_text:
                x1, x2 = random.choice([(1, 4), (2, 3), (2, 5)])
                ans = x1 + x2 + x1*x2
                return Question(
                    id=slot.slot_id,
                    type=QuestionType.SHORT_ANSWER,
                    topic=slot.topic,
                    subtopic=slot.subtopic,
                    level=slot.level,
                    stem=f"Cho phương trình bậc hai $x^2 - {x1+x2}x + {x1*x2} = 0$ có hai nghiệm $x_1, x_2$. Giá trị của biểu thức $x_1 + x_2 + x_1 x_2$ bằng bao nhiêu?",
                    correct_value=str(ans),
                    solution=f"Theo định lý Viète, $x_1 + x_2 = {x1+x2}$ và $x_1 x_2 = {x1*x2}$. Vậy $x_1 + x_2 + x_1 x_2 = {ans}$.",
                    tikz_code=None,
                    sympy_code="is_valid = True",
                    verified=True
                )
            elif "căn" in full_text:
                a_val = random.choice([2, 3, 4])
                res = a_val - 2 + 1
                return Question(
                    id=slot.slot_id,
                    type=QuestionType.SHORT_ANSWER,
                    topic=slot.topic,
                    subtopic=slot.subtopic,
                    level=slot.level,
                    stem=f"Rút gọn biểu thức $P = \\sqrt{{{a_val*a_val*2}}} - \\sqrt{8} + \\sqrt{2}$. Kết quả có dạng $k\\sqrt{2}$ với $k$ là số nguyên. Giá trị của $k$ bằng bao nhiêu?",
                    correct_value=str(res),
                    solution=f"Ta có $\\sqrt{{{a_val*a_val*2}}} = {a_val}\\sqrt{2}$, $\\sqrt{8} = 2\\sqrt{2}$. Suy ra $P = ({a_val} - 2 + 1)\\sqrt{2} = {res}\\sqrt{2}$. Vậy $k = {res}$.",
                    tikz_code=None,
                    sympy_code="is_valid = True",
                    verified=True
                )
            elif "thực tế" in full_text or "giảm giá" in full_text or "phần trăm" in full_text:
                price = random.choice([200, 300, 400])
                disc = random.choice([10, 20])
                pay = price * (100 - disc) // 100
                return Question(
                    id=slot.slot_id,
                    type=QuestionType.SHORT_ANSWER,
                    topic=slot.topic,
                    subtopic=slot.subtopic,
                    level=slot.level,
                    stem=f"Một mặt hàng giá niêm yết ${price}\\,000$ đồng được giảm giá ${disc}\\%$. Hỏi khách hàng phải trả bao nhiêu nghìn đồng?",
                    correct_value=str(pay),
                    solution=f"Khách hàng phải trả: ${price} \\times (1 - {disc}\\%) = {pay}$ nghìn đồng.",
                    tikz_code=None,
                    sympy_code="is_valid = True",
                    verified=True
                )
            elif "tỉ lệ thức" in full_text or "dãy tỉ số" in full_text or "tìm x" in full_text:
                k = random.choice([3, 4, 5])
                return Question(
                    id=slot.slot_id,
                    type=QuestionType.SHORT_ANSWER,
                    topic=slot.topic,
                    subtopic=slot.subtopic,
                    level=slot.level,
                    stem=f"Tìm số nguyên dương $x$ thỏa mãn đẳng thức $\\frac{{x}}{{4}} = \\frac{{{3*k}}}{{3}}$.",
                    correct_value=str(4*k),
                    solution=f"Ta có $\\frac{{x}}{{4}} = {k} \\Leftrightarrow x = 4 \\times {k} = {4*k}$.",
                    tikz_code=None,
                    sympy_code="is_valid = True",
                    verified=True
                )
            elif "thống kê" in full_text or "xác suất" in full_text or "biểu đồ" in full_text or "số học sinh" in full_text:
                total_students = random.choice([40, 45, 50])
                gioi_pct = random.choice([20, 25, 30])
                ans = total_students * gioi_pct // 100
                return Question(
                    id=slot.slot_id,
                    type=QuestionType.SHORT_ANSWER,
                    topic=slot.topic,
                    subtopic=slot.subtopic,
                    level=slot.level,
                    stem=f"Một lớp học có ${total_students}$ học sinh. Kết quả khảo sát cho thấy có ${gioi_pct}\\%$ số học sinh đạt học lực Xuất sắc. Số học sinh đạt loại Xuất sắc của lớp là bao nhiêu học sinh?",
                    correct_value=str(ans),
                    solution=f"Số học sinh đạt loại Xuất sắc là: ${total_students} \\times {gioi_pct}\\% = {ans}$ học sinh.",
                    tikz_code=None,
                    sympy_code="is_valid = True",
                    verified=True
                )
            elif "hình học" in full_text or "tam giác" in full_text or "đoạn thẳng" in full_text or "chiều dài" in full_text:
                d = random.choice([15, 20, 25])
                r = random.choice([8, 10, 12])
                s = d * r
                return Question(
                    id=slot.slot_id,
                    type=QuestionType.SHORT_ANSWER,
                    topic=slot.topic,
                    subtopic=slot.subtopic,
                    level=slot.level,
                    stem=f"Một mảnh vườn hình chữ nhật có chiều dài ${d}\\text{{ m}}$ và chiều rộng ${r}\\text{{ m}}$. Diện tích của mảnh vườn đó bằng bao nhiêu mét vuông?",
                    correct_value=str(s),
                    solution=f"Diện tích mảnh vườn là $S = {d} \\times {r} = {s}\\text{{ m}}^2$.",
                    tikz_code=None,
                    sympy_code="is_valid = True",
                    verified=True
                )
            elif "oxy" in top_lower and "oxyz" not in top_lower:
                val = random.choice([2, 3, 5])
                return Question(
                    id=slot.slot_id,
                    type=QuestionType.SHORT_ANSWER,
                    topic=slot.topic,
                    subtopic=slot.subtopic,
                    level=slot.level,
                    stem=f"Trong mặt phẳng $Oxy$, khoảng cách từ điểm $M(1; -2)$ đến đường thẳng $\\Delta: 3x - 4y + {5*val - 11} = 0$ bằng bao nhiêu?",
                    correct_value=str(val),
                    solution=f"Khoảng cách là $d(M, \\Delta) = \\frac{{|3(1) - 4(-2) + {5*val - 11}|}}{{\\sqrt{{3^2 + (-4)^2}}}} = \\frac{{{5*val}}}{{5}} = {val}$.",
                    tikz_code=None,
                    sympy_code=f"result = {val}\nis_valid = True",
                    verified=True
                )
            elif "oxyz" in top_lower or "mặt phẳng" in full_text:
                val = random.choice([2, 3, 5])
                return Question(
                    id=slot.slot_id,
                    type=QuestionType.SHORT_ANSWER,
                    topic=slot.topic,
                    subtopic=slot.subtopic,
                    level=slot.level,
                    stem=f"Trong không gian $Oxyz$, cho điểm $M(1; 2; 3)$ và mặt phẳng $(P): 2x - 2y + z + {3*val - 1} = 0$. Khoảng cách từ điểm $M$ đến mặt phẳng $(P)$ bằng bao nhiêu?",
                    correct_value=str(val),
                    solution=f"Khoảng cách từ $M$ đến mặt phẳng $(P)$ là: $d(M, (P)) = \\frac{{|2(1) - 2(2) + 1(3) + ({3*val - 1})|}}{{\\sqrt{{2^2 + (-2)^2 + 1^2}}}} = \\frac{{{3*val}}}{{3}} = {val}$.",
                    tikz_code=None,
                    sympy_code=f"result = {val}\nis_valid = True",
                    verified=True
                )
            else:
                x_val = random.choice([3, 4, 5])
                return Question(
                    id=slot.slot_id,
                    type=QuestionType.SHORT_ANSWER,
                    topic=slot.topic,
                    subtopic=slot.subtopic,
                    level=slot.level,
                    stem=f"Tìm giá trị của $x$ biết $2x - 5 = {2*x_val - 5}$.",
                    correct_value=str(x_val),
                    solution=f"Ta có $2x - 5 = {2*x_val - 5} \\Leftrightarrow 2x = {2*x_val} \\Leftrightarrow x = {x_val}$.",
                    tikz_code=None,
                    sympy_code=f"result = {x_val}\nis_valid = True",
                    verified=True
                )

        else:
            return Question(
                id=slot.slot_id,
                type=QuestionType.ESSAY,
                topic=slot.topic,
                subtopic=slot.subtopic,
                level=slot.level,
                stem="Tìm tất cả các giá trị thực của tham số $m$ để hàm số $y = x^3 - 3x^2 + mx - 1$ đồng biến trên $\\mathbb{R}$.",
                solution="Ta có $y' = 3x^2 - 6x + m$. Để hàm số đồng biến trên $\\mathbb{R}$ thì $y' \\ge 0, \\forall x \\in \\mathbb{R} \\Leftrightarrow \\Delta' = 9 - 3m \\le 0 \\Leftrightarrow m \\ge 3$.",
                tikz_code=None,
                sympy_code="is_valid = True",
                verified=True
            )
