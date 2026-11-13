import io
import json
import os
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from typing import List, Dict, Any, Optional
from app.models.question import ExamMatrix, ExamSlot, QuestionType, CognitiveLevel

CUSTOM_MATRICES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "matrices"))
os.makedirs(CUSTOM_MATRICES_DIR, exist_ok=True)

# Helper functions to build standard slot structures
def _build_thcs_slots(prefix: str, tn_items: List[tuple], tl_items: List[tuple]) -> List[ExamSlot]:
    """
    Cấu trúc chuẩn THCS (Lớp 6 đến Lớp 9):
    - Phần I: 12 câu trắc nghiệm (8 NB, 4 TH) x 0.25đ = 3.0đ
    - Phần II: 4 bài Tự luận gồm 7 ý (2 NB, 2 TH, 2 VD, 1 VDC) x 1.0đ = 7.0đ
    Tổng điểm: 10.0đ.
    """
    slots = []
    for i, (top, sub, lev) in enumerate(tn_items, 1):
        slots.append(ExamSlot(
            slot_id=f"{prefix}_tn_{i}",
            slot_number=i,
            part=1,
            type=QuestionType.MULTIPLE_CHOICE,
            topic=top,
            subtopic=sub,
            level=lev,
            points=0.25
        ))
    for j, (top, sub, lev, pts) in enumerate(tl_items, 13):
        slots.append(ExamSlot(
            slot_id=f"{prefix}_tl_{j}",
            slot_number=j,
            part=2,
            type=QuestionType.ESSAY,
            topic=top,
            subtopic=sub,
            level=lev,
            points=pts
        ))
    return slots

def _build_thpt_10_11_slots(prefix: str, tn_items: List[tuple], tf_items: List[tuple], tl_items: List[tuple]) -> List[ExamSlot]:
    """
    Cấu trúc chuẩn THPT Lớp 10 & 11 (70% Trắc nghiệm + 30% Tự luận):
    - Phần I: 12 câu trắc nghiệm 4 lựa chọn (8 NB, 4 TH) x 0.25đ = 3.0đ
    - Phần II: 4 câu Đúng/Sai (16 ý: 4 NB, 8 TH, 4 VD) x 1.0đ/câu = 4.0đ
    - Phần III: 3 ý Tự luận (1 NB, 1 VD, 1 VDC) x 1.0đ = 3.0đ
    Tổng điểm: 10.0đ.
    """
    slots = []
    for i, (top, sub, lev) in enumerate(tn_items, 1):
        slots.append(ExamSlot(
            slot_id=f"{prefix}_p1_{i}",
            slot_number=i,
            part=1,
            type=QuestionType.MULTIPLE_CHOICE,
            topic=top,
            subtopic=sub,
            level=lev,
            points=0.25
        ))
    for j, (top, sub, lev) in enumerate(tf_items, 13):
        slots.append(ExamSlot(
            slot_id=f"{prefix}_p2_{j}",
            slot_number=j,
            part=2,
            type=QuestionType.TRUE_FALSE,
            topic=top,
            subtopic=sub,
            level=lev,
            points=1.0
        ))
    for k, (top, sub, lev) in enumerate(tl_items, 17):
        slots.append(ExamSlot(
            slot_id=f"{prefix}_p3_{k}",
            slot_number=k,
            part=3,
            type=QuestionType.ESSAY,
            topic=top,
            subtopic=sub,
            level=lev,
            points=1.0
        ))
    return slots

def _build_thpt_12_slots(prefix: str, tn_items: List[tuple], tf_items: List[tuple], sa_items: List[tuple]) -> List[ExamSlot]:
    """
    Cấu trúc chuẩn THPT Lớp 12 & Tốt nghiệp THPT 2025:
    - Phần I: 12 câu trắc nghiệm 4 lựa chọn (8 NB, 4 TH) x 0.25đ = 3.0đ
    - Phần II: 4 câu Đúng/Sai với 4 ý a, b, c, d (8 NB, 6 TH, 2 VD) x 1.0đ = 4.0đ
    - Phần III: 6 câu trắc nghiệm trả lời ngắn (1 TH, 3 VD, 2 VDC) x 0.5đ = 3.0đ
    Tổng cộng: 22 câu = 10.0đ.
    """
    slots = []
    for i, (top, sub, lev) in enumerate(tn_items, 1):
        slots.append(ExamSlot(
            slot_id=f"{prefix}_p1_{i}",
            slot_number=i,
            part=1,
            type=QuestionType.MULTIPLE_CHOICE,
            topic=top,
            subtopic=sub,
            level=lev,
            points=0.25
        ))
    for j, (top, sub, lev) in enumerate(tf_items, 13):
        slots.append(ExamSlot(
            slot_id=f"{prefix}_p2_{j}",
            slot_number=j,
            part=2,
            type=QuestionType.TRUE_FALSE,
            topic=top,
            subtopic=sub,
            level=lev,
            points=1.0
        ))
    for k, (top, sub, lev) in enumerate(sa_items, 17):
        slots.append(ExamSlot(
            slot_id=f"{prefix}_p3_{k}",
            slot_number=k,
            part=3,
            type=QuestionType.SHORT_ANSWER,
            topic=top,
            subtopic=sub,
            level=lev,
            points=0.5
        ))
    return slots


class MatrixService:
    """
    Dịch vụ quản lý Ma trận đề thi Toán theo Chương trình GDPT 2018 (SGK Kết nối tri thức).
    Đặc biệt cung cấp:
    - Ma trận chuẩn 22 câu đề thi Tốt nghiệp THPT 2025 của Bộ GD&ĐT:
      + Phần I: 12 câu trắc nghiệm 4 lựa chọn (3.0 điểm)
      + Phần II: 4 câu trắc nghiệm Đúng/Sai với 4 ý a, b, c, d (4.0 điểm)
      + Phần III: 6 câu trắc nghiệm trả lời ngắn điền số (3.0 điểm)
    - Toàn bộ ma trận định kì Giữa kì I, Cuối kì I, Giữa kì II, Cuối kì II cho THCS (Lớp 6, 7, 8, 9) và THPT (Lớp 10, 11, 12).
    - Hỗ trợ ma trận tùy biến linh hoạt không giới hạn cấu trúc.
    """

    # =========================================================================
    # ĐỀ THI TỐT NGHIỆP THPT 2025 (CHUẨN 22 CÂU BỘ GD&ĐT)
    # =========================================================================
    @classmethod
    def get_matrix_12_thpt_2025(cls) -> ExamMatrix:
        """Đề thi chuẩn 22 câu Tốt nghiệp THPT 2025 của Bộ GD&ĐT."""
        p1 = [
            ("Số và Đại số", "Ứng dụng đạo hàm: Tính đơn điệu của hàm số", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Ứng dụng đạo hàm: Cực trị của hàm số", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Ứng dụng đạo hàm: Giá trị lớn nhất, nhỏ nhất trên đoạn", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Ứng dụng đạo hàm: Đường tiệm cận của đồ thị hàm số", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Ứng dụng đạo hàm: Nhận dạng bảng biến thiên và đồ thị", CognitiveLevel.NHAN_BIET),
            ("Hình học và Đo lường", "Tọa độ vectơ trong không gian Oxyz", CognitiveLevel.NHAN_BIET),
            ("Hình học và Đo lường", "Phương trình mặt cầu cơ bản", CognitiveLevel.NHAN_BIET),
            ("Thống kê và Xác suất", "Số đặc trưng đo mức độ phân tán mẫu ghép nhóm", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Ứng dụng đạo hàm: Bài toán tương giao và đồ thị", CognitiveLevel.THONG_HIEU),
            ("Hình học và Đo lường", "Tích vô hướng và góc trong không gian Oxyz", CognitiveLevel.THONG_HIEU),
            ("Số và Đại số", "Nguyên hàm và tích phân cơ bản", CognitiveLevel.THONG_HIEU),
            ("Thống kê và Xác suất", "Xác suất có điều kiện cơ bản", CognitiveLevel.THONG_HIEU),
        ]
        p2 = [
            ("Số và Đại số", "Khảo sát tính biến thiên toàn diện và đồ thị hàm số", CognitiveLevel.THONG_HIEU),
            ("Hình học và Đo lường", "Phương trình mặt phẳng, đường thẳng và khoảng cách Oxyz", CognitiveLevel.THONG_HIEU),
            ("Số và Đại số", "Ứng dụng tích phân tính diện tích, thể tích", CognitiveLevel.THONG_HIEU),
            ("Thống kê và Xác suất", "Công thức xác suất toàn phần và công thức Bayes", CognitiveLevel.VAN_DUNG),
        ]
        p3 = [
            ("Toán thực tế & Trải nghiệm", "Bài toán tối ưu hóa / cực trị thực tế (chi phí, dung tích)", CognitiveLevel.THONG_HIEU),
            ("Số và Đại số", "Ứng dụng tích phân tính thể tích vật thể tròn xoay", CognitiveLevel.VAN_DUNG),
            ("Hình học và Đo lường", "Mô hình hóa hình học không gian thực tế gắn hệ trục Oxyz", CognitiveLevel.VAN_DUNG),
            ("Thống kê và Xác suất", "Ứng dụng xác suất trong kiểm định chất lượng y tế / kinh tế", CognitiveLevel.VAN_DUNG),
            ("Số và Đại số", "Phương trình, bất phương trình chứa tham số m", CognitiveLevel.VAN_DUNG_CAO),
            ("Hình học và Đo lường", "Cực trị khoảng cách hình học giải tích Oxyz", CognitiveLevel.VAN_DUNG_CAO),
        ]

        slots = _build_thpt_12_slots("thpt2025", p1, p2, p3)
        return ExamMatrix(
            id="matrix_12_thpt_2025",
            title="ĐỀ THI TỐT NGHIỆP TRUNG HỌC PHỔ THÔNG NĂM 2025",
            description="Ma trận chuẩn 22 câu theo format mới của Bộ GD&ĐT (Phần I: 12 TN 4 lựa chọn, Phần II: 4 Đúng/Sai, Phần III: 6 Trả lời ngắn)",
            subject="TOÁN HỌC",
            grade=12,
            semester="Tốt nghiệp THPT",
            time_minutes=90,
            academic_year="2024 - 2025",
            tags=["Tốt nghiệp THPT", "Bộ GD&ĐT 2025", "Chuẩn 22 câu", "Lớp 12"],
            slots=slots
        )

    # =========================================================================
    # LỚP 6 (SGK Kết nối tri thức - 40/30/20/10)
    # =========================================================================
    @classmethod
    def get_matrix_6_gk1(cls) -> ExamMatrix:
        """Ma trận đề Giữa kì I - Toán 6 (Chương 1, 2, 3)."""
        p1 = [
            ("Số và Đại số", "Chương 1. Tập hợp và phần tử của tập hợp", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 1. Các phép tính với số tự nhiên", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 1. Lũy thừa với số mũ tự nhiên", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 2. Quan hệ chia hết và tính chất chia hết", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 2. Dấu hiệu chia hết cho 2, 3, 5, 9", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 2. Số nguyên tố, hợp số", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 3. Tập hợp số nguyên, số nguyên âm", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 3. Thứ tự trong tập hợp các số nguyên", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 1. Thứ tự thực hiện các phép tính", CognitiveLevel.THONG_HIEU),
            ("Số và Đại số", "Chương 2. Ước và bội; ƯCLN và BCNN", CognitiveLevel.THONG_HIEU),
            ("Số và Đại số", "Chương 2. Tìm ƯCLN và BCNN bằng phân tích thừa số nguyên tố", CognitiveLevel.THONG_HIEU),
            ("Số và Đại số", "Chương 3. Phép cộng và trừ hai số nguyên", CognitiveLevel.THONG_HIEU),
        ]
        p2 = [
            ("Số và Đại số", "Chương 1. Viết tập hợp và thực hiện phép tính số tự nhiên (Bài 1a)", CognitiveLevel.NHAN_BIET, 1.0),
            ("Số và Đại số", "Chương 2. Kiểm tra tính chia hết và phân tích ra thừa số nguyên tố (Bài 1b)", CognitiveLevel.NHAN_BIET, 1.0),
            ("Số và Đại số", "Chương 1. Tính giá trị biểu thức hợp lý / thứ tự phép tính (Bài 2a)", CognitiveLevel.THONG_HIEU, 1.0),
            ("Số và Đại số", "Chương 3. Phép cộng, trừ số nguyên và quy tắc dấu ngoặc (Bài 2b)", CognitiveLevel.THONG_HIEU, 1.0),
            ("Số và Đại số", "Chương 1. Bài toán thực tiễn về số tự nhiên / chi phí mua hàng (Bài 3a)", CognitiveLevel.VAN_DUNG, 1.0),
            ("Số và Đại số", "Chương 2. Bài toán thực tiễn ứng dụng ƯCLN, BCNN (Bài 3b)", CognitiveLevel.VAN_DUNG, 1.0),
            ("Số và Đại số", "Chương 2. Tính chia hết nâng cao, chữ số tận cùng hoặc chứng minh (Bài 4)", CognitiveLevel.VAN_DUNG_CAO, 1.0),
        ]
        return ExamMatrix(
            id="matrix_6_gk1",
            title="ĐỀ KIỂM TRA GIỮA HỌC KỲ 1 - TOÁN 6",
            description="Theo SGK Kết nối tri thức: Chương 1 (Số tự nhiên), Chương 2 (Tính chia hết), Chương 3 (Số nguyên)",
            subject="TOÁN HỌC",
            grade=6,
            semester="Giữa kỳ 1",
            time_minutes=90,
            academic_year="2026 - 2027",
            tags=["Lớp 6", "Giữa kỳ 1", "KNTT", "12 TN + 7 TL"],
            slots=_build_thcs_slots("m6_gk1", p1, p2)
        )

    @classmethod
    def get_matrix_6_ck1(cls) -> ExamMatrix:
        """Ma trận đề Cuối kì I - Toán 6 (Chương 1 đến 5)."""
        p1 = [
            ("Số và Đại số", "Chương 1. Tập hợp và phép tính số tự nhiên", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 1. Thứ tự thực hiện phép tính", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 2. Dấu hiệu chia hết và số nguyên tố", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 3. Tập hợp số nguyên, biểu diễn trên trục số", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 3. So sánh hai số nguyên", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 3. Phép cộng, trừ hai số nguyên", CognitiveLevel.NHAN_BIET),
            ("Hình học và Đo lường", "Chương 4. Tam giác đều, hình vuông, lục giác đều", CognitiveLevel.NHAN_BIET),
            ("Hình học và Đo lường", "Chương 4. Hình chữ nhật, hình thoi, hình bình hành", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 1. Phép nhân, chia lũy thừa cùng cơ số", CognitiveLevel.THONG_HIEU),
            ("Số và Đại số", "Chương 2. Tìm ƯCLN, BCNN", CognitiveLevel.THONG_HIEU),
            ("Số và Đại số", "Chương 3. Quy tắc dấu ngoặc và tính nhanh số nguyên", CognitiveLevel.THONG_HIEU),
            ("Hình học và Đo lường", "Chương 5. Hình có trục đối xứng, tâm đối xứng", CognitiveLevel.THONG_HIEU),
        ]
        p2 = [
            ("Số và Đại số", "Chương 1. Thực hiện phép tính số tự nhiên (Bài 1a)", CognitiveLevel.NHAN_BIET, 1.0),
            ("Số và Đại số", "Chương 3. Thực hiện phép tính với số nguyên (Bài 1b)", CognitiveLevel.NHAN_BIET, 1.0),
            ("Số và Đại số", "Chương 2. Tìm ước chung, bội chung của các số (Bài 2a)", CognitiveLevel.THONG_HIEU, 1.0),
            ("Số và Đại số", "Chương 3. Tìm số nguyên x thỏa mãn đẳng thức (Bài 2b)", CognitiveLevel.THONG_HIEU, 1.0),
            ("Số và Đại số", "Chương 3. Bài toán thực tiễn về số nguyên âm (nhiệt độ, độ cao, lỗ lãi) (Bài 3a)", CognitiveLevel.VAN_DUNG, 1.0),
            ("Hình học và Đo lường", "Chương 4. Tính chu vi, diện tích hình chữ nhật, hình thang, lát gạch (Bài 3b)", CognitiveLevel.VAN_DUNG, 1.0),
            ("Số và Đại số", "Chương 2. Bài toán chia hết hoặc tìm giá trị nguyên lớn nhất/nhỏ nhất (Bài 4)", CognitiveLevel.VAN_DUNG_CAO, 1.0),
        ]
        return ExamMatrix(
            id="matrix_6_ck1",
            title="ĐỀ KIỂM TRA CUỐI HỌC KỲ 1 - TOÁN 6",
            description="Bao quát Chương 1 đến Chương 5 (Số tự nhiên, Chia hết, Số nguyên, Hình phẳng, Tính đối xứng)",
            subject="TOÁN HỌC",
            grade=6,
            semester="Học kỳ 1",
            time_minutes=90,
            academic_year="2026 - 2027",
            tags=["Lớp 6", "Cuối kỳ 1", "KNTT", "12 TN + 7 TL"],
            slots=_build_thcs_slots("m6_ck1", p1, p2)
        )

    @classmethod
    def get_matrix_6_gk2(cls) -> ExamMatrix:
        """Ma trận đề Giữa kì II - Toán 6 (Chương 6 Phân số, Chương 7 Số thập phân)."""
        p1 = [
            ("Số và Đại số", "Chương 6. Khái niệm phân số, phân số bằng nhau", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 6. Tính chất cơ bản của phân số, rút gọn phân số", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 6. So sánh hai phân số", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 6. Phép nhân hai phân số", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 6. Phép chia hai phân số", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 6. Hỗn số dương", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 7. Số thập phân và số đối của số thập phân", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 7. So sánh các số thập phân", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 6. Cộng, trừ hai phân số khác mẫu", CognitiveLevel.THONG_HIEU),
            ("Số và Đại số", "Chương 6. Tính hợp lý biểu thức phân số", CognitiveLevel.THONG_HIEU),
            ("Số và Đại số", "Chương 6. Tìm phân số của một số cho trước", CognitiveLevel.THONG_HIEU),
            ("Số và Đại số", "Chương 7. Các phép tính cộng, trừ, nhân, chia số thập phân", CognitiveLevel.THONG_HIEU),
        ]
        p2 = [
            ("Số và Đại số", "Chương 6. Thực hiện phép tính cộng trừ phân số (Bài 1a)", CognitiveLevel.NHAN_BIET, 1.0),
            ("Số và Đại số", "Chương 6. Thực hiện phép tính nhân chia phân số (Bài 1b)", CognitiveLevel.NHAN_BIET, 1.0),
            ("Số và Đại số", "Chương 6. Tính giá trị biểu thức phân số hợp lý (Bài 2a)", CognitiveLevel.THONG_HIEU, 1.0),
            ("Số và Đại số", "Chương 7. Tìm x trong biểu thức chứa số thập phân (Bài 2b)", CognitiveLevel.THONG_HIEU, 1.0),
            ("Số và Đại số", "Chương 6. Bài toán thực tiễn về phân số (Bài 3a)", CognitiveLevel.VAN_DUNG, 1.0),
            ("Số và Đại số", "Chương 7. Bài toán thực tiễn tính tiền, giảm giá phần trăm (Bài 3b)", CognitiveLevel.VAN_DUNG, 1.0),
            ("Số và Đại số", "Chương 6. Tính tổng dãy phân số theo quy luật (Bài 4)", CognitiveLevel.VAN_DUNG_CAO, 1.0),
        ]
        return ExamMatrix(
            id="matrix_6_gk2",
            title="ĐỀ KIỂM TRA GIỮA HỌC KỲ 2 - TOÁN 6",
            description="Theo SGK Kết nối tri thức: Chương 6 (Phân số), Chương 7 (Số thập phân)",
            subject="TOÁN HỌC",
            grade=6,
            semester="Giữa kỳ 2",
            time_minutes=90,
            academic_year="2026 - 2027",
            tags=["Lớp 6", "Giữa kỳ 2", "KNTT", "12 TN + 7 TL"],
            slots=_build_thcs_slots("m6_gk2", p1, p2)
        )

    @classmethod
    def get_matrix_6_ck2(cls) -> ExamMatrix:
        """Ma trận đề Cuối kì II - Toán 6 (Chương 6 đến Chương 9)."""
        p1 = [
            ("Số và Đại số", "Chương 6. Khái niệm phân số và phân số bằng nhau", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 6. So sánh phân số", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 7. Số thập phân và làm tròn số", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 7. Tỉ số và tỉ số phần trăm", CognitiveLevel.NHAN_BIET),
            ("Hình học và Đo lường", "Chương 8. Điểm, đường thẳng, ba điểm thẳng hàng", CognitiveLevel.NHAN_BIET),
            ("Hình học và Đo lường", "Chương 8. Đoạn thẳng, độ dài đoạn thẳng", CognitiveLevel.NHAN_BIET),
            ("Thống kê và Xác suất", "Chương 9. Dữ liệu và thu thập dữ liệu", CognitiveLevel.NHAN_BIET),
            ("Thống kê và Xác suất", "Chương 9. Bảng số liệu và biểu đồ cột", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 6. Các phép tính với phân số", CognitiveLevel.THONG_HIEU),
            ("Số và Đại số", "Chương 7. Phép tính số thập phân và bài toán phần trăm", CognitiveLevel.THONG_HIEU),
            ("Hình học và Đo lường", "Chương 8. Góc, số đo góc, trung điểm đoạn thẳng", CognitiveLevel.THONG_HIEU),
            ("Thống kê và Xác suất", "Chương 9. Xác suất thực nghiệm trong trò chơi đơn giản", CognitiveLevel.THONG_HIEU),
        ]
        p2 = [
            ("Số và Đại số", "Chương 6. Thực hiện phép tính phân số (Bài 1a)", CognitiveLevel.NHAN_BIET, 1.0),
            ("Hình học và Đo lường", "Chương 8. Nhận dạng điểm thuộc đường thẳng, đo góc (Bài 1b)", CognitiveLevel.NHAN_BIET, 1.0),
            ("Số và Đại số", "Chương 7. Tìm x liên quan đến số thập phân hoặc phân số (Bài 2a)", CognitiveLevel.THONG_HIEU, 1.0),
            ("Hình học và Đo lường", "Chương 8. Tính độ dài đoạn thẳng và chứng minh trung điểm (Bài 2b)", CognitiveLevel.THONG_HIEU, 1.0),
            ("Số và Đại số", "Chương 7. Bài toán thực tiễn mua bán giảm giá hoặc lãi suất (Bài 3a)", CognitiveLevel.VAN_DUNG, 1.0),
            ("Thống kê và Xác suất", "Chương 9. Đọc biểu đồ cột và tính xác suất thực nghiệm (Bài 3b)", CognitiveLevel.VAN_DUNG, 1.0),
            ("Số và Đại số", "Chương 6. Dãy phân số quy luật hoặc bất đẳng thức phân số (Bài 4)", CognitiveLevel.VAN_DUNG_CAO, 1.0),
        ]
        return ExamMatrix(
            id="matrix_6_ck2",
            title="ĐỀ KIỂM TRA CUỐI HỌC KỲ 2 - TOÁN 6",
            description="Bao quát Chương 6 đến Chương 9 (Phân số, Số thập phân, Hình học cơ bản, Dữ liệu và xác suất thực nghiệm)",
            subject="TOÁN HỌC",
            grade=6,
            semester="Học kỳ 2",
            time_minutes=90,
            academic_year="2026 - 2027",
            tags=["Lớp 6", "Cuối kỳ 2", "KNTT", "12 TN + 7 TL"],
            slots=_build_thcs_slots("m6_ck2", p1, p2)
        )

    # =========================================================================
    # LỚP 7 (SGK Kết nối tri thức - 40/30/20/10)
    # =========================================================================
    @classmethod
    def get_matrix_7_gk1(cls) -> ExamMatrix:
        """Ma trận đề Giữa kì I - Toán 7 (Chương 1, 2, 3)."""
        p1 = [
            ("Số và Đại số", "Chương 1. Tập hợp các số hữu tỉ, biểu diễn trên trục số", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 1. Cộng, trừ, nhân, chia số hữu tỉ", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 1. Lũy thừa với số mũ tự nhiên của số hữu tỉ", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 2. Khái niệm số thập phân vô hạn tuần hoàn, số vô tỉ", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 2. Căn bậc hai số học", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 2. Tập hợp số thực và giá trị tuyệt đối", CognitiveLevel.NHAN_BIET),
            ("Hình học và Đo lường", "Chương 3. Góc ở vị trí đặc biệt (kề bù, đối đỉnh)", CognitiveLevel.NHAN_BIET),
            ("Hình học và Đo lường", "Chương 3. Tia phân giác của một góc", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 1. Quy tắc dấu ngoặc và chuyển vế", CognitiveLevel.THONG_HIEU),
            ("Số và Đại số", "Chương 2. So sánh và làm tròn số thực", CognitiveLevel.THONG_HIEU),
            ("Số và Đại số", "Chương 2. Tính giá trị biểu thức chứa căn bậc hai", CognitiveLevel.THONG_HIEU),
            ("Hình học và Đo lường", "Chương 3. Hai đường thẳng song song và dấu hiệu nhận biết", CognitiveLevel.THONG_HIEU),
        ]
        p2 = [
            ("Số và Đại số", "Chương 1. Thực hiện phép tính số hữu tỉ (Bài 1a)", CognitiveLevel.NHAN_BIET, 1.0),
            ("Số và Đại số", "Chương 2. Tính căn bậc hai số học và giá trị tuyệt đối (Bài 1b)", CognitiveLevel.NHAN_BIET, 1.0),
            ("Số và Đại số", "Chương 1. Tính giá trị biểu thức hợp lý / lũy thừa (Bài 2a)", CognitiveLevel.THONG_HIEU, 1.0),
            ("Hình học và Đo lường", "Chương 3. Tính số đo góc kề bù, đối đỉnh, so le trong (Bài 2b)", CognitiveLevel.THONG_HIEU, 1.0),
            ("Số và Đại số", "Chương 1. Tìm x thỏa mãn đẳng thức số hữu tỉ (Bài 3a)", CognitiveLevel.VAN_DUNG, 1.0),
            ("Hình học và Đo lường", "Chương 3. Chứng minh hai đường thẳng song song hoặc tia phân giác (Bài 3b)", CognitiveLevel.VAN_DUNG, 1.0),
            ("Số và Đại số", "Chương 2. Bài toán cực trị giá trị tuyệt đối hoặc số thực nâng cao (Bài 4)", CognitiveLevel.VAN_DUNG_CAO, 1.0),
        ]
        return ExamMatrix(
            id="matrix_7_gk1",
            title="ĐỀ KIỂM TRA GIỮA HỌC KỲ 1 - TOÁN 7",
            description="Theo SGK Kết nối tri thức: Chương 1 (Số hữu tỉ), Chương 2 (Số thực), Chương 3 (Góc và đường thẳng song song)",
            subject="TOÁN HỌC",
            grade=7,
            semester="Giữa kỳ 1",
            time_minutes=90,
            academic_year="2026 - 2027",
            tags=["Lớp 7", "Giữa kỳ 1", "KNTT", "12 TN + 7 TL"],
            slots=_build_thcs_slots("m7_gk1", p1, p2)
        )

    @classmethod
    def get_matrix_7_ck1(cls) -> ExamMatrix:
        """Ma trận đề Cuối kì I - Toán 7 (Chương 1 đến Chương 5)."""
        p1 = [
            ("Số và Đại số", "Chương 1. Số hữu tỉ và các phép tính", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 1. Lũy thừa của số hữu tỉ", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 2. Căn bậc hai số học và số thực", CognitiveLevel.NHAN_BIET),
            ("Hình học và Đo lường", "Chương 3. Góc đối đỉnh, tia phân giác", CognitiveLevel.NHAN_BIET),
            ("Hình học và Đo lường", "Chương 4. Tổng các góc trong một tam giác", CognitiveLevel.NHAN_BIET),
            ("Hình học và Đo lường", "Chương 4. Hai tam giác bằng nhau", CognitiveLevel.NHAN_BIET),
            ("Thống kê và Xác suất", "Chương 5. Thu thập và phân loại dữ liệu", CognitiveLevel.NHAN_BIET),
            ("Thống kê và Xác suất", "Chương 5. Biểu diễn dữ liệu trên biểu đồ", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 1. Tính hợp lý biểu thức số hữu tỉ", CognitiveLevel.THONG_HIEU),
            ("Số và Đại số", "Chương 2. Làm tròn số và ước lượng kết quả", CognitiveLevel.THONG_HIEU),
            ("Hình học và Đo lường", "Chương 3. Định lí và chứng minh định lí về đường thẳng song song", CognitiveLevel.THONG_HIEU),
            ("Hình học và Đo lường", "Chương 4. Các trường hợp bằng nhau c-c-c, c-g-c, g-c-g", CognitiveLevel.THONG_HIEU),
        ]
        p2 = [
            ("Số và Đại số", "Chương 1. Thực hiện phép tính số hữu tỉ (Bài 1a)", CognitiveLevel.NHAN_BIET, 1.0),
            ("Hình học và Đo lường", "Chương 4. Nhận biết tam giác cân, tam giác đều (Bài 1b)", CognitiveLevel.NHAN_BIET, 1.0),
            ("Số và Đại số", "Chương 2. Tìm x liên quan đến căn bậc hai hoặc số thực (Bài 2a)", CognitiveLevel.THONG_HIEU, 1.0),
            ("Hình học và Đo lường", "Chương 4. Chứng minh hai tam giác bằng nhau (Bài 2b)", CognitiveLevel.THONG_HIEU, 1.0),
            ("Hình học và Đo lường", "Chương 3. Chứng minh hai đường thẳng vuông góc hoặc song song (Bài 3a)", CognitiveLevel.VAN_DUNG, 1.0),
            ("Thống kê và Xác suất", "Chương 5. Đọc và phân tích biểu đồ quạt tròn, biểu đồ đoạn thẳng (Bài 3b)", CognitiveLevel.VAN_DUNG, 1.0),
            ("Hình học và Đo lường", "Chương 4. Bài toán chứng minh hình học tam giác nâng cao (Bài 4)", CognitiveLevel.VAN_DUNG_CAO, 1.0),
        ]
        return ExamMatrix(
            id="matrix_7_ck1",
            title="ĐỀ KIỂM TRA CUỐI HỌC KỲ 1 - TOÁN 7",
            description="Bao quát Chương 1 đến Chương 5 (Số hữu tỉ, Số thực, Góc & song song, Tam giác bằng nhau, Thu thập biểu diễn dữ liệu)",
            subject="TOÁN HỌC",
            grade=7,
            semester="Học kỳ 1",
            time_minutes=90,
            academic_year="2026 - 2027",
            tags=["Lớp 7", "Cuối kỳ 1", "KNTT", "12 TN + 7 TL"],
            slots=_build_thcs_slots("m7_ck1", p1, p2)
        )

    @classmethod
    def get_matrix_7_gk2(cls) -> ExamMatrix:
        """Ma trận đề Giữa kì II - Toán 7 (Chương 6 Tỉ lệ thức, Chương 7 Đa thức 1 biến)."""
        p1 = [
            ("Số và Đại số", "Chương 6. Tỉ lệ thức và các tính chất", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 6. Tính chất của dãy tỉ số bằng nhau", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 6. Đại lượng tỉ lệ thuận", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 6. Đại lượng tỉ lệ nghịch", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 7. Biểu thức số và biểu thức đại số", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 7. Đa thức một biến, bậc của đa thức", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 7. Các hệ số của đa thức một biến", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 7. Nghiệm của đa thức một biến", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 6. Tìm hai số biết tỉ số và tổng hoặc hiệu", CognitiveLevel.THONG_HIEU),
            ("Số và Đại số", "Chương 6. Bài toán chia theo tỉ lệ thuận, nghịch", CognitiveLevel.THONG_HIEU),
            ("Số và Đại số", "Chương 7. Tính giá trị của đa thức một biến", CognitiveLevel.THONG_HIEU),
            ("Số và Đại số", "Chương 7. Cộng, trừ hai đa thức một biến", CognitiveLevel.THONG_HIEU),
        ]
        p2 = [
            ("Số và Đại số", "Chương 6. Tìm x trong tỉ lệ thức đơn giản (Bài 1a)", CognitiveLevel.NHAN_BIET, 1.0),
            ("Số và Đại số", "Chương 7. Thu gọn và sắp xếp đa thức một biến (Bài 1b)", CognitiveLevel.NHAN_BIET, 1.0),
            ("Số và Đại số", "Chương 6. Áp dụng tính chất dãy tỉ số bằng nhau tìm x, y (Bài 2a)", CognitiveLevel.THONG_HIEU, 1.0),
            ("Số và Đại số", "Chương 7. Thực hiện phép cộng, trừ đa thức một biến (Bài 2b)", CognitiveLevel.THONG_HIEU, 1.0),
            ("Số và Đại số", "Chương 6. Bài toán thực tế về đại lượng tỉ lệ (Bài 3a)", CognitiveLevel.VAN_DUNG, 1.0),
            ("Số và Đại số", "Chương 7. Tìm nghiệm của đa thức một biến (Bài 3b)", CognitiveLevel.VAN_DUNG, 1.0),
            ("Số và Đại số", "Chương 7. Chứng minh đa thức không có nghiệm hoặc dãy tỉ số nâng cao (Bài 4)", CognitiveLevel.VAN_DUNG_CAO, 1.0),
        ]
        return ExamMatrix(
            id="matrix_7_gk2",
            title="ĐỀ KIỂM TRA GIỮA HỌC KỲ 2 - TOÁN 7",
            description="Theo SGK Kết nối tri thức: Chương 6 (Tỉ lệ thức và đại lượng tỉ lệ), Chương 7 (Biểu thức đại số và đa thức một biến)",
            subject="TOÁN HỌC",
            grade=7,
            semester="Giữa kỳ 2",
            time_minutes=90,
            academic_year="2026 - 2027",
            tags=["Lớp 7", "Giữa kỳ 2", "KNTT", "12 TN + 7 TL"],
            slots=_build_thcs_slots("m7_gk2", p1, p2)
        )

    @classmethod
    def get_matrix_7_ck2(cls) -> ExamMatrix:
        """Ma trận đề Cuối kì II - Toán 7 (Chương 6 đến Chương 10)."""
        p1 = [
            ("Số và Đại số", "Chương 6. Tỉ lệ thức và dãy tỉ số bằng nhau", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 7. Đa thức một biến và nghiệm", CognitiveLevel.NHAN_BIET),
            ("Thống kê và Xác suất", "Chương 8. Biến cố ngẫu nhiên, biến cố chắc chắn, không thể", CognitiveLevel.NHAN_BIET),
            ("Hình học và Đo lường", "Chương 9. Quan hệ giữa góc và cạnh đối diện trong tam giác", CognitiveLevel.NHAN_BIET),
            ("Hình học và Đo lường", "Chương 9. Quan hệ giữa ba cạnh của một tam giác", CognitiveLevel.NHAN_BIET),
            ("Hình học và Đo lường", "Chương 9. Sự đồng quy của ba đường trung tuyến, phân giác", CognitiveLevel.NHAN_BIET),
            ("Hình học và Đo lường", "Chương 10. Hình hộp chữ nhật và hình lập phương", CognitiveLevel.NHAN_BIET),
            ("Hình học và Đo lường", "Chương 10. Lăng trụ đứng tam giác, lăng trụ đứng tứ giác", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 6. Bài toán tỉ lệ thực tiễn", CognitiveLevel.THONG_HIEU),
            ("Số và Đại số", "Chương 7. Nhân, chia đa thức một biến", CognitiveLevel.THONG_HIEU),
            ("Thống kê và Xác suất", "Chương 8. Xác suất của biến cố trong trò chơi gieo xúc xắc", CognitiveLevel.THONG_HIEU),
            ("Hình học và Đo lường", "Chương 9. Tính chất đường trung trực của đoạn thẳng", CognitiveLevel.THONG_HIEU),
        ]
        p2 = [
            ("Số và Đại số", "Chương 6. Tìm x từ dãy tỉ số bằng nhau (Bài 1a)", CognitiveLevel.NHAN_BIET, 1.0),
            ("Hình học và Đo lường", "Chương 9. Nhận biết quan hệ giữa đường vuông góc và đường xiên (Bài 1b)", CognitiveLevel.NHAN_BIET, 1.0),
            ("Số và Đại số", "Chương 7. Thực hiện phép cộng trừ nhân đa thức một biến (Bài 2a)", CognitiveLevel.THONG_HIEU, 1.0),
            ("Thống kê và Xác suất", "Chương 8. Tính xác suất của biến cố ngẫu nhiên (Bài 2b)", CognitiveLevel.THONG_HIEU, 1.0),
            ("Số và Đại số", "Chương 7. Tìm nghiệm đa thức hoặc chứng minh chia hết (Bài 3a)", CognitiveLevel.VAN_DUNG, 1.0),
            ("Hình học và Đo lường", "Chương 10. Tính diện tích xung quanh, thể tích hình lăng trụ / hình hộp (Bài 3b)", CognitiveLevel.VAN_DUNG, 1.0),
            ("Hình học và Đo lường", "Chương 9. Bài toán bất đẳng thức tam giác hoặc điểm đồng quy nâng cao (Bài 4)", CognitiveLevel.VAN_DUNG_CAO, 1.0),
        ]
        return ExamMatrix(
            id="matrix_7_ck2",
            title="ĐỀ KIỂM TRA CUỐI HỌC KỲ 2 - TOÁN 7",
            description="Bao quát Chương 6 đến Chương 10 (Tỉ lệ thức, Đa thức, Biến cố xác suất, Quan hệ tam giác, Hình khối)",
            subject="TOÁN HỌC",
            grade=7,
            semester="Học kỳ 2",
            time_minutes=90,
            academic_year="2026 - 2027",
            tags=["Lớp 7", "Cuối kỳ 2", "KNTT", "12 TN + 7 TL"],
            slots=_build_thcs_slots("m7_ck2", p1, p2)
        )

    # =========================================================================
    # LỚP 8 (SGK Kết nối tri thức - 40/30/20/10)
    # =========================================================================
    @classmethod
    def get_matrix_8_gk1(cls) -> ExamMatrix:
        """Ma trận đề Giữa kì I - Toán 8 (Chương 1, 2, 3)."""
        p1 = [
            ("Số và Đại số", "Chương 1. Đơn thức nhiều biến, đơn thức thu gọn", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 1. Đa thức nhiều biến và bậc của đa thức", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 1. Đơn thức đồng dạng", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 2. Bình phương của một tổng và một hiệu", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 2. Hiệu hai bình phương", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 2. Lập phương của một tổng và một hiệu", CognitiveLevel.NHAN_BIET),
            ("Hình học và Đo lường", "Chương 3. Tứ giác và tổng các góc của một tứ giác", CognitiveLevel.NHAN_BIET),
            ("Hình học và Đo lường", "Chương 3. Hình thang, hình thang cân và tính chất", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 1. Phép nhân và chia đa thức cho đơn thức", CognitiveLevel.THONG_HIEU),
            ("Số và Đại số", "Chương 2. Phân tích đa thức thành nhân tử bằng đặt nhân tử chung", CognitiveLevel.THONG_HIEU),
            ("Số và Đại số", "Chương 2. Phân tích đa thức bằng dùng hằng đẳng thức", CognitiveLevel.THONG_HIEU),
            ("Hình học và Đo lường", "Chương 3. Dấu hiệu nhận biết hình thang cân", CognitiveLevel.THONG_HIEU),
        ]
        p2 = [
            ("Số và Đại số", "Chương 1. Thu gọn đa thức nhiều biến (Bài 1a)", CognitiveLevel.NHAN_BIET, 1.0),
            ("Số và Đại số", "Chương 2. Khai triển hằng đẳng thức (Bài 1b)", CognitiveLevel.NHAN_BIET, 1.0),
            ("Số và Đại số", "Chương 1. Thực hiện phép nhân, chia đa thức (Bài 2a)", CognitiveLevel.THONG_HIEU, 1.0),
            ("Hình học và Đo lường", "Chương 3. Tính số đo các góc của tứ giác, hình thang cân (Bài 2b)", CognitiveLevel.THONG_HIEU, 1.0),
            ("Số và Đại số", "Chương 2. Phân tích đa thức thành nhân tử nhóm hạng tử (Bài 3a)", CognitiveLevel.VAN_DUNG, 1.0),
            ("Hình học và Đo lường", "Chương 3. Chứng minh hình thang cân và tính độ dài cạnh (Bài 3b)", CognitiveLevel.VAN_DUNG, 1.0),
            ("Số và Đại số", "Chương 2. Tìm giá trị lớn nhất, nhỏ nhất của biểu thức bậc hai (Bài 4)", CognitiveLevel.VAN_DUNG_CAO, 1.0),
        ]
        return ExamMatrix(
            id="matrix_8_gk1",
            title="ĐỀ KIỂM TRA GIỮA HỌC KỲ 1 - TOÁN 8",
            description="Theo SGK Kết nối tri thức: Chương 1 (Đa thức nhiều biến), Chương 2 (Hằng đẳng thức đáng nhớ), Chương 3 (Tứ giác)",
            subject="TOÁN HỌC",
            grade=8,
            semester="Giữa kỳ 1",
            time_minutes=90,
            academic_year="2026 - 2027",
            tags=["Lớp 8", "Giữa kỳ 1", "KNTT", "12 TN + 7 TL"],
            slots=_build_thcs_slots("m8_gk1", p1, p2)
        )

    @classmethod
    def get_matrix_8_ck1(cls) -> ExamMatrix:
        """Ma trận đề Cuối kì I - Toán 8 (Chương 1 đến Chương 5)."""
        p1 = [
            ("Số và Đại số", "Chương 1. Đa thức nhiều biến và các phép toán", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 2. Bảy hằng đẳng thức đáng nhớ", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 2. Phân tích đa thức thành nhân tử", CognitiveLevel.NHAN_BIET),
            ("Hình học và Đo lường", "Chương 3. Tổng số đo các góc của một tứ giác", CognitiveLevel.NHAN_BIET),
            ("Hình học và Đo lường", "Chương 3. Hình bình hành, hình chữ nhật", CognitiveLevel.NHAN_BIET),
            ("Hình học và Đo lường", "Chương 4. Định lí Thalès trong tam giác", CognitiveLevel.NHAN_BIET),
            ("Hình học và Đo lường", "Chương 4. Đường trung bình của tam giác", CognitiveLevel.NHAN_BIET),
            ("Thống kê và Xác suất", "Chương 5. Thu thập và phân loại dữ liệu", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 1. Chia đa thức cho đơn thức", CognitiveLevel.THONG_HIEU),
            ("Hình học và Đo lường", "Chương 3. Hình thoi, hình vuông và dấu hiệu nhận biết", CognitiveLevel.THONG_HIEU),
            ("Hình học và Đo lường", "Chương 4. Tính chất đường phân giác trong tam giác", CognitiveLevel.THONG_HIEU),
            ("Thống kê và Xác suất", "Chương 5. Lựa chọn biểu đồ thích hợp biểu diễn dữ liệu", CognitiveLevel.THONG_HIEU),
        ]
        p2 = [
            ("Số và Đại số", "Chương 1. Rút gọn biểu thức đại số (Bài 1a)", CognitiveLevel.NHAN_BIET, 1.0),
            ("Hình học và Đo lường", "Chương 3. Dùng tính chất hai cạnh đối bằng nhau của hình bình hành (Bài 1b)", CognitiveLevel.NHAN_BIET, 1.0),
            ("Số và Đại số", "Chương 2. Phân tích đa thức thành nhân tử và tìm x (Bài 2a)", CognitiveLevel.THONG_HIEU, 1.0),
            ("Hình học và Đo lường", "Chương 4. Áp dụng định lí Thalès tính độ dài đoạn thẳng (Bài 2b)", CognitiveLevel.THONG_HIEU, 1.0),
            ("Hình học và Đo lường", "Chương 3. Chứng minh tứ giác là hình chữ nhật, hình thoi (Bài 3a)", CognitiveLevel.VAN_DUNG, 1.0),
            ("Thống kê và Xác suất", "Chương 5. Phân tích biểu đồ và nhận xét xu hướng dữ liệu (Bài 3b)", CognitiveLevel.VAN_DUNG, 1.0),
            ("Hình học và Đo lường", "Chương 4. Bài toán chứng minh hình học đường trung bình nâng cao (Bài 4)", CognitiveLevel.VAN_DUNG_CAO, 1.0),
        ]
        return ExamMatrix(
            id="matrix_8_ck1",
            title="ĐỀ KIỂM TRA CUỐI HỌC KỲ 1 - TOÁN 8",
            description="Bao quát Chương 1 đến Chương 5 (Đa thức, Hằng đẳng thức, Tứ giác, Định lí Thalès, Dữ liệu biểu đồ)",
            subject="TOÁN HỌC",
            grade=8,
            semester="Học kỳ 1",
            time_minutes=90,
            academic_year="2026 - 2027",
            tags=["Lớp 8", "Cuối kỳ 1", "KNTT", "12 TN + 7 TL"],
            slots=_build_thcs_slots("m8_ck1", p1, p2)
        )

    @classmethod
    def get_matrix_8_gk2(cls) -> ExamMatrix:
        """Ma trận đề Giữa kì II - Toán 8 (Chương 6 Phân thức, Chương 7 Phương trình bậc nhất)."""
        p1 = [
            ("Số và Đại số", "Chương 6. Khái niệm phân thức đại số", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 6. Tính chất cơ bản của phân thức đại số", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 6. Rút gọn phân thức đại số", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 6. Quy đồng mẫu thức nhiều phân thức", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 7. Phương trình bậc nhất một ẩn và cách giải", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 7. Phương trình đưa về dạng ax + b = 0", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 7. Khái niệm hàm số và đồ thị hàm số", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 7. Hàm số bậc nhất y = ax + b", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 6. Phép cộng và trừ các phân thức đại số", CognitiveLevel.THONG_HIEU),
            ("Số và Đại số", "Chương 6. Phép nhân và chia các phân thức đại số", CognitiveLevel.THONG_HIEU),
            ("Số và Đại số", "Chương 7. Giải phương trình bậc nhất một ẩn", CognitiveLevel.THONG_HIEU),
            ("Số và Đại số", "Chương 7. Hệ số góc của đường thẳng y = ax + b", CognitiveLevel.THONG_HIEU),
        ]
        p2 = [
            ("Số và Đại số", "Chương 6. Rút gọn phân thức đại số đơn giản (Bài 1a)", CognitiveLevel.NHAN_BIET, 1.0),
            ("Số và Đại số", "Chương 7. Giải phương trình bậc nhất một ẩn (Bài 1b)", CognitiveLevel.NHAN_BIET, 1.0),
            ("Số và Đại số", "Chương 6. Thực hiện phép tính phân thức đại số (Bài 2a)", CognitiveLevel.THONG_HIEU, 1.0),
            ("Số và Đại số", "Chương 7. Tìm điều kiện của m để hàm số bậc nhất đồng biến/nghịch biến (Bài 2b)", CognitiveLevel.THONG_HIEU, 1.0),
            ("Số và Đại số", "Chương 6. Rút gọn biểu thức hữu tỉ và tính giá trị nguyên (Bài 3a)", CognitiveLevel.VAN_DUNG, 1.0),
            ("Số và Đại số", "Chương 7. Giải bài toán bằng cách lập phương trình (toán chuyển động, năng suất) (Bài 3b)", CognitiveLevel.VAN_DUNG, 1.0),
            ("Số và Đại số", "Chương 7. Bài toán cực trị đồ thị hoặc tham số m nâng cao (Bài 4)", CognitiveLevel.VAN_DUNG_CAO, 1.0),
        ]
        return ExamMatrix(
            id="matrix_8_gk2",
            title="ĐỀ KIỂM TRA GIỮA HỌC KỲ 2 - TOÁN 8",
            description="Theo SGK Kết nối tri thức: Chương 6 (Phân thức đại số), Chương 7 (Phương trình bậc nhất và hàm số bậc nhất)",
            subject="TOÁN HỌC",
            grade=8,
            semester="Giữa kỳ 2",
            time_minutes=90,
            academic_year="2026 - 2027",
            tags=["Lớp 8", "Giữa kỳ 2", "KNTT", "12 TN + 7 TL"],
            slots=_build_thcs_slots("m8_gk2", p1, p2)
        )

    @classmethod
    def get_matrix_8_ck2(cls) -> ExamMatrix:
        """Ma trận đề Cuối kì II - Toán 8 (Chương 6 đến Chương 10)."""
        p1 = [
            ("Số và Đại số", "Chương 6. Phân thức đại số và điều kiện xác định", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 7. Phương trình bậc nhất một ẩn", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 7. Đồ thị hàm số bậc nhất y = ax + b", CognitiveLevel.NHAN_BIET),
            ("Thống kê và Xác suất", "Chương 8. Kết quả có thể và kết quả thuận lợi", CognitiveLevel.NHAN_BIET),
            ("Hình học và Đo lường", "Chương 9. Hai tam giác đồng dạng", CognitiveLevel.NHAN_BIET),
            ("Hình học và Đo lường", "Chương 9. Trường hợp đồng dạng c-c-c, c-g-c", CognitiveLevel.NHAN_BIET),
            ("Hình học và Đo lường", "Chương 9. Trường hợp đồng dạng góc-góc", CognitiveLevel.NHAN_BIET),
            ("Hình học và Đo lường", "Chương 10. Hình chóp tam giác đều, chóp tứ giác đều", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 6. Rút gọn biểu thức phân thức", CognitiveLevel.THONG_HIEU),
            ("Thống kê và Xác suất", "Chương 8. Tính xác suất của biến cố ngẫu nhiên", CognitiveLevel.THONG_HIEU),
            ("Hình học và Đo lường", "Chương 9. Các trường hợp đồng dạng của tam giác vuông", CognitiveLevel.THONG_HIEU),
            ("Hình học và Đo lường", "Chương 10. Diện tích xung quanh, thể tích hình chóp", CognitiveLevel.THONG_HIEU),
        ]
        p2 = [
            ("Số và Đại số", "Chương 6. Rút gọn phân thức đại số (Bài 1a)", CognitiveLevel.NHAN_BIET, 1.0),
            ("Hình học và Đo lường", "Chương 9. Nhận biết các cặp tam giác đồng dạng (Bài 1b)", CognitiveLevel.NHAN_BIET, 1.0),
            ("Số và Đại số", "Chương 7. Giải phương trình bậc nhất một ẩn (Bài 2a)", CognitiveLevel.THONG_HIEU, 1.0),
            ("Hình học và Đo lường", "Chương 10. Tính diện tích xung quanh hoặc thể tích hình chóp (Bài 2b)", CognitiveLevel.THONG_HIEU, 1.0),
            ("Số và Đại số", "Chương 7. Giải bài toán bằng cách lập phương trình (Bài 3a)", CognitiveLevel.VAN_DUNG, 1.0),
            ("Thống kê và Xác suất", "Chương 8. Tính xác suất thực tế của biến cố (Bài 3b)", CognitiveLevel.VAN_DUNG, 1.0),
            ("Hình học và Đo lường", "Chương 9. Chứng minh tam giác đồng dạng và đẳng thức hình học nâng cao (Bài 4)", CognitiveLevel.VAN_DUNG_CAO, 1.0),
        ]
        return ExamMatrix(
            id="matrix_8_ck2",
            title="ĐỀ KIỂM TRA CUỐI HỌC KỲ 2 - TOÁN 8",
            description="Bao quát Chương 6 đến Chương 10 (Phân thức, Phương trình, Xác suất, Tam giác đồng dạng, Hình chóp đều)",
            subject="TOÁN HỌC",
            grade=8,
            semester="Học kỳ 2",
            time_minutes=90,
            academic_year="2026 - 2027",
            tags=["Lớp 8", "Cuối kỳ 2", "KNTT", "12 TN + 7 TL"],
            slots=_build_thcs_slots("m8_ck2", p1, p2)
        )

    # =========================================================================
    # LỚP 9 (SGK Kết nối tri thức - 40/30/20/10)
    # =========================================================================
    @classmethod
    def get_matrix_9_gk1(cls) -> ExamMatrix:
        """Ma trận đề Giữa kì I - Toán 9 (Chương 1, 2, 3)."""
        p1 = [
            ("Số và Đại số", "Chương 1. Phương trình bậc nhất hai ẩn", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 1. Khái niệm hệ hai phương trình bậc nhất hai ẩn", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 1. Giải hệ phương trình bằng phương pháp thế", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 2. Phương trình quy về phương trình bậc nhất một ẩn", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 2. Bất đẳng thức và tính chất", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 2. Bất phương trình bậc nhất một ẩn", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 3. Khái niệm căn bậc hai số học", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 3. Căn bậc ba của số thực", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 1. Giải hệ phương trình bằng phương pháp cộng đại số", CognitiveLevel.THONG_HIEU),
            ("Số và Đại số", "Chương 2. Giải bất phương trình bậc nhất một ẩn", CognitiveLevel.THONG_HIEU),
            ("Số và Đại số", "Chương 2. Biểu diễn tập nghiệm trên trục số", CognitiveLevel.THONG_HIEU),
            ("Số và Đại số", "Chương 3. Khai căn bậc hai của một bình phương", CognitiveLevel.THONG_HIEU),
        ]
        p2 = [
            ("Số và Đại số", "Chương 1. Giải hệ hai phương trình bậc nhất hai ẩn cơ bản (Bài 1a)", CognitiveLevel.NHAN_BIET, 1.0),
            ("Số và Đại số", "Chương 2. Giải bất phương trình bậc nhất một ẩn (Bài 1b)", CognitiveLevel.NHAN_BIET, 1.0),
            ("Số và Đại số", "Chương 1. Tìm điều kiện nghiệm của hệ phương trình (Bài 2a)", CognitiveLevel.THONG_HIEU, 1.0),
            ("Số và Đại số", "Chương 3. Rút gọn biểu thức chứa căn bậc hai (Bài 2b)", CognitiveLevel.THONG_HIEU, 1.0),
            ("Số và Đại số", "Chương 1. Giải bài toán bằng cách lập hệ phương trình (Bài 3a)", CognitiveLevel.VAN_DUNG, 1.0),
            ("Số và Đại số", "Chương 2. Giải phương trình quy về bậc nhất chứa dấu giá trị tuyệt đối (Bài 3b)", CognitiveLevel.VAN_DUNG, 1.0),
            ("Số và Đại số", "Chương 2. Chứng minh bất đẳng thức Cauchy hoặc tìm GTNN/GTLN (Bài 4)", CognitiveLevel.VAN_DUNG_CAO, 1.0),
        ]
        return ExamMatrix(
            id="matrix_9_gk1",
            title="ĐỀ KIỂM TRA GIỮA HỌC KỲ 1 - TOÁN 9",
            description="Theo SGK Kết nối tri thức: Chương 1 (Hệ phương trình bậc nhất), Chương 2 (Phương trình, BPT 1 ẩn), Chương 3 (Căn bậc hai, căn bậc ba)",
            subject="TOÁN HỌC",
            grade=9,
            semester="Giữa kỳ 1",
            time_minutes=90,
            academic_year="2026 - 2027",
            tags=["Lớp 9", "Giữa kỳ 1", "KNTT", "12 TN + 7 TL"],
            slots=_build_thcs_slots("m9_gk1", p1, p2)
        )

    @classmethod
    def get_matrix_9_ck1(cls) -> ExamMatrix:
        """Ma trận đề Cuối kì I - Toán 9 (Chương 1 đến Chương 5)."""
        p1 = [
            ("Số và Đại số", "Chương 1. Hệ phương trình bậc nhất hai ẩn", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 2. Bất đẳng thức và bất phương trình", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 2. Phương trình tích", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 3. Căn bậc hai và điều kiện xác định", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 3. Căn bậc ba", CognitiveLevel.NHAN_BIET),
            ("Hình học và Đo lường", "Chương 4. Tỉ số lượng giác của góc nhọn (sin, cos, tan, cot)", CognitiveLevel.NHAN_BIET),
            ("Hình học và Đo lường", "Chương 4. Hệ thức giữa cạnh và góc trong tam giác vuông", CognitiveLevel.NHAN_BIET),
            ("Hình học và Đo lường", "Chương 5. Đường tròn và tính chất đối xứng", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 1. Giải hệ phương trình chứa ẩn ở mẫu", CognitiveLevel.THONG_HIEU),
            ("Số và Đại số", "Chương 3. Trục căn thức ở mẫu và rút gọn căn", CognitiveLevel.THONG_HIEU),
            ("Hình học và Đo lường", "Chương 4. Giải tam giác vuông và ứng dụng thực tiễn", CognitiveLevel.THONG_HIEU),
            ("Hình học và Đo lường", "Chương 5. Vị trí tương đối của đường thẳng và đường tròn, tiếp tuyến", CognitiveLevel.THONG_HIEU),
        ]
        p2 = [
            ("Số và Đại số", "Chương 1. Giải hệ phương trình bậc nhất hai ẩn (Bài 1a)", CognitiveLevel.NHAN_BIET, 1.0),
            ("Số và Đại số", "Chương 3. Tính giá trị biểu thức căn thức (Bài 1b)", CognitiveLevel.NHAN_BIET, 1.0),
            ("Số và Đại số", "Chương 2. Giải phương trình quy về bậc nhất (Bài 2a)", CognitiveLevel.THONG_HIEU, 1.0),
            ("Hình học và Đo lường", "Chương 4. Tính tỉ số lượng giác và cạnh tam giác vuông (Bài 2b)", CognitiveLevel.THONG_HIEU, 1.0),
            ("Số và Đại số", "Chương 1. Giải bài toán bằng cách lập hệ phương trình (toán thực tế) (Bài 3a)", CognitiveLevel.VAN_DUNG, 1.0),
            ("Hình học và Đo lường", "Chương 4. Bài toán thực tế đo chiều cao tòa nhà / góc nghiêng (Bài 3b)", CognitiveLevel.VAN_DUNG, 1.0),
            ("Hình học và Đo lường", "Chương 5. Chứng minh tiếp tuyến đường tròn và hệ thức hình học (Bài 4)", CognitiveLevel.VAN_DUNG_CAO, 1.0),
        ]
        return ExamMatrix(
            id="matrix_9_ck1",
            title="ĐỀ KIỂM TRA CUỐI HỌC KỲ 1 - TOÁN 9",
            description="Bao quát Chương 1 đến Chương 5 (Hệ PT, BPT, Căn thức, Hệ thức lượng tam giác vuông, Đường tròn)",
            subject="TOÁN HỌC",
            grade=9,
            semester="Học kỳ 1",
            time_minutes=90,
            academic_year="2026 - 2027",
            tags=["Lớp 9", "Cuối kỳ 1", "KNTT", "12 TN + 7 TL"],
            slots=_build_thcs_slots("m9_ck1", p1, p2)
        )

    @classmethod
    def get_matrix_9_gk2(cls) -> ExamMatrix:
        """Ma trận đề Giữa kì II - Toán 9 (Chương 6 Hàm số y = ax² & PT bậc hai, Chương 7 Tần số)."""
        p1 = [
            ("Số và Đại số", "Chương 6. Hàm số y = ax² (a khác 0) và tính chất", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 6. Đồ thị của hàm số y = ax²", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 6. Phương trình bậc hai một ẩn ax² + bx + c = 0", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 6. Công thức nghiệm của phương trình bậc hai", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 6. Công thức nghiệm thu gọn", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 6. Định lí Viète và ứng dụng nhẩm nghiệm", CognitiveLevel.NHAN_BIET),
            ("Thống kê và Xác suất", "Chương 7. Tần số và bảng tần số", CognitiveLevel.NHAN_BIET),
            ("Thống kê và Xác suất", "Chương 7. Tần số tương đối và biểu đồ tần số tương đối", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 6. Tọa độ giao điểm của parabol và đường thẳng", CognitiveLevel.THONG_HIEU),
            ("Số và Đại số", "Chương 6. Tìm hai số biết tổng và tích", CognitiveLevel.THONG_HIEU),
            ("Số và Đại số", "Chương 6. Giải bài toán bằng cách lập phương trình bậc hai", CognitiveLevel.THONG_HIEU),
            ("Thống kê và Xác suất", "Chương 7. Bảng tần số ghép nhóm và biểu đồ cột ghép nhóm", CognitiveLevel.THONG_HIEU),
        ]
        p2 = [
            ("Số và Đại số", "Chương 6. Vẽ parabol y = ax² và tìm điểm thuộc đồ thị (Bài 1a)", CognitiveLevel.NHAN_BIET, 1.0),
            ("Số và Đại số", "Chương 6. Giải phương trình bậc hai một ẩn cơ bản (Bài 1b)", CognitiveLevel.NHAN_BIET, 1.0),
            ("Số và Đại số", "Chương 6. Áp dụng định lí Viète tính giá trị biểu thức nghiệm (Bài 2a)", CognitiveLevel.THONG_HIEU, 1.0),
            ("Thống kê và Xác suất", "Chương 7. Lập bảng tần số và vẽ biểu đồ hình quạt/đoạn thẳng (Bài 2b)", CognitiveLevel.THONG_HIEU, 1.0),
            ("Số và Đại số", "Chương 6. Giải bài toán bằng cách lập phương trình bậc hai (Bài 3a)", CognitiveLevel.VAN_DUNG, 1.0),
            ("Thống kê và Xác suất", "Chương 7. Phân tích bảng tần số ghép nhóm trong thực tế (Bài 3b)", CognitiveLevel.VAN_DUNG, 1.0),
            ("Số và Đại số", "Chương 6. Tìm tham số m để phương trình bậc hai có nghiệm thỏa mãn điều kiện (Bài 4)", CognitiveLevel.VAN_DUNG_CAO, 1.0),
        ]
        return ExamMatrix(
            id="matrix_9_gk2",
            title="ĐỀ KIỂM TRA GIỮA HỌC KỲ 2 - TOÁN 9",
            description="Theo SGK Kết nối tri thức: Chương 6 (Hàm số y = ax² và PT bậc hai), Chương 7 (Tần số và tần số tương đối)",
            subject="TOÁN HỌC",
            grade=9,
            semester="Giữa kỳ 2",
            time_minutes=90,
            academic_year="2026 - 2027",
            tags=["Lớp 9", "Giữa kỳ 2", "KNTT", "12 TN + 7 TL"],
            slots=_build_thcs_slots("m9_gk2", p1, p2)
        )

    @classmethod
    def get_matrix_9_ck2(cls) -> ExamMatrix:
        """Ma trận đề Cuối kì II - Toán 9 (Sát định dạng thi vào lớp 10)."""
        p1 = [
            ("Số và Đại số", "Chương 6. Hàm số y = ax² và tính đồng biến nghịch biến", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 6. Phương trình bậc hai một ẩn", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 6. Định lí Viète", CognitiveLevel.NHAN_BIET),
            ("Thống kê và Xác suất", "Chương 7. Tần số và tần số tương đối", CognitiveLevel.NHAN_BIET),
            ("Thống kê và Xác suất", "Chương 8. Không gian mẫu và biến cố", CognitiveLevel.NHAN_BIET),
            ("Hình học và Đo lường", "Chương 9. Góc ở tâm và góc nội tiếp đường tròn", CognitiveLevel.NHAN_BIET),
            ("Hình học và Đo lường", "Chương 9. Đường tròn ngoại tiếp và nội tiếp tam giác", CognitiveLevel.NHAN_BIET),
            ("Hình học và Đo lường", "Chương 10. Hình trụ, hình nón, hình cầu", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Chương 6. Tương giao Parabol và đường thẳng y = mx + n", CognitiveLevel.THONG_HIEU),
            ("Số và Đại số", "Chương 6. Bài toán lập phương trình bậc hai", CognitiveLevel.THONG_HIEU),
            ("Thống kê và Xác suất", "Chương 8. Tính xác suất của biến cố trong mô hình đơn giản", CognitiveLevel.THONG_HIEU),
            ("Hình học và Đo lường", "Chương 9. Tứ giác nội tiếp đường tròn và tính chất", CognitiveLevel.THONG_HIEU),
        ]
        p2 = [
            ("Số và Đại số", "Chương 6. Giải phương trình bậc hai và tìm tọa độ giao điểm (Bài 1a)", CognitiveLevel.NHAN_BIET, 1.0),
            ("Hình học và Đo lường", "Chương 9. Tính số đo cung và góc nội tiếp (Bài 1b)", CognitiveLevel.NHAN_BIET, 1.0),
            ("Số và Đại số", "Chương 6. Ứng dụng hệ thức Viète tìm m thỏa mãn đẳng thức (Bài 2a)", CognitiveLevel.THONG_HIEU, 1.0),
            ("Thống kê và Xác suất", "Chương 8. Tính xác suất biến cố (Bài 2b)", CognitiveLevel.THONG_HIEU, 1.0),
            ("Hình học và Đo lường", "Chương 9. Chứng minh tứ giác nội tiếp đường tròn (Bài 3a)", CognitiveLevel.VAN_DUNG, 1.0),
            ("Hình học và Đo lường", "Chương 10. Tính diện tích, thể tích hình trụ/nón/cầu thực tế (Bài 3b)", CognitiveLevel.VAN_DUNG, 1.0),
            ("Số và Đại số", "Chương 6. Bài toán cực trị đại số hoặc bất đẳng thức vào lớp 10 (Bài 4)", CognitiveLevel.VAN_DUNG_CAO, 1.0),
        ]
        return ExamMatrix(
            id="matrix_9_ck2",
            title="ĐỀ KIỂM TRA CUỐI HỌC KỲ 2 - TOÁN 9 (THI VÀO 10)",
            description="Bao quát toàn diện Chương 6 đến 10, cấu trúc chuẩn hóa cho kỳ thi tuyển sinh vào lớp 10 THPT",
            subject="TOÁN HỌC",
            grade=9,
            semester="Học kỳ 2",
            time_minutes=90,
            academic_year="2026 - 2027",
            tags=["Lớp 9", "Cuối kỳ 2", "Thi vào 10", "KNTT", "12 TN + 7 TL"],
            slots=_build_thcs_slots("m9_ck2", p1, p2)
        )

    # =========================================================================
    # LỚP 10 (THPT - 70% TN + 30% TL)
    # =========================================================================
    @classmethod
    def get_matrix_10_gk1(cls) -> ExamMatrix:
        """Ma trận đề Giữa kì I - Toán 10 (Chương 1, 2, 3)."""
        p1 = [
            ("Đại số và Giải tích", "Chương 1. Mệnh đề toán học", CognitiveLevel.NHAN_BIET),
            ("Đại số và Giải tích", "Chương 1. Tập hợp và các phép toán giao, hợp", CognitiveLevel.NHAN_BIET),
            ("Đại số và Giải tích", "Chương 1. Các tập hợp số", CognitiveLevel.NHAN_BIET),
            ("Đại số và Giải tích", "Chương 2. Bất phương trình bậc nhất hai ẩn", CognitiveLevel.NHAN_BIET),
            ("Đại số và Giải tích", "Chương 2. Biểu diễn miền nghiệm của bất phương trình bậc nhất hai ẩn", CognitiveLevel.NHAN_BIET),
            ("Đại số và Giải tích", "Chương 2. Hệ bất phương trình bậc nhất hai ẩn", CognitiveLevel.NHAN_BIET),
            ("Hình học và Đo lường", "Chương 3. Giá trị lượng giác của một góc từ 0 đến 180 độ", CognitiveLevel.NHAN_BIET),
            ("Hình học và Đo lường", "Chương 3. Định lí côsin trong tam giác", CognitiveLevel.NHAN_BIET),
            ("Đại số và Giải tích", "Chương 1. Các phép toán trên tập hợp con của R", CognitiveLevel.THONG_HIEU),
            ("Đại số và Giải tích", "Chương 2. Miền nghiệm của hệ bất phương trình bậc nhất hai ẩn", CognitiveLevel.THONG_HIEU),
            ("Đại số và Giải tích", "Chương 2. Bài toán tìm giá trị lớn nhất, nhỏ nhất trên miền đa giác", CognitiveLevel.THONG_HIEU),
            ("Hình học và Đo lường", "Chương 3. Định lí sin và công thức tính diện tích tam giác", CognitiveLevel.THONG_HIEU),
        ]
        p2 = [
            ("Đại số và Giải tích", "Chương 1. Phép toán tập hợp và điều kiện chứa tham số", CognitiveLevel.THONG_HIEU),
            ("Đại số và Giải tích", "Chương 2. Miền nghiệm hệ bất phương trình bậc nhất hai ẩn và ứng dụng thực tiễn", CognitiveLevel.THONG_HIEU),
            ("Hình học và Đo lường", "Chương 3. Giải tam giác và tính bán kính đường tròn ngoại tiếp, nội tiếp", CognitiveLevel.THONG_HIEU),
            ("Đại số và Giải tích", "Chương 2. Bài toán quy hoạch tuyến tính tối ưu hóa chi phí sản xuất", CognitiveLevel.VAN_DUNG),
        ]
        p3 = [
            ("Đại số và Giải tích", "Chương 1. Chứng minh mệnh đề và quan hệ tập hợp (Bài 1)", CognitiveLevel.NHAN_BIET),
            ("Hình học và Đo lường", "Chương 3. Ứng dụng giải tam giác vào bài toán đo đạc khoảng cách thực tế (Bài 2)", CognitiveLevel.VAN_DUNG),
            ("Đại số và Giải tích", "Chương 2. Bài toán tối ưu hóa hệ bất phương trình hai ẩn chứa tham số (Bài 3)", CognitiveLevel.VAN_DUNG_CAO),
        ]
        return ExamMatrix(
            id="matrix_10_gk1",
            title="ĐỀ KIỂM TRA GIỮA HỌC KỲ 1 - TOÁN 10",
            description="Theo SGK Kết nối tri thức: Chương 1 (Mệnh đề, tập hợp), Chương 2 (BPT & hệ BPT bậc nhất hai ẩn), Chương 3 (Hệ thức lượng tam giác)",
            subject="TOÁN HỌC",
            grade=10,
            semester="Giữa kỳ 1",
            time_minutes=90,
            academic_year="2026 - 2027",
            tags=["Lớp 10", "Giữa kỳ 1", "KNTT", "12 TN + 4 Đ/S + 3 TL"],
            slots=_build_thpt_10_11_slots("m10_gk1", p1, p2, p3)
        )

    @classmethod
    def get_matrix_10_ck1(cls) -> ExamMatrix:
        """Ma trận đề Cuối kì I - Toán 10 (Chương 1 đến Chương 5)."""
        p1 = [
            ("Đại số và Giải tích", "Chương 1. Mệnh đề và tập hợp", CognitiveLevel.NHAN_BIET),
            ("Đại số và Giải tích", "Chương 2. Bất phương trình bậc nhất hai ẩn", CognitiveLevel.NHAN_BIET),
            ("Đại số và Giải tích", "Chương 2. Hệ bất phương trình bậc nhất hai ẩn", CognitiveLevel.NHAN_BIET),
            ("Hình học và Đo lường", "Chương 3. Định lí côsin và định lí sin", CognitiveLevel.NHAN_BIET),
            ("Hình học và Đo lường", "Chương 3. Các công thức tính diện tích tam giác", CognitiveLevel.NHAN_BIET),
            ("Hình học và Đo lường", "Chương 4. Khái niệm vectơ, hai vectơ cùng phương", CognitiveLevel.NHAN_BIET),
            ("Hình học và Đo lường", "Chương 4. Tổng và hiệu của hai vectơ", CognitiveLevel.NHAN_BIET),
            ("Thống kê và Xác suất", "Chương 5. Số gần đúng và sai số", CognitiveLevel.NHAN_BIET),
            ("Đại số và Giải tích", "Chương 2. Bài toán thực tiễn hệ bất phương trình", CognitiveLevel.THONG_HIEU),
            ("Hình học và Đo lường", "Chương 3. Giải tam giác thực tế", CognitiveLevel.THONG_HIEU),
            ("Hình học và Đo lường", "Chương 4. Tích của một số với một vectơ, tích vô hướng", CognitiveLevel.THONG_HIEU),
            ("Thống kê và Xác suất", "Chương 5. Các số đặc trưng đo xu thế trung tâm (số trung bình, trung vị, tứ phân vị, mốt)", CognitiveLevel.THONG_HIEU),
        ]
        p2 = [
            ("Đại số và Giải tích", "Chương 1 & 2. Mệnh đề, tập hợp và miền nghiệm hệ BPT", CognitiveLevel.THONG_HIEU),
            ("Hình học và Đo lường", "Chương 3. Hệ thức lượng trong tam giác và bán kính đường tròn", CognitiveLevel.THONG_HIEU),
            ("Hình học và Đo lường", "Chương 4. Phân tích vectơ, tính góc giữa hai vectơ và tích vô hướng", CognitiveLevel.THONG_HIEU),
            ("Thống kê và Xác suất", "Chương 5. Khoảng biến thiên, khoảng tứ phân vị và độ lệch chuẩn", CognitiveLevel.VAN_DUNG),
        ]
        p3 = [
            ("Đại số và Giải tích", "Chương 1. Xác định tập hợp và phép toán giao hợp (Bài 1)", CognitiveLevel.NHAN_BIET),
            ("Hình học và Đo lường", "Chương 4. Chứng minh hệ thức vectơ hoặc tính tích vô hướng (Bài 2)", CognitiveLevel.VAN_DUNG),
            ("Hình học và Đo lường", "Chương 3. Bài toán thực tế giải tam giác kết hợp vectơ nâng cao (Bài 3)", CognitiveLevel.VAN_DUNG_CAO),
        ]
        return ExamMatrix(
            id="matrix_10_ck1",
            title="ĐỀ KIỂM TRA CUỐI HỌC KỲ 1 - TOÁN 10",
            description="Bao quát Chương 1 đến Chương 5 (Mệnh đề tập hợp, Hệ BPT, Lượng giác tam giác, Vectơ, Số đặc trưng thống kê)",
            subject="TOÁN HỌC",
            grade=10,
            semester="Học kỳ 1",
            time_minutes=90,
            academic_year="2026 - 2027",
            tags=["Lớp 10", "Cuối kỳ 1", "KNTT", "12 TN + 4 Đ/S + 3 TL"],
            slots=_build_thpt_10_11_slots("m10_ck1", p1, p2, p3)
        )

    @classmethod
    def get_matrix_10_gk2(cls) -> ExamMatrix:
        """Ma trận đề Giữa kì II - Toán 10 (Chương 6 Hàm số, Chương 7 Phương pháp tọa độ Oxy)."""
        p1 = [
            ("Đại số và Giải tích", "Chương 6. Khái niệm hàm số và tập xác định", CognitiveLevel.NHAN_BIET),
            ("Đại số và Giải tích", "Chương 6. Hàm số bậc hai, tọa độ đỉnh parabol", CognitiveLevel.NHAN_BIET),
            ("Đại số và Giải tích", "Chương 6. Trục đối xứng của parabol", CognitiveLevel.NHAN_BIET),
            ("Đại số và Giải tích", "Chương 6. Dấu của tam thức bậc hai", CognitiveLevel.NHAN_BIET),
            ("Đại số và Giải tích", "Chương 6. Bất phương trình bậc hai một ẩn", CognitiveLevel.NHAN_BIET),
            ("Đại số và Giải tích", "Chương 6. Phương trình quy về phương trình bậc hai", CognitiveLevel.NHAN_BIET),
            ("Hình học và Đo lường", "Chương 7. Tọa độ của vectơ trong mặt phẳng Oxy", CognitiveLevel.NHAN_BIET),
            ("Hình học và Đo lường", "Chương 7. Tọa độ của điểm và các phép toán vectơ", CognitiveLevel.NHAN_BIET),
            ("Đại số và Giải tích", "Chương 6. Vẽ đồ thị hàm số bậc hai và khảo sát tính biến thiên", CognitiveLevel.THONG_HIEU),
            ("Đại số và Giải tích", "Chương 6. Giải bất phương trình bậc hai một ẩn", CognitiveLevel.THONG_HIEU),
            ("Đại số và Giải tích", "Chương 6. Phương trình chứa căn dạng căn A = B hoặc căn A = căn B", CognitiveLevel.THONG_HIEU),
            ("Hình học và Đo lường", "Chương 7. Phương trình tổng quát và tham số của đường thẳng", CognitiveLevel.THONG_HIEU),
        ]
        p2 = [
            ("Đại số và Giải tích", "Chương 6. Khảo sát hàm số bậc hai và tương giao đồ thị", CognitiveLevel.THONG_HIEU),
            ("Đại số và Giải tích", "Chương 6. Bất phương trình bậc hai chứa tham số m", CognitiveLevel.THONG_HIEU),
            ("Hình học và Đo lường", "Chương 7. Vị trí tương đối của hai đường thẳng, góc và khoảng cách", CognitiveLevel.THONG_HIEU),
            ("Đại số và Giải tích", "Chương 6. Bài toán thực tiễn tối ưu hóa liên quan đến parabol", CognitiveLevel.VAN_DUNG),
        ]
        p3 = [
            ("Đại số và Giải tích", "Chương 6. Tìm tập xác định của hàm số chứa căn và mẫu (Bài 1)", CognitiveLevel.NHAN_BIET),
            ("Hình học và Đo lường", "Chương 7. Viết phương trình đường thẳng và tính khoảng cách (Bài 2)", CognitiveLevel.VAN_DUNG),
            ("Đại số và Giải tích", "Chương 6. Giải phương trình chứa căn thức hoặc bất phương trình tham số nâng cao (Bài 3)", CognitiveLevel.VAN_DUNG_CAO),
        ]
        return ExamMatrix(
            id="matrix_10_gk2",
            title="ĐỀ KIỂM TRA GIỮA HỌC KỲ 2 - TOÁN 10",
            description="Theo SGK Kết nối tri thức: Chương 6 (Hàm số, đồ thị & ứng dụng), Chương 7 (Phương pháp tọa độ Oxy)",
            subject="TOÁN HỌC",
            grade=10,
            semester="Giữa kỳ 2",
            time_minutes=90,
            academic_year="2026 - 2027",
            tags=["Lớp 10", "Giữa kỳ 2", "KNTT", "12 TN + 4 Đ/S + 3 TL"],
            slots=_build_thpt_10_11_slots("m10_gk2", p1, p2, p3)
        )

    @classmethod
    def get_matrix_10_ck2(cls) -> ExamMatrix:
        """Ma trận đề Cuối kì II - Toán 10 (Chương 6 đến Chương 9)."""
        p1 = [
            ("Đại số và Giải tích", "Chương 6. Hàm số bậc hai và tam thức bậc hai", CognitiveLevel.NHAN_BIET),
            ("Hình học và Đo lường", "Chương 7. Phương trình đường thẳng trong Oxy", CognitiveLevel.NHAN_BIET),
            ("Hình học và Đo lường", "Chương 7. Phương trình đường tròn và tâm, bán kính", CognitiveLevel.NHAN_BIET),
            ("Hình học và Đo lường", "Chương 7. Ba đường conic (elip, hypebol, parabol)", CognitiveLevel.NHAN_BIET),
            ("Thống kê và Xác suất", "Chương 8. Quy tắc cộng và quy tắc nhân", CognitiveLevel.NHAN_BIET),
            ("Thống kê và Xác suất", "Chương 8. Hoán vị, chỉnh hợp, tổ hợp", CognitiveLevel.NHAN_BIET),
            ("Thống kê và Xác suất", "Chương 9. Phép thử ngẫu nhiên và không gian mẫu", CognitiveLevel.NHAN_BIET),
            ("Thống kê và Xác suất", "Chương 9. Biến cố và xác suất của biến cố", CognitiveLevel.NHAN_BIET),
            ("Đại số và Giải tích", "Chương 6. Giải phương trình quy về bậc hai", CognitiveLevel.THONG_HIEU),
            ("Hình học và Đo lường", "Chương 7. Viết phương trình tiếp tuyến của đường tròn", CognitiveLevel.THONG_HIEU),
            ("Thống kê và Xác suất", "Chương 8. Khai triển nhị thức Newton với số mũ nhỏ", CognitiveLevel.THONG_HIEU),
            ("Thống kê và Xác suất", "Chương 9. Tính xác suất bằng sơ đồ cây hoặc tổ hợp", CognitiveLevel.THONG_HIEU),
        ]
        p2 = [
            ("Đại số và Giải tích", "Chương 6. Tam thức bậc hai và bài toán thực tế", CognitiveLevel.THONG_HIEU),
            ("Hình học và Đo lường", "Chương 7. Phương trình đường tròn và vị trí tương đối", CognitiveLevel.THONG_HIEU),
            ("Thống kê và Xác suất", "Chương 8. Bài toán đếm tổ hợp và nhị thức Newton", CognitiveLevel.THONG_HIEU),
            ("Thống kê và Xác suất", "Chương 9. Bài toán xác suất cổ điển nâng cao", CognitiveLevel.VAN_DUNG),
        ]
        p3 = [
            ("Đại số và Giải tích", "Chương 6. Giải bất phương trình bậc hai một ẩn (Bài 1)", CognitiveLevel.NHAN_BIET),
            ("Thống kê và Xác suất", "Chương 8. Bài toán đếm hoặc tính hệ số trong nhị thức Newton (Bài 2)", CognitiveLevel.VAN_DUNG),
            ("Hình học và Đo lường", "Chương 7. Viết phương trình đường tròn hoặc đường conic trong bài toán thực tế (Bài 3)", CognitiveLevel.VAN_DUNG_CAO),
        ]
        return ExamMatrix(
            id="matrix_10_ck2",
            title="ĐỀ KIỂM TRA CUỐI HỌC KỲ 2 - TOÁN 10",
            description="Bao quát Chương 6 đến Chương 9 (Hàm số bậc hai, Tọa độ Oxy & Conic, Đại số tổ hợp, Xác suất cổ điển)",
            subject="TOÁN HỌC",
            grade=10,
            semester="Học kỳ 2",
            time_minutes=90,
            academic_year="2026 - 2027",
            tags=["Lớp 10", "Cuối kỳ 2", "KNTT", "12 TN + 4 Đ/S + 3 TL"],
            slots=_build_thpt_10_11_slots("m10_ck2", p1, p2, p3)
        )

    # =========================================================================
    # LỚP 11 (THPT - 70% TN + 30% TL)
    # =========================================================================
    @classmethod
    def get_matrix_11_gk1(cls) -> ExamMatrix:
        """Ma trận đề Giữa kì I - Toán 11 (Chương 1 Lượng giác, Chương 2 Cấp số)."""
        p1 = [
            ("Đại số và Giải tích", "Chương 1. Góc lượng giác và đơn vị radian", CognitiveLevel.NHAN_BIET),
            ("Đại số và Giải tích", "Chương 1. Giá trị lượng giác của góc lượng giác", CognitiveLevel.NHAN_BIET),
            ("Đại số và Giải tích", "Chương 1. Các công thức lượng giác cơ bản", CognitiveLevel.NHAN_BIET),
            ("Đại số và Giải tích", "Chương 1. Tập xác định và tập giá trị của hàm số lượng giác", CognitiveLevel.NHAN_BIET),
            ("Đại số và Giải tích", "Chương 2. Khái niệm dãy số, số hạng tổng quát", CognitiveLevel.NHAN_BIET),
            ("Đại số và Giải tích", "Chương 2. Dãy số tăng, dãy số giảm", CognitiveLevel.NHAN_BIET),
            ("Đại số và Giải tích", "Chương 2. Định nghĩa cấp số cộng và công sai", CognitiveLevel.NHAN_BIET),
            ("Đại số và Giải tích", "Chương 2. Định nghĩa cấp số nhân và công bội", CognitiveLevel.NHAN_BIET),
            ("Đại số và Giải tích", "Chương 1. Công thức cộng, công thức nhân đôi", CognitiveLevel.THONG_HIEU),
            ("Đại số và Giải tích", "Chương 1. Phương trình lượng giác cơ bản sin x = m, cos x = m", CognitiveLevel.THONG_HIEU),
            ("Đại số và Giải tích", "Chương 2. Số hạng tổng quát và tổng n số hạng đầu của cấp số cộng", CognitiveLevel.THONG_HIEU),
            ("Đại số và Giải tích", "Chương 2. Số hạng tổng quát và tổng n số hạng đầu của cấp số nhân", CognitiveLevel.THONG_HIEU),
        ]
        p2 = [
            ("Đại số và Giải tích", "Chương 1. Rút gọn biểu thức lượng giác và giải phương trình", CognitiveLevel.THONG_HIEU),
            ("Đại số và Giải tích", "Chương 1. Khảo sát tính tuần hoàn và đồ thị hàm số lượng giác", CognitiveLevel.THONG_HIEU),
            ("Đại số và Giải tích", "Chương 2. Dãy số và bài toán cấp số cộng", CognitiveLevel.THONG_HIEU),
            ("Đại số và Giải tích", "Chương 2. Cấp số nhân và bài toán thực tế tăng trưởng/lãi suất", CognitiveLevel.VAN_DUNG),
        ]
        p3 = [
            ("Đại số và Giải tích", "Chương 1. Giải phương trình lượng giác cơ bản (Bài 1)", CognitiveLevel.NHAN_BIET),
            ("Đại số và Giải tích", "Chương 2. Bài toán thực tiễn về cấp số cộng hoặc cấp số nhân (Bài 2)", CognitiveLevel.VAN_DUNG),
            ("Đại số và Giải tích", "Chương 1. Phương trình lượng giác có nghiệm thuộc khoảng hoặc điều kiện tham số (Bài 3)", CognitiveLevel.VAN_DUNG_CAO),
        ]
        return ExamMatrix(
            id="matrix_11_gk1",
            title="ĐỀ KIỂM TRA GIỮA HỌC KỲ 1 - TOÁN 11",
            description="Theo SGK Kết nối tri thức: Chương 1 (Hàm số & phương trình lượng giác), Chương 2 (Dãy số, Cấp số cộng & Cấp số nhân)",
            subject="TOÁN HỌC",
            grade=11,
            semester="Giữa kỳ 1",
            time_minutes=90,
            academic_year="2026 - 2027",
            tags=["Lớp 11", "Giữa kỳ 1", "KNTT", "12 TN + 4 Đ/S + 3 TL"],
            slots=_build_thpt_10_11_slots("m11_gk1", p1, p2, p3)
        )

    @classmethod
    def get_matrix_11_ck1(cls) -> ExamMatrix:
        """Ma trận đề Cuối kì I - Toán 11 (Chương 1 đến Chương 4)."""
        p1 = [
            ("Đại số và Giải tích", "Chương 1. Hàm số lượng giác và phương trình lượng giác", CognitiveLevel.NHAN_BIET),
            ("Đại số và Giải tích", "Chương 1. Chu kì và đồ thị hàm số lượng giác", CognitiveLevel.NHAN_BIET),
            ("Đại số và Giải tích", "Chương 2. Cấp số cộng và cấp số nhân", CognitiveLevel.NHAN_BIET),
            ("Đại số và Giải tích", "Chương 2. Dãy số bị chặn", CognitiveLevel.NHAN_BIET),
            ("Thống kê và Xác suất", "Chương 3. Mẫu số liệu ghép nhóm và bảng tần số", CognitiveLevel.NHAN_BIET),
            ("Thống kê và Xác suất", "Chương 3. Khoảng biến thiên và khoảng tứ phân vị mẫu ghép nhóm", CognitiveLevel.NHAN_BIET),
            ("Hình học và Đo lường", "Chương 4. Điểm, đường thẳng và mặt phẳng trong không gian", CognitiveLevel.NHAN_BIET),
            ("Hình học và Đo lường", "Chương 4. Hai đường thẳng song song trong không gian", CognitiveLevel.NHAN_BIET),
            ("Đại số và Giải tích", "Chương 1. Phương trình lượng giác quy về bậc nhất hoặc bậc hai", CognitiveLevel.THONG_HIEU),
            ("Đại số và Giải tích", "Chương 2. Bài toán thực tế về cấp số", CognitiveLevel.THONG_HIEU),
            ("Hình học và Đo lường", "Chương 4. Đường thẳng song song với mặt phẳng", CognitiveLevel.THONG_HIEU),
            ("Hình học và Đo lường", "Chương 4. Hai mặt phẳng song song và hình hộp", CognitiveLevel.THONG_HIEU),
        ]
        p2 = [
            ("Đại số và Giải tích", "Chương 1. Phương trình lượng giác và nghiệm thuộc khoảng", CognitiveLevel.THONG_HIEU),
            ("Đại số và Giải tích", "Chương 2. Dãy số, cấp số cộng và cấp số nhân", CognitiveLevel.THONG_HIEU),
            ("Thống kê và Xác suất", "Chương 3. Số đặc trưng đo độ phân tán của mẫu ghép nhóm", CognitiveLevel.THONG_HIEU),
            ("Hình học và Đo lường", "Chương 4. Thiết diện và quan hệ song song trong không gian", CognitiveLevel.VAN_DUNG),
        ]
        p3 = [
            ("Đại số và Giải tích", "Chương 1. Giải phương trình lượng giác (Bài 1)", CognitiveLevel.NHAN_BIET),
            ("Hình học và Đo lường", "Chương 4. Tìm giao tuyến và xác định thiết diện song song (Bài 2)", CognitiveLevel.VAN_DUNG),
            ("Đại số và Giải tích", "Chương 2. Bài toán cấp số cộng, cấp số nhân nâng cao hoặc giới hạn dãy số (Bài 3)", CognitiveLevel.VAN_DUNG_CAO),
        ]
        return ExamMatrix(
            id="matrix_11_ck1",
            title="ĐỀ KIỂM TRA CUỐI HỌC KỲ 1 - TOÁN 11",
            description="Bao quát Chương 1 đến Chương 4 (Lượng giác, Cấp số, Thống kê ghép nhóm, Quan hệ song song không gian)",
            subject="TOÁN HỌC",
            grade=11,
            semester="Học kỳ 1",
            time_minutes=90,
            academic_year="2026 - 2027",
            tags=["Lớp 11", "Cuối kỳ 1", "KNTT", "12 TN + 4 Đ/S + 3 TL"],
            slots=_build_thpt_10_11_slots("m11_ck1", p1, p2, p3)
        )

    @classmethod
    def get_matrix_11_gk2(cls) -> ExamMatrix:
        """Ma trận đề Giữa kì II - Toán 11 (Chương 5 Giới hạn, Chương 6 Mũ & Lôgarit)."""
        p1 = [
            ("Đại số và Giải tích", "Chương 5. Giới hạn của dãy số", CognitiveLevel.NHAN_BIET),
            ("Đại số và Giải tích", "Chương 5. Giới hạn hữu hạn của hàm số tại một điểm", CognitiveLevel.NHAN_BIET),
            ("Đại số và Giải tích", "Chương 5. Giới hạn tại vô cực", CognitiveLevel.NHAN_BIET),
            ("Đại số và Giải tích", "Chương 5. Khái niệm hàm số liên tục", CognitiveLevel.NHAN_BIET),
            ("Đại số và Giải tích", "Chương 6. Phép tính lũy thừa với số mũ thực", CognitiveLevel.NHAN_BIET),
            ("Đại số và Giải tích", "Chương 6. Khái niệm và tính chất của lôgarit", CognitiveLevel.NHAN_BIET),
            ("Đại số và Giải tích", "Chương 6. Hàm số mũ y = a^x", CognitiveLevel.NHAN_BIET),
            ("Đại số và Giải tích", "Chương 6. Hàm số lôgarit y = log_a(x)", CognitiveLevel.NHAN_BIET),
            ("Đại số và Giải tích", "Chương 5. Tính giới hạn dạng 0/0 hoặc vô cùng trừ vô cùng", CognitiveLevel.THONG_HIEU),
            ("Đại số và Giải tích", "Chương 5. Xét tính liên tục của hàm số tại một điểm", CognitiveLevel.THONG_HIEU),
            ("Đại số và Giải tích", "Chương 6. Phương trình mũ cơ bản", CognitiveLevel.THONG_HIEU),
            ("Đại số và Giải tích", "Chương 6. Phương trình lôgarit cơ bản", CognitiveLevel.THONG_HIEU),
        ]
        p2 = [
            ("Đại số và Giải tích", "Chương 5. Giới hạn hàm số và ứng dụng định lí giá trị trung gian", CognitiveLevel.THONG_HIEU),
            ("Đại số và Giải tích", "Chương 5. Tính liên tục của hàm số trên một khoảng", CognitiveLevel.THONG_HIEU),
            ("Đại số và Giải tích", "Chương 6. Biến đổi biểu thức lũy thừa và lôgarit", CognitiveLevel.THONG_HIEU),
            ("Đại số và Giải tích", "Chương 6. Bất phương trình mũ và lôgarit, bài toán lãi kép thực tiễn", CognitiveLevel.VAN_DUNG),
        ]
        p3 = [
            ("Đại số và Giải tích", "Chương 5. Tính giới hạn hàm số dạng 0/0 khử dạng vô định (Bài 1)", CognitiveLevel.NHAN_BIET),
            ("Đại số và Giải tích", "Chương 6. Giải phương trình mũ hoặc lôgarit đặt ẩn phụ (Bài 2)", CognitiveLevel.VAN_DUNG),
            ("Đại số và Giải tích", "Chương 6. Bài toán thực tế về mô hình tăng trưởng dân số / phân rã phóng xạ (Bài 3)", CognitiveLevel.VAN_DUNG_CAO),
        ]
        return ExamMatrix(
            id="matrix_11_gk2",
            title="ĐỀ KIỂM TRA GIỮA HỌC KỲ 2 - TOÁN 11",
            description="Theo SGK Kết nối tri thức: Chương 5 (Giới hạn, Hàm số liên tục), Chương 6 (Hàm số mũ và hàm số lôgarit)",
            subject="TOÁN HỌC",
            grade=11,
            semester="Giữa kỳ 2",
            time_minutes=90,
            academic_year="2026 - 2027",
            tags=["Lớp 11", "Giữa kỳ 2", "KNTT", "12 TN + 4 Đ/S + 3 TL"],
            slots=_build_thpt_10_11_slots("m11_gk2", p1, p2, p3)
        )

    @classmethod
    def get_matrix_11_ck2(cls) -> ExamMatrix:
        """Ma trận đề Cuối kì II - Toán 11 (Chương 5 đến Chương 9)."""
        p1 = [
            ("Đại số và Giải tích", "Chương 5. Giới hạn và hàm số liên tục", CognitiveLevel.NHAN_BIET),
            ("Đại số và Giải tích", "Chương 6. Hàm số mũ và hàm số lôgarit", CognitiveLevel.NHAN_BIET),
            ("Hình học và Đo lường", "Chương 7. Hai đường thẳng vuông góc trong không gian", CognitiveLevel.NHAN_BIET),
            ("Hình học và Đo lường", "Chương 7. Đường thẳng vuông góc với mặt phẳng", CognitiveLevel.NHAN_BIET),
            ("Hình học và Đo lường", "Chương 7. Hai mặt phẳng vuông góc", CognitiveLevel.NHAN_BIET),
            ("Thống kê và Xác suất", "Chương 8. Biến cố giao và biến cố hợp", CognitiveLevel.NHAN_BIET),
            ("Đại số và Giải tích", "Chương 9. Định nghĩa đạo hàm tại một điểm", CognitiveLevel.NHAN_BIET),
            ("Đại số và Giải tích", "Chương 9. Đạo hàm của hàm số lượng giác, mũ, lôgarit", CognitiveLevel.NHAN_BIET),
            ("Đại số và Giải tích", "Chương 6. Phương trình và bất phương trình mũ, lôgarit", CognitiveLevel.THONG_HIEU),
            ("Hình học và Đo lường", "Chương 7. Khoảng cách từ điểm đến mặt phẳng, khoảng cách giữa hai đường chéo nhau", CognitiveLevel.THONG_HIEU),
            ("Thống kê và Xác suất", "Chương 8. Công thức cộng và công thức nhân xác suất", CognitiveLevel.THONG_HIEU),
            ("Đại số và Giải tích", "Chương 9. Quy tắc tính đạo hàm và phương trình tiếp tuyến của đồ thị", CognitiveLevel.THONG_HIEU),
        ]
        p2 = [
            ("Đại số và Giải tích", "Chương 6. Phương trình, bất phương trình mũ và lôgarit", CognitiveLevel.THONG_HIEU),
            ("Hình học và Đo lường", "Chương 7. Quan hệ vuông góc và góc giữa đường thẳng và mặt phẳng", CognitiveLevel.THONG_HIEU),
            ("Thống kê và Xác suất", "Chương 8. Biến cố độc lập và quy tắc nhân xác suất", CognitiveLevel.THONG_HIEU),
            ("Đại số và Giải tích", "Chương 9. Đạo hàm cấp hai, ý nghĩa hình học và vật lí", CognitiveLevel.VAN_DUNG),
        ]
        p3 = [
            ("Đại số và Giải tích", "Chương 9. Viết phương trình tiếp tuyến của đồ thị hàm số tại điểm (Bài 1)", CognitiveLevel.NHAN_BIET),
            ("Hình học và Đo lường", "Chương 7. Tính khoảng cách từ điểm đến mặt phẳng trong hình chóp (Bài 2)", CognitiveLevel.VAN_DUNG),
            ("Thống kê và Xác suất", "Chương 8. Bài toán tính xác suất biến cố thực tế nâng cao (Bài 3)", CognitiveLevel.VAN_DUNG_CAO),
        ]
        return ExamMatrix(
            id="matrix_11_ck2",
            title="ĐỀ KIỂM TRA CUỐI HỌC KỲ 2 - TOÁN 11",
            description="Bao quát Chương 5 đến Chương 9 (Giới hạn, Mũ & Lôgarit, Quan hệ vuông góc, Xác suất, Đạo hàm)",
            subject="TOÁN HỌC",
            grade=11,
            semester="Học kỳ 2",
            time_minutes=90,
            academic_year="2026 - 2027",
            tags=["Lớp 11", "Cuối kỳ 2", "KNTT", "12 TN + 4 Đ/S + 3 TL"],
            slots=_build_thpt_10_11_slots("m11_ck2", p1, p2, p3)
        )

    # =========================================================================
    # LỚP 12 (THPT - 22 CÂU: 12 TN + 4 Đ/S + 6 TLN)
    # =========================================================================
    @classmethod
    def get_matrix_12_gk1(cls) -> ExamMatrix:
        """Ma trận đề Giữa kì I - Toán 12 (Chương 1 Ứng dụng đạo hàm khảo sát hàm số)."""
        p1 = [
            ("Đại số và Giải tích", "Chương 1. Tính đơn điệu của hàm số", CognitiveLevel.NHAN_BIET),
            ("Đại số và Giải tích", "Chương 1. Cực trị của hàm số", CognitiveLevel.NHAN_BIET),
            ("Đại số và Giải tích", "Chương 1. Giá trị lớn nhất, giá trị nhỏ nhất trên đoạn", CognitiveLevel.NHAN_BIET),
            ("Đại số và Giải tích", "Chương 1. Đường tiệm cận đứng, tiệm cận ngang", CognitiveLevel.NHAN_BIET),
            ("Đại số và Giải tích", "Chương 1. Đường tiệm cận xiên của đồ thị hàm số", CognitiveLevel.NHAN_BIET),
            ("Đại số và Giải tích", "Chương 1. Nhận dạng bảng biến thiên hàm số", CognitiveLevel.NHAN_BIET),
            ("Đại số và Giải tích", "Chương 1. Nhận dạng đồ thị hàm phân thức hữu tỉ", CognitiveLevel.NHAN_BIET),
            ("Đại số và Giải tích", "Chương 1. Tính đơn điệu của hàm số chứa tham số", CognitiveLevel.NHAN_BIET),
            ("Đại số và Giải tích", "Chương 1. Khoảng đơn điệu của hàm số hợp", CognitiveLevel.THONG_HIEU),
            ("Đại số và Giải tích", "Chương 1. Cực trị hàm đa thức bậc ba", CognitiveLevel.THONG_HIEU),
            ("Đại số và Giải tích", "Chương 1. Giá trị lớn nhất, nhỏ nhất trên một khoảng", CognitiveLevel.THONG_HIEU),
            ("Đại số và Giải tích", "Chương 1. Tìm tiệm cận của đồ thị hàm số", CognitiveLevel.THONG_HIEU),
        ]
        p2 = [
            ("Đại số và Giải tích", "Chương 1. Tính đơn điệu toàn diện của hàm số", CognitiveLevel.NHAN_BIET),
            ("Đại số và Giải tích", "Chương 1. Khảo sát cực trị và tính lồi lõm của đồ thị", CognitiveLevel.THONG_HIEU),
            ("Đại số và Giải tích", "Chương 1. Đường tiệm cận và tâm đối xứng của đồ thị", CognitiveLevel.THONG_HIEU),
            ("Đại số và Giải tích", "Chương 1. Khảo sát toàn diện sự biến thiên và đồ thị", CognitiveLevel.VAN_DUNG),
        ]
        p3 = [
            ("Đại số và Giải tích", "Chương 1. Điểm cực trị của hàm số", CognitiveLevel.THONG_HIEU),
            ("Đại số và Giải tích", "Chương 1. Giá trị lớn nhất của hàm số trên đoạn", CognitiveLevel.VAN_DUNG),
            ("Đại số và Giải tích", "Chương 1. Bài toán tối ưu hóa thực tiễn (chi phí, diện tích)", CognitiveLevel.VAN_DUNG),
            ("Đại số và Giải tích", "Chương 1. Đường tiệm cận xiên chứa tham số", CognitiveLevel.VAN_DUNG),
            ("Đại số và Giải tích", "Chương 1. Cực trị hàm số có tham số m", CognitiveLevel.VAN_DUNG_CAO),
            ("Đại số và Giải tích", "Chương 1. Bài toán thực tiễn tối ưu hóa thể tích hình học", CognitiveLevel.VAN_DUNG_CAO),
        ]
        return ExamMatrix(
            id="matrix_12_gk1",
            title="ĐỀ KIỂM TRA GIỮA HỌC KỲ 1 - TOÁN 12",
            description="Theo SGK Kết nối tri thức: Chương 1 (Ứng dụng đạo hàm để khảo sát và vẽ đồ thị hàm số)",
            subject="TOÁN HỌC",
            grade=12,
            semester="Giữa kỳ 1",
            time_minutes=90,
            academic_year="2026 - 2027",
            tags=["Lớp 12", "Giữa kỳ 1", "KNTT", "22 câu", "TN THPT format"],
            slots=_build_thpt_12_slots("m12_gk1", p1, p2, p3)
        )

    @classmethod
    def get_matrix_12_ck1(cls) -> ExamMatrix:
        """Ma trận đề Cuối kì I - Toán 12 (Chương 1 đến Chương 3)."""
        p1 = [
            ("Đại số và Giải tích", "Chương 1. Đơn điệu và cực trị hàm số", CognitiveLevel.NHAN_BIET),
            ("Đại số và Giải tích", "Chương 1. Giá trị lớn nhất, nhỏ nhất trên đoạn", CognitiveLevel.NHAN_BIET),
            ("Đại số và Giải tích", "Chương 1. Tiệm cận của đồ thị hàm số", CognitiveLevel.NHAN_BIET),
            ("Đại số và Giải tích", "Chương 1. Nhận dạng đồ thị hàm số", CognitiveLevel.NHAN_BIET),
            ("Hình học và Đo lường", "Chương 2. Vectơ trong không gian và các phép toán", CognitiveLevel.NHAN_BIET),
            ("Hình học và Đo lường", "Chương 2. Tọa độ của điểm trong hệ Oxyz", CognitiveLevel.NHAN_BIET),
            ("Hình học và Đo lường", "Chương 2. Tọa độ của vectơ trong hệ Oxyz", CognitiveLevel.NHAN_BIET),
            ("Thống kê và Xác suất", "Chương 3. Mẫu số liệu ghép nhóm và khoảng biến thiên", CognitiveLevel.NHAN_BIET),
            ("Đại số và Giải tích", "Chương 1. Tương giao đồ thị hàm số", CognitiveLevel.THONG_HIEU),
            ("Hình học và Đo lường", "Chương 2. Tích vô hướng của hai vectơ trong Oxyz", CognitiveLevel.THONG_HIEU),
            ("Hình học và Đo lường", "Chương 2. Góc giữa hai vectơ trong không gian Oxyz", CognitiveLevel.THONG_HIEU),
            ("Thống kê và Xác suất", "Chương 3. Phương sai và độ lệch chuẩn của mẫu ghép nhóm", CognitiveLevel.THONG_HIEU),
        ]
        p2 = [
            ("Đại số và Giải tích", "Chương 1. Khảo sát toàn diện hàm số bậc ba hoặc hàm phân thức", CognitiveLevel.NHAN_BIET),
            ("Đại số và Giải tích", "Chương 1. Tiệm cận và tâm đối xứng của đồ thị", CognitiveLevel.THONG_HIEU),
            ("Hình học và Đo lường", "Chương 2. Tọa độ điểm, trung điểm và trọng tâm trong Oxyz", CognitiveLevel.THONG_HIEU),
            ("Thống kê và Xác suất", "Chương 3. So sánh độ phân tán của hai mẫu số liệu ghép nhóm", CognitiveLevel.VAN_DUNG),
        ]
        p3 = [
            ("Hình học và Đo lường", "Chương 2. Độ dài vectơ trong hệ Oxyz", CognitiveLevel.THONG_HIEU),
            ("Đại số và Giải tích", "Chương 1. Giá trị lớn nhất trong bài toán thực tế", CognitiveLevel.VAN_DUNG),
            ("Đại số và Giải tích", "Chương 1. Tối ưu hóa chi phí sản xuất", CognitiveLevel.VAN_DUNG),
            ("Hình học và Đo lường", "Chương 2. Tọa độ điểm thỏa mãn hệ thức vectơ", CognitiveLevel.VAN_DUNG),
            ("Đại số và Giải tích", "Chương 1. Hàm số chứa tham số m đơn điệu trên khoảng", CognitiveLevel.VAN_DUNG_CAO),
            ("Hình học và Đo lường", "Chương 2. Gắn hệ trục Oxyz vào mô hình công trình thực tế", CognitiveLevel.VAN_DUNG_CAO),
        ]
        return ExamMatrix(
            id="matrix_12_ck1",
            title="ĐỀ KIỂM TRA CUỐI HỌC KỲ 1 - TOÁN 12",
            description="Bao quát Chương 1 đến Chương 3 (Ứng dụng đạo hàm, Hệ tọa độ Oxyz, Thống kê đo độ phân tán)",
            subject="TOÁN HỌC",
            grade=12,
            semester="Học kỳ 1",
            time_minutes=90,
            academic_year="2026 - 2027",
            tags=["Lớp 12", "Cuối kỳ 1", "KNTT", "22 câu", "TN THPT format"],
            slots=_build_thpt_12_slots("m12_ck1", p1, p2, p3)
        )

    @classmethod
    def get_matrix_12_gk2(cls) -> ExamMatrix:
        """Ma trận đề Giữa kì II - Toán 12 (Chương 4 Nguyên hàm và tích phân)."""
        p1 = [
            ("Đại số và Giải tích", "Chương 4. Định nghĩa nguyên hàm và tính chất", CognitiveLevel.NHAN_BIET),
            ("Đại số và Giải tích", "Chương 4. Bảng nguyên hàm của các hàm số cơ bản", CognitiveLevel.NHAN_BIET),
            ("Đại số và Giải tích", "Chương 4. Nguyên hàm của hàm số mũ và lượng giác", CognitiveLevel.NHAN_BIET),
            ("Đại số và Giải tích", "Chương 4. Định nghĩa tích phân và ý nghĩa hình học", CognitiveLevel.NHAN_BIET),
            ("Đại số và Giải tích", "Chương 4. Tính chất của tích phân", CognitiveLevel.NHAN_BIET),
            ("Đại số và Giải tích", "Chương 4. Tích phân của các hàm số cơ bản", CognitiveLevel.NHAN_BIET),
            ("Hình học và Đo lường", "Chương 4. Diện tích hình phẳng giới hạn bởi đồ thị hàm số", CognitiveLevel.NHAN_BIET),
            ("Hình học và Đo lường", "Chương 4. Thể tích vật thể và thể tích khối tròn xoay", CognitiveLevel.NHAN_BIET),
            ("Đại số và Giải tích", "Chương 4. Phương pháp đổi biến số tính nguyên hàm", CognitiveLevel.THONG_HIEU),
            ("Đại số và Giải tích", "Chương 4. Phương pháp nguyên hàm từng phần", CognitiveLevel.THONG_HIEU),
            ("Đại số và Giải tích", "Chương 4. Phương pháp tính tích phân", CognitiveLevel.THONG_HIEU),
            ("Hình học và Đo lường", "Chương 4. Ứng dụng tích phân tính diện tích hình phẳng", CognitiveLevel.THONG_HIEU),
        ]
        p2 = [
            ("Đại số và Giải tích", "Chương 4. Nguyên hàm và điều kiện ban đầu f(x0) = y0", CognitiveLevel.NHAN_BIET),
            ("Đại số và Giải tích", "Chương 4. Tích phân đổi biến số", CognitiveLevel.THONG_HIEU),
            ("Đại số và Giải tích", "Chương 4. Tích phân từng phần hàm đa thức nhân mũ/lượng giác", CognitiveLevel.THONG_HIEU),
            ("Hình học và Đo lường", "Chương 4. Ứng dụng tích phân tính thể tích vật thể tròn xoay", CognitiveLevel.VAN_DUNG),
        ]
        p3 = [
            ("Đại số và Giải tích", "Chương 4. Tích phân cơ bản", CognitiveLevel.THONG_HIEU),
            ("Đại số và Giải tích", "Chương 4. Ứng dụng tích phân tính quãng đường chuyển động", CognitiveLevel.VAN_DUNG),
            ("Đại số và Giải tích", "Chương 4. Tính tích phân bằng phương pháp đổi biến", CognitiveLevel.VAN_DUNG),
            ("Hình học và Đo lường", "Chương 4. Diện tích hình phẳng giới hạn bởi hai đường cong", CognitiveLevel.VAN_DUNG),
            ("Đại số và Giải tích", "Chương 4. Bài toán thực tế tích phân lưu lượng nước / chi phí", CognitiveLevel.VAN_DUNG_CAO),
            ("Hình học và Đo lường", "Chương 4. Thể tích thùng rượu, phao bơi tròn xoay thực tế", CognitiveLevel.VAN_DUNG_CAO),
        ]
        return ExamMatrix(
            id="matrix_12_gk2",
            title="ĐỀ KIỂM TRA GIỮA HỌC KỲ 2 - TOÁN 12",
            description="Theo SGK Kết nối tri thức: Chương 4 (Nguyên hàm và tích phân, Ứng dụng hình học)",
            subject="TOÁN HỌC",
            grade=12,
            semester="Giữa kỳ 2",
            time_minutes=90,
            academic_year="2026 - 2027",
            tags=["Lớp 12", "Giữa kỳ 2", "KNTT", "22 câu", "TN THPT format"],
            slots=_build_thpt_12_slots("m12_gk2", p1, p2, p3)
        )

    @classmethod
    def get_matrix_12_ck2(cls) -> ExamMatrix:
        """Ma trận đề Cuối kì II - Toán 12 (Chương 4 đến Chương 6 - Ôn thi Tốt nghiệp)."""
        p1 = [
            ("Đại số và Giải tích", "Chương 4. Nguyên hàm cơ bản", CognitiveLevel.NHAN_BIET),
            ("Đại số và Giải tích", "Chương 4. Tính chất tích phân", CognitiveLevel.NHAN_BIET),
            ("Hình học và Đo lường", "Chương 4. Ứng dụng hình học của tích phân", CognitiveLevel.NHAN_BIET),
            ("Hình học và Đo lường", "Chương 5. Phương trình mặt phẳng trong không gian Oxyz", CognitiveLevel.NHAN_BIET),
            ("Hình học và Đo lường", "Chương 5. Phương trình đường thẳng trong không gian Oxyz", CognitiveLevel.NHAN_BIET),
            ("Hình học và Đo lường", "Chương 5. Phương trình mặt cầu trong không gian Oxyz", CognitiveLevel.NHAN_BIET),
            ("Thống kê và Xác suất", "Chương 6. Khái niệm xác suất có điều kiện", CognitiveLevel.NHAN_BIET),
            ("Thống kê và Xác suất", "Chương 6. Công thức nhân xác suất", CognitiveLevel.NHAN_BIET),
            ("Đại số và Giải tích", "Chương 4. Tích phân đổi biến số", CognitiveLevel.THONG_HIEU),
            ("Hình học và Đo lường", "Chương 5. Vị trí tương đối giữa mặt phẳng và đường thẳng", CognitiveLevel.THONG_HIEU),
            ("Hình học và Đo lường", "Chương 5. Khoảng cách từ điểm đến mặt phẳng, đường thẳng", CognitiveLevel.THONG_HIEU),
            ("Thống kê và Xác suất", "Chương 6. Công thức xác suất toàn phần và công thức Bayes", CognitiveLevel.THONG_HIEU),
        ]
        p2 = [
            ("Đại số và Giải tích", "Chương 4. Nguyên hàm và tích phân toàn diện", CognitiveLevel.NHAN_BIET),
            ("Hình học và Đo lường", "Chương 5. Phương trình đường thẳng và mặt phẳng Oxyz", CognitiveLevel.THONG_HIEU),
            ("Hình học và Đo lường", "Chương 5. Mặt cầu và khoảng cách trong Oxyz", CognitiveLevel.THONG_HIEU),
            ("Thống kê và Xác suất", "Chương 6. Bài toán xác suất có điều kiện trong xét nghiệm y tế", CognitiveLevel.VAN_DUNG),
        ]
        p3 = [
            ("Hình học và Đo lường", "Chương 5. Bán kính mặt cầu hoặc khoảng cách", CognitiveLevel.THONG_HIEU),
            ("Đại số và Giải tích", "Chương 4. Ứng dụng tích phân tính diện tích hình phẳng", CognitiveLevel.VAN_DUNG),
            ("Hình học và Đo lường", "Chương 5. Viết phương trình mặt phẳng đi qua 3 điểm hoặc tiếp xúc mặt cầu", CognitiveLevel.VAN_DUNG),
            ("Hình học và Đo lường", "Chương 5. Góc và khoảng cách trong hình giải tích Oxyz", CognitiveLevel.VAN_DUNG),
            ("Đại số và Giải tích", "Chương 4. Tích phân hàm ẩn hoặc thể tích vật thể thực tế", CognitiveLevel.VAN_DUNG_CAO),
            ("Hình học và Đo lường", "Chương 5. Cực trị hình học không gian Oxyz", CognitiveLevel.VAN_DUNG_CAO),
        ]
        return ExamMatrix(
            id="matrix_12_ck2",
            title="ĐỀ KIỂM TRA CUỐI HỌC KỲ 2 - TOÁN 12 (ÔN TỐT NGHIỆP)",
            description="Bao quát Chương 4 đến Chương 6 (Nguyên hàm & Tích phân, Hình học giải tích Oxyz, Xác suất có điều kiện Bayes)",
            subject="TOÁN HỌC",
            grade=12,
            semester="Học kỳ 2",
            time_minutes=90,
            academic_year="2026 - 2027",
            tags=["Lớp 12", "Cuối kỳ 2", "Ôn Tốt nghiệp", "KNTT", "22 câu"],
            slots=_build_thpt_12_slots("m12_ck2", p1, p2, p3)
        )

    # =========================================================================
    # DANH MỤC TỔNG HỢP VÀ BỘ LỌC
    # =========================================================================
    @classmethod
    def get_all_preset_matrices(cls) -> List[ExamMatrix]:
        """Danh mục toàn bộ các ma trận chuẩn hóa theo SGK Kết nối tri thức và Bộ GD&ĐT."""
        return [
            # ĐỀ CHUẨN BỘ GD&ĐT 2025
            cls.get_matrix_12_thpt_2025(),

            # LỚP 6
            cls.get_matrix_6_gk1(),
            cls.get_matrix_6_ck1(),
            cls.get_matrix_6_gk2(),
            cls.get_matrix_6_ck2(),

            # LỚP 7
            cls.get_matrix_7_gk1(),
            cls.get_matrix_7_ck1(),
            cls.get_matrix_7_gk2(),
            cls.get_matrix_7_ck2(),

            # LỚP 8
            cls.get_matrix_8_gk1(),
            cls.get_matrix_8_ck1(),
            cls.get_matrix_8_gk2(),
            cls.get_matrix_8_ck2(),

            # LỚP 9
            cls.get_matrix_9_gk1(),
            cls.get_matrix_9_ck1(),
            cls.get_matrix_9_gk2(),
            cls.get_matrix_9_ck2(),

            # LỚP 10
            cls.get_matrix_10_gk1(),
            cls.get_matrix_10_ck1(),
            cls.get_matrix_10_gk2(),
            cls.get_matrix_10_ck2(),

            # LỚP 11
            cls.get_matrix_11_gk1(),
            cls.get_matrix_11_ck1(),
            cls.get_matrix_11_gk2(),
            cls.get_matrix_11_ck2(),

            # LỚP 12
            cls.get_matrix_12_gk1(),
            cls.get_matrix_12_ck1(),
            cls.get_matrix_12_gk2(),
            cls.get_matrix_12_ck2(),
        ]

    @classmethod
    def get_custom_matrices(cls) -> List[ExamMatrix]:
        """Tải các ma trận do giáo viên tự thiết kế hoặc tải lên."""
        custom_matrices = []
        if not os.path.exists(CUSTOM_MATRICES_DIR):
            return custom_matrices

        for filename in os.listdir(CUSTOM_MATRICES_DIR):
            if filename.endswith(".json"):
                path = os.path.join(CUSTOM_MATRICES_DIR, filename)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        data["is_custom"] = True
                        custom_matrices.append(ExamMatrix(**data))
                except Exception as e:
                    pass
        return custom_matrices

    @classmethod
    def save_custom_matrix(cls, matrix: ExamMatrix) -> ExamMatrix:
        """Lưu ma trận tùy biến của giáo viên vào thư mục lưu trữ cục bộ."""
        matrix.is_custom = True
        filename = f"{matrix.id}.json"
        path = os.path.join(CUSTOM_MATRICES_DIR, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(matrix.model_dump_json(indent=2))
        return matrix

    @classmethod
    def delete_custom_matrix(cls, matrix_id: str) -> bool:
        """Xóa ma trận tùy biến của giáo viên."""
        filename = f"{matrix_id}.json"
        path = os.path.join(CUSTOM_MATRICES_DIR, filename)
        if os.path.exists(path):
            os.remove(path)
            return True
        return False

    @classmethod
    def get_matrix_by_id(cls, matrix_id: str) -> Optional[ExamMatrix]:
        """Tìm ma trận theo ID (tìm trong cả kho có sẵn và kho giáo viên tự tạo)."""
        for m in cls.get_all_preset_matrices():
            if m.id == matrix_id:
                return m
        for m in cls.get_custom_matrices():
            if m.id == matrix_id:
                return m
        return None

    @classmethod
    def filter_matrices(
        cls,
        grade: Optional[int] = None,
        semester: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[ExamMatrix]:
        """Lọc ma trận theo khối lớp, học kỳ và từ khóa tìm kiếm."""
        all_matrices = cls.get_all_preset_matrices() + cls.get_custom_matrices()
        results = all_matrices

        if grade is not None:
            results = [m for m in results if m.grade == grade]

        if semester:
            sem_lower = semester.lower()
            results = [m for m in results if m.semester and sem_lower in m.semester.lower()]

        if search:
            q = search.lower().strip()
            results = [
                m for m in results
                if q in m.title.lower()
                or (m.description and q in m.description.lower())
                or any(q in t.lower() for t in m.tags)
            ]

        return results

    # =========================================================================
    # EXCEL IMPORT / EXPORT TEMPLATE
    # =========================================================================
    @classmethod
    def generate_excel_template(cls, matrix_id: Optional[str] = None) -> bytes:
        """Tạo file Excel mẫu ma trận đề thi chuẩn mực để giáo viên tải về chỉnh sửa."""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Ma trận đề thi"

        headers = ["STT", "Phần thi", "Dạng câu", "Chủ đề kiến thức", "Dạng bài chi tiết", "Mức độ nhận thức", "Điểm số"]
        ws.append(headers)

        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
        border = Border(
            left=Side(style='thin', color='BFBFBF'),
            right=Side(style='thin', color='BFBFBF'),
            top=Side(style='thin', color='BFBFBF'),
            bottom=Side(style='thin', color='BFBFBF')
        )

        for col_idx in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=col_idx)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = border

        matrix = cls.get_matrix_by_id(matrix_id) if matrix_id else cls.get_matrix_12_thpt_2025()
        type_names = {
            QuestionType.MULTIPLE_CHOICE: "Trắc nghiệm 4 lựa chọn",
            QuestionType.TRUE_FALSE: "Trắc nghiệm Đúng/Sai",
            QuestionType.SHORT_ANSWER: "Trả lời ngắn",
            QuestionType.ESSAY: "Tự luận",
        }
        level_names = {
            CognitiveLevel.NHAN_BIET: "Nhận biết",
            CognitiveLevel.THONG_HIEU: "Thông hiểu",
            CognitiveLevel.VAN_DUNG: "Vận dụng",
            CognitiveLevel.VAN_DUNG_CAO: "Vận dụng cao",
        }

        for slot in matrix.slots:
            ws.append([
                slot.slot_number,
                f"Phần {slot.part}",
                type_names.get(slot.type, "Trắc nghiệm 4 lựa chọn"),
                slot.topic,
                slot.subtopic or "",
                level_names.get(slot.level, "Nhận biết"),
                slot.points
            ])

        for row in range(2, len(matrix.slots) + 2):
            for col in range(1, len(headers) + 1):
                cell = ws.cell(row=row, column=col)
                cell.border = border
                if col in [1, 2, 6, 7]:
                    cell.alignment = Alignment(horizontal="center", vertical="center")

        col_widths = [8, 12, 25, 35, 35, 15, 10]
        for idx, width in enumerate(col_widths, start=1):
            col_letter = openpyxl.utils.get_column_letter(idx)
            ws.column_dimensions[col_letter].width = width

        output = io.BytesIO()
        wb.save(output)
        return output.getvalue()

    @classmethod
    def parse_excel_matrix(cls, file_bytes: bytes, grade: Optional[int] = None) -> ExamMatrix:
        """Đọc file Excel giáo viên tải lên thành cấu trúc ExamMatrix linh hoạt, kiểm tra lỗi từng dòng."""
        wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
        ws = wb.active

        type_map = {
            "trắc nghiệm": QuestionType.MULTIPLE_CHOICE,
            "4 lựa chọn": QuestionType.MULTIPLE_CHOICE,
            "đúng/sai": QuestionType.TRUE_FALSE,
            "đúng sai": QuestionType.TRUE_FALSE,
            "trả lời ngắn": QuestionType.SHORT_ANSWER,
            "ngắn": QuestionType.SHORT_ANSWER,
            "tự luận": QuestionType.ESSAY,
            "multiple_choice": QuestionType.MULTIPLE_CHOICE,
            "true_false": QuestionType.TRUE_FALSE,
            "short_answer": QuestionType.SHORT_ANSWER,
            "essay": QuestionType.ESSAY,
        }

        level_map = {
            "nhận biết": CognitiveLevel.NHAN_BIET,
            "thông hiểu": CognitiveLevel.THONG_HIEU,
            "vận dụng cao": CognitiveLevel.VAN_DUNG_CAO,
            "vận dụng": CognitiveLevel.VAN_DUNG,
            "nhan_biet": CognitiveLevel.NHAN_BIET,
            "thong_hieu": CognitiveLevel.THONG_HIEU,
            "van_dung_cao": CognitiveLevel.VAN_DUNG_CAO,
            "van_dung": CognitiveLevel.VAN_DUNG,
        }

        slots: List[ExamSlot] = []
        slot_number = 1

        for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
            if not row or row[0] is None:
                continue

            # Kiểm tra phần thi (Part)
            part_str = str(row[1]).strip() if len(row) > 1 and row[1] is not None else "1"
            part = 1
            if part_str in ["1", "2", "3", "4"]:
                part = int(part_str)
            elif "2" in part_str or "II" in part_str.upper():
                part = 2
            elif "3" in part_str or "III" in part_str.upper():
                part = 3
            elif "4" in part_str or "IV" in part_str.upper():
                part = 4
            elif "1" in part_str or "I" in part_str.upper():
                part = 1
            else:
                raise ValueError(f"Dòng {row_idx}: Phần thi '{part_str}' không hợp lệ. Vui lòng chọn 1, 2, 3 hoặc 4 (Phần I, II, III, IV).")

            # Kiểm tra dạng thức câu hỏi (Type)
            type_raw = str(row[2]).strip() if len(row) > 2 and row[2] else ""
            type_str = type_raw.lower()
            q_type = None
            for k, v in type_map.items():
                if k in type_str:
                    q_type = v
                    break
            if q_type is None:
                raise ValueError(
                    f"Dòng {row_idx}: Dạng thức câu hỏi '{type_raw}' không hợp lệ. "
                    f"Các dạng hợp lệ: Trắc nghiệm 4 lựa chọn, Đúng/Sai, Trả lời ngắn, Tự luận."
                )

            topic = str(row[3]).strip() if len(row) > 3 and row[3] else "Toán học"
            subtopic = str(row[4]).strip() if len(row) > 4 and row[4] else None

            # Kiểm tra mức độ nhận thức (Level)
            level_raw = str(row[5]).strip() if len(row) > 5 and row[5] else ""
            level_str = level_raw.lower()
            level = None
            for k, v in level_map.items():
                if k in level_str:
                    level = v
                    break
            if level is None:
                raise ValueError(
                    f"Dòng {row_idx}: Mức độ nhận thức '{level_raw}' không hợp lệ. "
                    f"Các mức độ hợp lệ: Nhận biết, Thông hiểu, Vận dụng, Vận dụng cao."
                )

            try:
                points = float(row[6]) if len(row) > 6 and row[6] is not None else (0.25 if q_type == QuestionType.MULTIPLE_CHOICE else 1.0)
            except Exception:
                points = 0.25

            slots.append(ExamSlot(
                slot_id=f"custom_slot_{slot_number}",
                slot_number=slot_number,
                part=part,
                type=q_type,
                topic=topic,
                subtopic=subtopic,
                level=level,
                points=points
            ))
            slot_number += 1

        effective_grade = grade if (grade and 6 <= grade <= 12) else 12
        return ExamMatrix(
            id=f"matrix_excel_{len(slots)}câu",
            title=f"ĐỀ THI TỪ FILE EXCEL MA TRẬN (LỚP {effective_grade})",
            description=f"Ma trận được nạp tự động từ file Excel ({len(slots)} câu hỏi)",
            subject="TOÁN HỌC",
            grade=effective_grade,
            semester="Kiểm tra định kì",
            time_minutes=90 if len(slots) >= 15 else 45,
            academic_year="2026 - 2027",
            tags=["Tùy biến", "Excel", f"Lớp {effective_grade}", f"{len(slots)} câu"],
            is_custom=True,
            slots=slots
        )
