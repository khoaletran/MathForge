"""
Bộ kiểm thử toàn diện cho hệ thống sinh đề thi Toán GDPT 2018 (29 ma trận chuẩn).
Kiểm tra:
1. Sinh đề thành công trên TOÀN BỘ 29 ma trận chuẩn (Lớp 6 đến 12).
2. Kiểm tra cách ly khối lớp nghiêm ngặt: Lớp 6-9 không có Đạo hàm/Tích phân/Cực trị.
3. Kiểm tra số tự nhiên Lớp 6: Tuyệt đối không dùng số âm cho phép tính số tự nhiên.
4. Kiểm tra chống trùng lặp: Không trùng lặp nguyên văn hoặc trùng lặp <NUM> masked stem.
5. Kiểm tra tính biến thiên qua các lần sinh (Randomization).
6. Kiểm tra API /generate/slot suy luận lớp và báo lỗi khi thiếu thông tin.
7. Kiểm tra bóc tách Excel kèm báo lỗi theo dòng.
"""

import io
import sys
sys.path.insert(0, 'backend')
import openpyxl
from fastapi.testclient import TestClient

from app.models.question import ExamSlot, QuestionType, CognitiveLevel, Question
from app.services.matrix_service import MatrixService
from app.services.template_registry import TemplateRegistry, AntiDuplicateEngine
from app.services.ai_service import AIService
from main import app

client = TestClient(app)

def test_anti_duplicate_engine():
    """Kiểm tra engine chống trùng lặp đa lớp."""
    stem1 = "Cho hàm số $y = f(x)$ có đạo hàm $f'(x) = x(x - 3)(x + 1)^2$. Hàm số có bao nhiêu điểm cực trị?"
    stem2 = "Cho hàm số $y = f(x)$ có đạo hàm $f'(x) = x(x - 4)(x + 1)^2$. Hàm số có bao nhiêu điểm cực trị?"
    
    masked1 = AntiDuplicateEngine.mask_numbers(stem1)
    masked2 = AntiDuplicateEngine.mask_numbers(stem2)
    assert masked1 == masked2, "Cùng dạng chỉ khác hệ số phải có masked numbers giống nhau"
    
    q1 = Question(
        id="c1",
        type=QuestionType.MULTIPLE_CHOICE,
        topic="Cực trị",
        level=CognitiveLevel.NHAN_BIET,
        stem=stem1,
        solution="sol",
        template_id="g12_p1_extrema_factors"
    )
    q2 = Question(
        id="c2",
        type=QuestionType.MULTIPLE_CHOICE,
        topic="Cực trị",
        level=CognitiveLevel.NHAN_BIET,
        stem=stem2,
        solution="sol",
        template_id="g12_p1_extrema_factors"
    )
    
    # Ở chế độ thường: q2 phải bị đánh dấu là duplicate của q1
    assert AntiDuplicateEngine.is_duplicate(q2, [q1], allow_same_template=False) is True
    # Ở chế độ clone: cho phép cùng template_id
    assert AntiDuplicateEngine.is_duplicate(q2, [q1], allow_same_template=True) is True  # masked stem vẫn trùng

def test_grade_6_natural_arithmetic_no_negatives():
    """Kiểm tra Lớp 6 bài toán số tự nhiên tuyệt đối không dùng số âm hoặc đạo hàm."""
    ai_service = AIService()
    slot_nat = ExamSlot(
        slot_id="slot_g6_nat",
        slot_number=2,
        part=1,
        type=QuestionType.MULTIPLE_CHOICE,
        topic="Số và Đại số",
        subtopic="Chương 1. Các phép tính với số tự nhiên",
        level=CognitiveLevel.NHAN_BIET,
        points=0.25
    )
    
    for _ in range(10):
        q = ai_service.generate_question(slot=slot_nat, grade=6)
        # Không được chứa số âm kiểu (-15) + 28
        assert "(-" not in q.stem, f"Số tự nhiên không được chứa số âm: {q.stem}"
        assert "đạo hàm" not in q.stem.lower()
        assert "cực trị" not in q.stem.lower()

def test_all_29_preset_matrices_generation():
    """Kiểm thử sinh đề trên toàn bộ 29 ma trận chuẩn của Bộ GD&ĐT."""
    matrices = MatrixService.get_all_preset_matrices()
    assert len(matrices) == 29, f"Cần có đúng 29 ma trận chuẩn, hiện có {len(matrices)}"
    
    ai_service = AIService()
    
    for m in matrices:
        generated_questions = []
        for s in m.slots:
            q = ai_service.generate_question(
                slot=s,
                grade=m.grade,
                avoid_questions=generated_questions,
                mode="generate"
            )
            generated_questions.append(q)
            
            # Kiểm tra cách ly khối lớp
            if m.grade <= 9:
                stem_lower = q.stem.lower()
                assert "đạo hàm" not in stem_lower, f"Rò rỉ đạo hàm vào Lớp {m.grade} ở ma trận {m.id}, câu #{s.slot_number}"
                assert "cực trị của hàm" not in stem_lower, f"Rò rỉ cực trị vào Lớp {m.grade} ở ma trận {m.id}, câu #{s.slot_number}"
                assert "tích phân" not in stem_lower, f"Rò rỉ tích phân vào Lớp {m.grade} ở ma trận {m.id}, câu #{s.slot_number}"

        assert len(generated_questions) == len(m.slots)
        print(f"PASS: Ma trận {m.id} (Lớp {m.grade}) - {len(generated_questions)} câu thành công.")

def test_variation_across_runs():
    """Kiểm tra sinh đề nhiều lần trên cùng 1 ma trận tạo ra các biến thể số liệu khác nhau."""
    ai_service = AIService()
    m = MatrixService.get_matrix_by_id("matrix_6_gk1")
    
    q1 = ai_service.generate_question(slot=m.slots[1], grade=6)
    q2 = ai_service.generate_question(slot=m.slots[1], grade=6, avoid_questions=[q1])
    
    # Hai câu khác nhau về dữ kiện
    assert q1.stem != q2.stem

def test_legacy_slot_api_inference():
    """Kiểm tra API /generate/slot suy luận lớp tự động hoặc báo 400 nếu mập mờ."""
    m6 = MatrixService.get_matrix_by_id("matrix_6_gk1")
    slot = m6.slots[0]
    
    # 1. Gọi không truyền grade nhưng slot khớp duy nhất trong preset
    resp = client.post("/api/generate/slot", json={
        "slot": slot.model_dump()
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "đạo hàm" not in data["stem"].lower()

    # 2. Gọi với slot giả lập không tồn tại trong preset mà không có grade -> phải báo 400
    fake_slot = ExamSlot(
        slot_id="custom_unknown_1",
        slot_number=1,
        part=1,
        type=QuestionType.MULTIPLE_CHOICE,
        topic="Chuyên đề lạ",
        subtopic="Không có trong sách",
        level=CognitiveLevel.NHAN_BIET
    )
    resp_fake = client.post("/api/generate/slot", json={
        "slot": fake_slot.model_dump()
    })
    assert resp_fake.status_code == 400
    assert "Thiếu thông tin khối lớp" in resp_fake.json()["detail"]

def test_excel_upload_validation_and_errors():
    """Kiểm tra kiểm duyệt file Excel theo từng dòng."""
    # 1. Tạo file Excel hợp lệ
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["STT", "Phần", "Dạng câu hỏi", "Chủ đề", "Dạng bài chi tiết", "Mức độ", "Điểm"])
    ws.append([1, "1", "Trắc nghiệm 4 lựa chọn", "Số và Đại số", "Chương 1. Tập hợp", "Nhận biết", 0.25])
    ws.append([2, "2", "Tự luận", "Số và Đại số", "Chương 1. Phép tính", "Thông hiểu", 1.0])
    
    bio = io.BytesIO()
    wb.save(bio)
    bio.seek(0)
    
    matrix = MatrixService.parse_excel_matrix(bio.getvalue(), grade=7)
    assert matrix.grade == 7
    assert len(matrix.slots) == 2
    
    # 2. Tạo file Excel cố tình sai Mức độ ở dòng 3
    wb_err = openpyxl.Workbook()
    ws_err = wb_err.active
    ws_err.append(["STT", "Phần", "Dạng câu hỏi", "Chủ đề", "Dạng bài chi tiết", "Mức độ", "Điểm"])
    ws_err.append([1, "1", "Trắc nghiệm 4 lựa chọn", "Số và Đại số", "Chương 1. Tập hợp", "Nhận biết", 0.25])
    ws_err.append([2, "1", "Trắc nghiệm 4 lựa chọn", "Số và Đại số", "Chương 1. Phép tính", "MỨC ĐỘ BỊ SAI", 0.25])
    
    bio_err = io.BytesIO()
    wb_err.save(bio_err)
    bio_err.seek(0)
    
    try:
        MatrixService.parse_excel_matrix(bio_err.getvalue())
        assert False, "Phải ném lỗi khi mức độ nhận thức sai"
    except ValueError as ve:
        assert "Dòng 3" in str(ve), f"Thông báo lỗi phải chỉ rõ Dòng 3: {str(ve)}"
        assert "Mức độ nhận thức 'MỨC ĐỘ BỊ SAI' không hợp lệ" in str(ve)
    print("PASS: Excel row validation verified.")

if __name__ == "__main__":
    test_anti_duplicate_engine()
    test_grade_6_natural_arithmetic_no_negatives()
    test_variation_across_runs()
    test_legacy_slot_api_inference()
    test_excel_upload_validation_and_errors()
    test_all_29_preset_matrices_generation()
    print("\n>>> TẤT CẢ CÁC BÀI KIỂM THỬ ĐÃ VƯỢT QUA 100%! <<<")
