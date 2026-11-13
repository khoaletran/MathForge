import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_full_pipeline():
    print("=== BẮT ĐẦU KIỂM THỬ TOÀN DIỆN HỆ THỐNG ===")
    
    # 1. Kiểm tra Health
    res_health = client.get("/api/health")
    assert res_health.status_code == 200
    print("1. [PASS] Kiểm tra /api/health:", res_health.json())

    # 2. Kiểm tra Ma trận chuẩn 2025
    res_matrix = client.get("/api/matrix/default")
    assert res_matrix.status_code == 200
    matrix = res_matrix.json()
    print(f"2. [PASS] Lấy ma trận chuẩn: {len(matrix['slots'])} slots")

    # 3. Kiểm tra Tải file Excel mẫu ma trận
    res_excel = client.get("/api/matrix/download-template")
    assert res_excel.status_code == 200
    assert len(res_excel.content) > 1000
    print(f"3. [PASS] Tải file Excel mẫu: {len(res_excel.content)} bytes")

    # 4. Kiểm tra Sinh câu hỏi cho 3 dạng thức
    slot_mc = matrix['slots'][0] # Phần I: Trắc nghiệm 4 lựa chọn
    res_q1 = client.post("/api/generate/slot", json={"slot": slot_mc})
    assert res_q1.status_code == 200
    q1 = res_q1.json()
    print("4.1. [PASS] Sinh câu Phần I (4 lựa chọn):", q1["stem"][:60], "...")

    slot_tf = matrix['slots'][12] # Phần II: Đúng / Sai
    res_q2 = client.post("/api/generate/slot", json={"slot": slot_tf})
    assert res_q2.status_code == 200
    q2 = res_q2.json()
    print("4.2. [PASS] Sinh câu Phần II (Đúng/Sai):", q2["stem"][:60], "...")

    slot_sa = matrix['slots'][16] # Phần III: Trả lời ngắn
    res_q3 = client.post("/api/generate/slot", json={"slot": slot_sa})
    assert res_q3.status_code == 200
    q3 = res_q3.json()
    print("4.3. [PASS] Sinh câu Phần III (Trả lời ngắn):", q3["stem"][:60], "...")

    # 5. Kiểm tra Xác minh SymPy
    res_sympy = client.post("/api/verify/math", json={"code": "x = sp.Symbol('x')\nresult = sp.diff(x**3, x)\nis_valid = (result == 3*x**2)"})
    assert res_sympy.status_code == 200
    assert res_sympy.json()["success"] is True
    print("5. [PASS] Kiểm chứng toán học SymPy:", res_sympy.json())

    # 6. Kiểm tra Ghép khung LaTeX chuẩn ex_test.sty
    paper = {
        "id": "exam_101",
        "title": matrix["title"],
        "school_name": "SỞ GIÁO DỤC VÀ ĐÀO TẠO HÀ NỘI",
        "exam_name": "KỲ THI TỐT NGHIỆP TRUNG HỌC PHỔ THÔNG NĂM 2025",
        "academic_year": "2024 - 2025",
        "exam_code": "101",
        "time_minutes": 90,
        "questions": [q1, q2, q3]
    }
    res_latex = client.post("/api/export/latex", json={"paper": paper, "include_solution": True})
    assert res_latex.status_code == 200
    latex_code = res_latex.json()["latex_code"]
    assert r"\documentclass[12pt,a4paper]{article}" in latex_code
    assert r"\choice" in latex_code
    assert r"\choiceTF" in latex_code
    assert r"\shortans" in latex_code
    assert r"\loigiai" in latex_code
    assert r"BẢNG ĐÁP ÁN THAM KHẢO" in latex_code
    print(f"6. [PASS] Ghép khung LaTeX ex_test thành công ({len(latex_code)} ký tự)")

    # 7. Kiểm tra Phục vụ Frontend
    res_fe = client.get("/")
    assert res_fe.status_code == 200
    assert "<!doctype html>" in res_fe.text
    print("7. [PASS] Frontend Single Page Application đã được nạp sẵn sàng!")

    print("\n🎉 TẤT CẢ 7 BƯỚC KIỂM THỬ ĐÃ THÀNH CÔNG RỰC RỠ! 🎉")

if __name__ == "__main__":
    test_full_pipeline()
