import traceback
import math
from typing import Dict, Any, Optional, Tuple
import sympy as sp

class SympyVerifier:
    """
    Dịch vụ kiểm chứng toán học bằng SymPy:
    - Chạy sandboxed code kiểm tra kết quả tính toán
    - Hỗ trợ giải phương trình, đạo hàm, tích phân, cực trị, tiệm cận, hình giải tích Oxyz
    """

    ALLOWED_SYMBOLS = {
        'x': sp.Symbol('x', real=True),
        'y': sp.Symbol('y', real=True),
        'z': sp.Symbol('z', real=True),
        't': sp.Symbol('t', real=True),
        'm': sp.Symbol('m', real=True),
        'a': sp.Symbol('a', real=True),
        'b': sp.Symbol('b', real=True),
        'c': sp.Symbol('c', real=True),
        'd': sp.Symbol('d', real=True),
    }

    @classmethod
    def get_safe_namespace(cls) -> Dict[str, Any]:
        """Tạo namespace an toàn chỉ gồm các hàm toán học của SymPy."""
        ns = {
            'sp': sp,
            'symbols': sp.symbols,
            'Symbol': sp.Symbol,
            'solve': sp.solve,
            'solveset': sp.solveset,
            'diff': sp.diff,
            'integrate': sp.integrate,
            'limit': sp.limit,
            'oo': sp.oo,
            'Matrix': sp.Matrix,
            'simplify': sp.simplify,
            'expand': sp.expand,
            'factor': sp.factor,
            'Eq': sp.Eq,
            'sqrt': sp.sqrt,
            'sin': sp.sin,
            'cos': sp.cos,
            'tan': sp.tan,
            'exp': sp.exp,
            'log': sp.log,
            'pi': sp.pi,
            'E': sp.E,
            'S': sp.S,
            'Rational': sp.Rational,
            'Abs': sp.Abs,
            'result': None,
            'is_valid': False,
        }
        ns.update(cls.ALLOWED_SYMBOLS)
        return ns

    @classmethod
    def execute_code(cls, code: str) -> Tuple[bool, Any, str]:
        """
        Thực thi đoạn mã SymPy ngắn và lấy biến `result` hoặc `is_valid`.
        Trả về: (thành_công, giá_trị_result, thông_báo_lỗi)
        """
        if not code or not code.strip():
            return False, None, "Mã SymPy trống"

        # Kiểm tra từ khóa nguy hiểm
        blocked_keywords = ['__', 'import', 'open', 'eval', 'exec', 'compile', 'os', 'sys', 'shutil', 'subprocess']
        for kw in blocked_keywords:
            if kw in code:
                return False, None, f"Từ khóa bị cấm: {kw}"

        namespace = cls.get_safe_namespace()
        try:
            # Biên dịch và thực thi
            compiled = compile(code, '<sympy_sandbox>', 'exec')
            exec(compiled, {"__builtins__": {}}, namespace)
            
            result = namespace.get('result', None)
            is_valid = namespace.get('is_valid', True)
            return True, result, "Xác minh thành công"
        except Exception as e:
            return False, None, f"Lỗi tính toán SymPy: {str(e)}"

    @classmethod
    def verify_expression_equality(cls, expr1: str, expr2: str) -> Tuple[bool, str]:
        """Kiểm tra xem 2 biểu thức toán học có tương đương nhau hay không (expr1 == expr2)"""
        try:
            ns = cls.get_safe_namespace()
            e1 = sp.sympify(expr1, locals=ns)
            e2 = sp.sympify(expr2, locals=ns)
            diff = sp.simplify(e1 - e2)
            if diff == 0:
                return True, "Hai biểu thức tương đương"
            return False, f"Hai biểu thức khác nhau: chênh lệch là {diff}"
        except Exception as e:
            return False, f"Không thể so sánh: {str(e)}"

    @classmethod
    def verify_question(cls, question_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Kiểm tra tính đúng đắn của 1 câu hỏi nếu có sympy_code hoặc các trường chuẩn.
        """
        sympy_code = question_dict.get('sympy_code')
        if sympy_code:
            success, result, msg = cls.execute_code(sympy_code)
            return {
                "verified": success,
                "calculated_result": str(result) if result is not None else None,
                "message": msg
            }

        # Nếu không có code tự sinh, thử suy diễn theo dạng câu
        q_type = question_dict.get('type')
        if q_type == "SHORT_ANSWER":
            correct_val = question_dict.get('correct_value')
            if correct_val:
                try:
                    ns = cls.get_safe_namespace()
                    val = sp.sympify(correct_val, locals=ns)
                    return {
                        "verified": True,
                        "calculated_result": str(val),
                        "message": "Giá trị số hợp lệ"
                    }
                except Exception as e:
                    return {"verified": False, "message": f"Giá trị không hợp lệ: {str(e)}"}

        return {"verified": True, "message": "Không yêu cầu kiểm chứng số học"}
