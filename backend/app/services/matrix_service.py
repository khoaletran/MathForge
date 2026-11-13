import io
import json
import os
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from typing import List, Dict, Any, Optional
from app.models.question import ExamMatrix, ExamSlot, QuestionType, CognitiveLevel

CUSTOM_MATRICES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "matrices"))
os.makedirs(CUSTOM_MATRICES_DIR, exist_ok=True)

class MatrixService:
    """
    Quản lý ma trận đề thi từ Lớp 6 đến Lớp 12 theo chuẩn mới nhất của Bộ GD&ĐT (2025 - 2026).
    Bao gồm 4 chủ đề cốt lõi:
    1. Số và Đại số
    2. Hình học và Đo lường
    3. Thống kê và Xác suất
    4. Hoạt động thực hành và trải nghiệm (Toán thực tế)
    Áp dụng đồng bộ cho các bộ sách giáo khoa mới (Kết nối tri thức, Cánh Diều, Chân trời sáng tạo).
    """

    # =========================================================================
    # LỚP 6
    # =========================================================================
    @classmethod
    def get_matrix_6_hk1(cls) -> ExamMatrix:
        """Đề Kiểm Tra Cuối Học Kỳ 1 - Toán 6 (4 chủ đề chuẩn GDPT 2018)."""
        slots = [
            # Phần I: 8 câu trắc nghiệm 4 lựa chọn (2.0 điểm, mỗi câu 0.25đ)
            ExamSlot(slot_id="s6_1", slot_number=1, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Số và Đại số", subtopic="Tập hợp số tự nhiên và thứ tự thực hiện phép tính", level=CognitiveLevel.NHAN_BIET, points=0.25),
            ExamSlot(slot_id="s6_2", slot_number=2, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Số và Đại số", subtopic="Dấu hiệu chia hết cho 2, 3, 5, 9", level=CognitiveLevel.NHAN_BIET, points=0.25),
            ExamSlot(slot_id="s6_3", slot_number=3, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Số và Đại số", subtopic="Số nguyên âm và tập hợp các số nguyên Z", level=CognitiveLevel.NHAN_BIET, points=0.25),
            ExamSlot(slot_id="s6_4", slot_number=4, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Số và Đại số", subtopic="Phép cộng và phép trừ hai số nguyên", level=CognitiveLevel.THONG_HIEU, points=0.25),
            ExamSlot(slot_id="s6_5", slot_number=5, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Hình học và Đo lường", subtopic="Hình tam giác đều, hình vuông, hình lục giác đều", level=CognitiveLevel.NHAN_BIET, points=0.25),
            ExamSlot(slot_id="s6_6", slot_number=6, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Hình học và Đo lường", subtopic="Hình chữ nhật, hình thoi, hình bình hành, hình thang cân", level=CognitiveLevel.THONG_HIEU, points=0.25),
            ExamSlot(slot_id="s6_7", slot_number=7, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Thống kê và Xác suất", subtopic="Thu thập dữ liệu và bảng số liệu ban đầu", level=CognitiveLevel.NHAN_BIET, points=0.25),
            ExamSlot(slot_id="s6_8", slot_number=8, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Thống kê và Xác suất", subtopic="Đọc và phân tích biểu đồ cột, biểu đồ cột kép", level=CognitiveLevel.THONG_HIEU, points=0.25),

            # Phần II: 2 câu Đúng / Sai (2.0 điểm, mỗi câu 1.0đ)
            ExamSlot(slot_id="s6_9", slot_number=9, part=2, type=QuestionType.TRUE_FALSE, topic="Số và Đại số", subtopic="Tính chất chia hết và ước chung lớn nhất, bội chung nhỏ nhất", level=CognitiveLevel.THONG_HIEU, points=1.0),
            ExamSlot(slot_id="s6_10", slot_number=10, part=2, type=QuestionType.TRUE_FALSE, topic="Hình học và Đo lường", subtopic="Tính chất cạnh, góc và đường chéo của các hình tứ giác đặc biệt", level=CognitiveLevel.THONG_HIEU, points=1.0),

            # Phần III: 4 câu Trả lời ngắn / Tự luận (6.0 điểm)
            ExamSlot(slot_id="s6_11", slot_number=11, part=3, type=QuestionType.SHORT_ANSWER, topic="Số và Đại số", subtopic="Thực hiện phép tính hợp lý trong tập hợp số nguyên", level=CognitiveLevel.THONG_HIEU, points=1.5),
            ExamSlot(slot_id="s6_12", slot_number=12, part=3, type=QuestionType.SHORT_ANSWER, topic="Số và Đại số", subtopic="Tìm số nguyên x thỏa mãn đẳng thức", level=CognitiveLevel.VAN_DUNG, points=1.5),
            ExamSlot(slot_id="s6_13", slot_number=13, part=3, type=QuestionType.SHORT_ANSWER, topic="Toán thực tế & Trải nghiệm", subtopic="Bài toán lát gạch sân vườn hoặc tính chi phí hàng rào", level=CognitiveLevel.VAN_DUNG, points=1.5),
            ExamSlot(slot_id="s6_14", slot_number=14, part=3, type=QuestionType.SHORT_ANSWER, topic="Thống kê và Xác suất", subtopic="Tính số học sinh hoặc tỉ lệ từ bảng biểu đồ số liệu", level=CognitiveLevel.VAN_DUNG_CAO, points=1.5),
        ]
        return ExamMatrix(
            id="matrix_6_hk1",
            title="ĐỀ KIỂM TRA CUỐI HỌC KỲ 1 - TOÁN 6",
            description="Bao quát 4 chủ đề: Số học & Số nguyên, Hình học trực quan, Thống kê biểu đồ, Toán thực tế (GDPT 2018)",
            subject="TOÁN HỌC",
            grade=6,
            semester="Học kỳ 1",
            time_minutes=90,
            academic_year="2025 - 2026",
            tags=["Lớp 6", "Học kỳ 1", "Số nguyên", "Hình học trực quan", "Bộ GD 2026"],
            slots=slots
        )

    @classmethod
    def get_matrix_6_hk2(cls) -> ExamMatrix:
        """Đề Kiểm Tra Cuối Học Kỳ 2 - Toán 6 (4 chủ đề chuẩn GDPT 2018)."""
        slots = [
            # Phần I: 8 câu trắc nghiệm 4 lựa chọn (2.0 điểm)
            ExamSlot(slot_id="s6b_1", slot_number=1, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Số và Đại số", subtopic="Phân số với tử và mẫu là số nguyên, phân số bằng nhau", level=CognitiveLevel.NHAN_BIET, points=0.25),
            ExamSlot(slot_id="s6b_2", slot_number=2, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Số và Đại số", subtopic="So sánh phân số và hỗn số dương", level=CognitiveLevel.THONG_HIEU, points=0.25),
            ExamSlot(slot_id="s6b_3", slot_number=3, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Số và Đại số", subtopic="Số thập phân và làm tròn số thập phân", level=CognitiveLevel.NHAN_BIET, points=0.25),
            ExamSlot(slot_id="s6b_4", slot_number=4, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Số và Đại số", subtopic="Tỉ số và tỉ số phần trăm", level=CognitiveLevel.THONG_HIEU, points=0.25),
            ExamSlot(slot_id="s6b_5", slot_number=5, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Hình học và Đo lường", subtopic="Điểm, đường thẳng, ba điểm thẳng hàng", level=CognitiveLevel.NHAN_BIET, points=0.25),
            ExamSlot(slot_id="s6b_6", slot_number=6, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Hình học và Đo lường", subtopic="Đoạn thẳng, độ dài đoạn thẳng và trung điểm", level=CognitiveLevel.THONG_HIEU, points=0.25),
            ExamSlot(slot_id="s6b_7", slot_number=7, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Hình học và Đo lường", subtopic="Góc, số đo góc, góc nhọn, góc vuông, góc tù", level=CognitiveLevel.NHAN_BIET, points=0.25),
            ExamSlot(slot_id="s6b_8", slot_number=8, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Thống kê và Xác suất", subtopic="Xác suất thực nghiệm trong trò chơi đơn giản", level=CognitiveLevel.THONG_HIEU, points=0.25),

            # Phần II: 2 câu Đúng / Sai (2.0 điểm)
            ExamSlot(slot_id="s6b_9", slot_number=9, part=2, type=QuestionType.TRUE_FALSE, topic="Số và Đại số", subtopic="Các phép tính cộng, trừ, nhân, chia phân số và số thập phân", level=CognitiveLevel.THONG_HIEU, points=1.0),
            ExamSlot(slot_id="s6b_10", slot_number=10, part=2, type=QuestionType.TRUE_FALSE, topic="Hình học và Đo lường", subtopic="Vị trí tương đối của hai đường thẳng, góc và số đo góc", level=CognitiveLevel.THONG_HIEU, points=1.0),

            # Phần III: 4 câu Trả lời ngắn / Tự luận (6.0 điểm)
            ExamSlot(slot_id="s6b_11", slot_number=11, part=3, type=QuestionType.SHORT_ANSWER, topic="Số và Đại số", subtopic="Thực hiện phép tính phân số hợp lý", level=CognitiveLevel.THONG_HIEU, points=1.5),
            ExamSlot(slot_id="s6b_12", slot_number=12, part=3, type=QuestionType.SHORT_ANSWER, topic="Toán thực tế & Trải nghiệm", subtopic="Bài toán mua bán giảm giá phần trăm hoặc lãi suất ngân hàng", level=CognitiveLevel.VAN_DUNG, points=1.5),
            ExamSlot(slot_id="s6b_13", slot_number=13, part=3, type=QuestionType.SHORT_ANSWER, topic="Hình học và Đo lường", subtopic="Tính độ dài đoạn thẳng và chứng minh trung điểm", level=CognitiveLevel.VAN_DUNG, points=1.5),
            ExamSlot(slot_id="s6b_14", slot_number=14, part=3, type=QuestionType.SHORT_ANSWER, topic="Thống kê và Xác suất", subtopic="Tính xác suất thực nghiệm gieo xúc xắc / quay số", level=CognitiveLevel.VAN_DUNG_CAO, points=1.5),
        ]
        return ExamMatrix(
            id="matrix_6_hk2",
            title="ĐỀ KIỂM TRA CUỐI HỌC KỲ 2 - TOÁN 6",
            description="Bao quát 4 chủ đề: Phân số & Số thập phân, Hình học phẳng (Đoạn thẳng & Góc), Xác suất thực nghiệm, Toán thực tế",
            subject="TOÁN HỌC",
            grade=6,
            semester="Học kỳ 2",
            time_minutes=90,
            academic_year="2025 - 2026",
            tags=["Lớp 6", "Học kỳ 2", "Phân số", "Hình học phẳng", "Bộ GD 2026"],
            slots=slots
        )

    @classmethod
    def get_matrix_6_giuaki2(cls) -> ExamMatrix:
        """Đề Kiểm Tra Giữa Học Kỳ 2 - Toán 6 (Bộ sách Mới 2026: KNTT, Cánh Diều, CTST)."""
        slots = [
            ExamSlot(slot_id="s6g_1", slot_number=1, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Số và Đại số", subtopic="Khái niệm phân số, phân số bằng nhau và tính chất cơ bản", level=CognitiveLevel.NHAN_BIET, points=0.25),
            ExamSlot(slot_id="s6g_2", slot_number=2, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Số và Đại số", subtopic="So sánh phân số và quy đồng mẫu số", level=CognitiveLevel.THONG_HIEU, points=0.25),
            ExamSlot(slot_id="s6g_3", slot_number=3, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Số và Đại số", subtopic="Số thập phân âm và số thập phân dương", level=CognitiveLevel.NHAN_BIET, points=0.25),
            ExamSlot(slot_id="s6g_4", slot_number=4, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Số và Đại số", subtopic="Làm tròn số thập phân và ước lượng kết quả", level=CognitiveLevel.THONG_HIEU, points=0.25),
            ExamSlot(slot_id="s6g_5", slot_number=5, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Hình học và Đo lường", subtopic="Điểm và đường thẳng, ba điểm thẳng hàng", level=CognitiveLevel.NHAN_BIET, points=0.25),
            ExamSlot(slot_id="s6g_6", slot_number=6, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Hình học và Đo lường", subtopic="Hai đường thẳng cắt nhau, song song", level=CognitiveLevel.THONG_HIEU, points=0.25),
            ExamSlot(slot_id="s6g_7", slot_number=7, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Thống kê và Xác suất", subtopic="Thu thập dữ liệu và lập bảng thống kê", level=CognitiveLevel.NHAN_BIET, points=0.25),
            ExamSlot(slot_id="s6g_8", slot_number=8, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Thống kê và Xác suất", subtopic="Đọc và khai thác thông tin từ biểu đồ cột kép", level=CognitiveLevel.THONG_HIEU, points=0.25),

            ExamSlot(slot_id="s6g_9", slot_number=9, part=2, type=QuestionType.TRUE_FALSE, topic="Số và Đại số", subtopic="Phép cộng, trừ, nhân, chia phân số và hỗn số", level=CognitiveLevel.THONG_HIEU, points=1.0),
            ExamSlot(slot_id="s6g_10", slot_number=10, part=2, type=QuestionType.TRUE_FALSE, topic="Hình học và Đo lường", subtopic="Tia và hai tia đối nhau, đoạn thẳng và trung điểm", level=CognitiveLevel.THONG_HIEU, points=1.0),

            ExamSlot(slot_id="s6g_11", slot_number=11, part=3, type=QuestionType.SHORT_ANSWER, topic="Số và Đại số", subtopic="Tính giá trị biểu thức phân số hợp lý", level=CognitiveLevel.THONG_HIEU, points=1.5),
            ExamSlot(slot_id="s6g_12", slot_number=12, part=3, type=QuestionType.SHORT_ANSWER, topic="Số và Đại số", subtopic="Tìm số chưa biết x trong đẳng thức phân số", level=CognitiveLevel.VAN_DUNG, points=1.5),
            ExamSlot(slot_id="s6g_13", slot_number=13, part=3, type=QuestionType.SHORT_ANSWER, topic="Hình học và Đo lường", subtopic="Tính độ dài đoạn thẳng trên tia Ox và xác định trung điểm", level=CognitiveLevel.VAN_DUNG, points=1.5),
            ExamSlot(slot_id="s6g_14", slot_number=14, part=3, type=QuestionType.SHORT_ANSWER, topic="Toán thực tế & Trải nghiệm", subtopic="Tính tỉ số phần trăm và chi phí mua hàng thực tế", level=CognitiveLevel.VAN_DUNG_CAO, points=1.5),
        ]
        return ExamMatrix(
            id="matrix_6_gk2",
            title="ĐỀ KIỂM TRA GIỮA HỌC KỲ 2 - TOÁN 6",
            description="Bao quát 4 chủ đề bộ sách mới: Phân số, Số thập phân, Hình phẳng cơ bản, Biểu đồ cột kép & Toán thực tế (GDPT 2018)",
            subject="TOÁN HỌC",
            grade=6,
            semester="Giữa kỳ 2",
            time_minutes=90,
            academic_year="2025 - 2026",
            tags=["Lớp 6", "Giữa kỳ 2", "Phân số", "Đoạn thẳng", "KNTT / CTST / Cánh Diều", "Bộ GD 2026"],
            slots=slots
        )

    # =========================================================================
    # LỚP 7
    # =========================================================================
    @classmethod
    def get_matrix_7_hk1(cls) -> ExamMatrix:
        """Đề Kiểm Tra Cuối Học Kỳ 1 - Toán 7 (4 chủ đề chuẩn GDPT 2018)."""
        slots = [
            # Phần I: 8 câu trắc nghiệm (2.0 điểm)
            ExamSlot(slot_id="s7_1", slot_number=1, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Số và Đại số", subtopic="Tập hợp số hữu tỉ Q và biểu diễn trên trục số", level=CognitiveLevel.NHAN_BIET, points=0.25),
            ExamSlot(slot_id="s7_2", slot_number=2, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Số và Đại số", subtopic="Lũy thừa với số mũ tự nhiên của số hữu tỉ", level=CognitiveLevel.THONG_HIEU, points=0.25),
            ExamSlot(slot_id="s7_3", slot_number=3, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Số và Đại số", subtopic="Số vô tỉ, căn bậc hai số học và số thực R", level=CognitiveLevel.NHAN_BIET, points=0.25),
            ExamSlot(slot_id="s7_4", slot_number=4, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Số và Đại số", subtopic="Giá trị tuyệt đối của một số thực", level=CognitiveLevel.THONG_HIEU, points=0.25),
            ExamSlot(slot_id="s7_5", slot_number=5, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Hình học và Đo lường", subtopic="Góc ở vị trí đặc biệt (kề bù, so le trong, đồng vị)", level=CognitiveLevel.NHAN_BIET, points=0.25),
            ExamSlot(slot_id="s7_6", slot_number=6, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Hình học và Đo lường", subtopic="Hai đường thẳng song song và dấu hiệu nhận biết", level=CognitiveLevel.THONG_HIEU, points=0.25),
            ExamSlot(slot_id="s7_7", slot_number=7, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Hình học và Đo lường", subtopic="Hình lăng trụ đứng tam giác và hình lăng trụ đứng tứ giác", level=CognitiveLevel.NHAN_BIET, points=0.25),
            ExamSlot(slot_id="s7_8", slot_number=8, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Thống kê và Xác suất", subtopic="Thu thập, phân loại dữ liệu và biểu đồ hình quạt tròn", level=CognitiveLevel.THONG_HIEU, points=0.25),

            # Phần II: 2 câu Đúng / Sai (2.0 điểm)
            ExamSlot(slot_id="s7_9", slot_number=9, part=2, type=QuestionType.TRUE_FALSE, topic="Số và Đại số", subtopic="Thứ tự thực hiện phép tính và quy tắc dấu ngoặc", level=CognitiveLevel.THONG_HIEU, points=1.0),
            ExamSlot(slot_id="s7_10", slot_number=10, part=2, type=QuestionType.TRUE_FALSE, topic="Hình học và Đo lường", subtopic="Các trường hợp bằng nhau của tam giác (c-c-c, c-g-c, g-c-g)", level=CognitiveLevel.THONG_HIEU, points=1.0),

            # Phần III: 4 câu Trả lời ngắn / Tự luận (6.0 điểm)
            ExamSlot(slot_id="s7_11", slot_number=11, part=3, type=QuestionType.SHORT_ANSWER, topic="Số và Đại số", subtopic="Tính giá trị biểu thức số thực hợp lý", level=CognitiveLevel.THONG_HIEU, points=1.5),
            ExamSlot(slot_id="s7_12", slot_number=12, part=3, type=QuestionType.SHORT_ANSWER, topic="Toán thực tế & Trải nghiệm", subtopic="Tính diện tích xung quanh hoặc thể tích hộp chứa hình lăng trụ", level=CognitiveLevel.VAN_DUNG, points=1.5),
            ExamSlot(slot_id="s7_13", slot_number=13, part=3, type=QuestionType.SHORT_ANSWER, topic="Hình học và Đo lường", subtopic="Chứng minh hai tam giác bằng nhau và góc vuông", level=CognitiveLevel.VAN_DUNG, points=1.5),
            ExamSlot(slot_id="s7_14", slot_number=14, part=3, type=QuestionType.SHORT_ANSWER, topic="Thống kê và Xác suất", subtopic="Phân tích biểu đồ đoạn thẳng và rút ra kết luận", level=CognitiveLevel.VAN_DUNG_CAO, points=1.5),
        ]
        return ExamMatrix(
            id="matrix_7_hk1",
            title="ĐỀ KIỂM TRA CUỐI HỌC KỲ 1 - TOÁN 7",
            description="Bao quát 4 chủ đề: Số hữu tỉ & Số thực, Đường song song & Tam giác, Hình lăng trụ đứng, Biểu đồ quạt tròn",
            subject="TOÁN HỌC",
            grade=7,
            semester="Học kỳ 1",
            time_minutes=90,
            academic_year="2025 - 2026",
            tags=["Lớp 7", "Học kỳ 1", "Số hữu tỉ", "Tam giác bằng nhau", "Lăng trụ", "Bộ GD 2026"],
            slots=slots
        )

    @classmethod
    def get_matrix_7_hk2(cls) -> ExamMatrix:
        """Đề Kiểm Tra Cuối Học Kỳ 2 - Toán 7 (4 chủ đề chuẩn GDPT 2018)."""
        slots = [
            # Phần I: 8 câu trắc nghiệm (2.0 điểm)
            ExamSlot(slot_id="s7b_1", slot_number=1, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Số và Đại số", subtopic="Tỉ lệ thức và tính chất dãy tỉ số bằng nhau", level=CognitiveLevel.NHAN_BIET, points=0.25),
            ExamSlot(slot_id="s7b_2", slot_number=2, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Số và Đại số", subtopic="Đại lượng tỉ lệ thuận và đại lượng tỉ lệ nghịch", level=CognitiveLevel.THONG_HIEU, points=0.25),
            ExamSlot(slot_id="s7b_3", slot_number=3, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Số và Đại số", subtopic="Biểu thức đại số và giá trị của biểu thức đại số", level=CognitiveLevel.NHAN_BIET, points=0.25),
            ExamSlot(slot_id="s7b_4", slot_number=4, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Số và Đại số", subtopic="Đa thức một biến, bậc và hệ số của đa thức", level=CognitiveLevel.THONG_HIEU, points=0.25),
            ExamSlot(slot_id="s7b_5", slot_number=5, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Hình học và Đo lường", subtopic="Quan hệ giữa góc và cạnh đối diện trong tam giác", level=CognitiveLevel.NHAN_BIET, points=0.25),
            ExamSlot(slot_id="s7b_6", slot_number=6, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Hình học và Đo lường", subtopic="Tam giác cân, đường trung trực của đoạn thẳng", level=CognitiveLevel.THONG_HIEU, points=0.25),
            ExamSlot(slot_id="s7b_7", slot_number=7, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Hình học và Đo lường", subtopic="Sự đồng quy của ba đường trung tuyến, ba đường phân giác", level=CognitiveLevel.THONG_HIEU, points=0.25),
            ExamSlot(slot_id="s7b_8", slot_number=8, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Thống kê và Xác suất", subtopic="Biến cố ngẫu nhiên và xác suất của biến cố trong trò chơi", level=CognitiveLevel.NHAN_BIET, points=0.25),

            # Phần II: 2 câu Đúng / Sai (2.0 điểm)
            ExamSlot(slot_id="s7b_9", slot_number=9, part=2, type=QuestionType.TRUE_FALSE, topic="Số và Đại số", subtopic="Phép cộng, trừ, nhân, chia đa thức một biến và nghiệm của đa thức", level=CognitiveLevel.THONG_HIEU, points=1.0),
            ExamSlot(slot_id="s7b_10", slot_number=10, part=2, type=QuestionType.TRUE_FALSE, topic="Hình học và Đo lường", subtopic="Bất đẳng thức tam giác và tính chất đường trung trực", level=CognitiveLevel.THONG_HIEU, points=1.0),

            # Phần III: 4 câu Trả lời ngắn / Tự luận (6.0 điểm)
            ExamSlot(slot_id="s7b_11", slot_number=11, part=3, type=QuestionType.SHORT_ANSWER, topic="Số và Đại số", subtopic="Tìm đa thức và nghiệm của đa thức một biến", level=CognitiveLevel.THONG_HIEU, points=1.5),
            ExamSlot(slot_id="s7b_12", slot_number=12, part=3, type=QuestionType.SHORT_ANSWER, topic="Toán thực tế & Trải nghiệm", subtopic="Bài toán chia tỉ lệ thuận/nghịch thực tế (chia vốn, năng suất)", level=CognitiveLevel.VAN_DUNG, points=1.5),
            ExamSlot(slot_id="s7b_13", slot_number=13, part=3, type=QuestionType.SHORT_ANSWER, topic="Hình học và Đo lường", subtopic="Chứng minh tam giác cân và đường đồng quy", level=CognitiveLevel.VAN_DUNG, points=1.5),
            ExamSlot(slot_id="s7b_14", slot_number=14, part=3, type=QuestionType.SHORT_ANSWER, topic="Thống kê và Xác suất", subtopic="Tính xác suất của biến cố chọn ngẫu nhiên từ hộp/túi", level=CognitiveLevel.VAN_DUNG_CAO, points=1.5),
        ]
        return ExamMatrix(
            id="matrix_7_hk2",
            title="ĐỀ KIỂM TRA CUỐI HỌC KỲ 2 - TOÁN 7",
            description="Bao quát 4 chủ đề: Tỉ lệ thức & Đa thức một biến, Tam giác & Đường đồng quy, Xác suất biến cố, Toán thực tế",
            subject="TOÁN HỌC",
            grade=7,
            semester="Học kỳ 2",
            time_minutes=90,
            academic_year="2025 - 2026",
            tags=["Lớp 7", "Học kỳ 2", "Đa thức", "Tam giác cân", "Xác suất", "Bộ GD 2026"],
            slots=slots
        )

    @classmethod
    def get_matrix_7_giuaki2(cls) -> ExamMatrix:
        """Đề Kiểm Tra Giữa Học Kỳ 2 - Toán 7 (Bộ sách Mới 2026: KNTT, Cánh Diều, CTST)."""
        slots = [
            ExamSlot(slot_id="s7g_1", slot_number=1, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Số và Đại số", subtopic="Tỉ lệ thức và tính chất cơ bản của tỉ lệ thức", level=CognitiveLevel.NHAN_BIET, points=0.25),
            ExamSlot(slot_id="s7g_2", slot_number=2, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Số và Đại số", subtopic="Tính chất của dãy tỉ số bằng nhau", level=CognitiveLevel.THONG_HIEU, points=0.25),
            ExamSlot(slot_id="s7g_3", slot_number=3, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Số và Đại số", subtopic="Đại lượng tỉ lệ thuận và tỉ lệ nghịch", level=CognitiveLevel.NHAN_BIET, points=0.25),
            ExamSlot(slot_id="s7g_4", slot_number=4, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Số và Đại số", subtopic="Biểu thức đại số và đơn thức, đa thức một biến", level=CognitiveLevel.THONG_HIEU, points=0.25),
            ExamSlot(slot_id="s7g_5", slot_number=5, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Hình học và Đo lường", subtopic="Định lý tổng ba góc trong một tam giác", level=CognitiveLevel.NHAN_BIET, points=0.25),
            ExamSlot(slot_id="s7g_6", slot_number=6, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Hình học và Đo lường", subtopic="Hai tam giác bằng nhau trường hợp c-c-c và c-g-c", level=CognitiveLevel.THONG_HIEU, points=0.25),
            ExamSlot(slot_id="s7g_7", slot_number=7, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Hình học và Đo lường", subtopic="Tam giác cân và tính chất đường trung trực của đoạn thẳng", level=CognitiveLevel.THONG_HIEU, points=0.25),
            ExamSlot(slot_id="s7g_8", slot_number=8, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Thống kê và Xác suất", subtopic="Làm quen với biến cố ngẫu nhiên", level=CognitiveLevel.NHAN_BIET, points=0.25),

            ExamSlot(slot_id="s7g_9", slot_number=9, part=2, type=QuestionType.TRUE_FALSE, topic="Số và Đại số", subtopic="Tìm hai số x, y khi biết tổng/hiệu và tỉ số của chúng", level=CognitiveLevel.THONG_HIEU, points=1.0),
            ExamSlot(slot_id="s7g_10", slot_number=10, part=2, type=QuestionType.TRUE_FALSE, topic="Hình học và Đo lường", subtopic="Chứng minh hai tam giác vuông bằng nhau và góc tương ứng", level=CognitiveLevel.THONG_HIEU, points=1.0),

            ExamSlot(slot_id="s7g_11", slot_number=11, part=3, type=QuestionType.SHORT_ANSWER, topic="Số và Đại số", subtopic="Cộng trừ và sắp xếp đa thức một biến theo lũy thừa giảm dần", level=CognitiveLevel.THONG_HIEU, points=1.5),
            ExamSlot(slot_id="s7g_12", slot_number=12, part=3, type=QuestionType.SHORT_ANSWER, topic="Toán thực tế & Trải nghiệm", subtopic="Chia số cây trồng hoặc phần thưởng theo tỉ lệ", level=CognitiveLevel.VAN_DUNG, points=1.5),
            ExamSlot(slot_id="s7g_13", slot_number=13, part=3, type=QuestionType.SHORT_ANSWER, topic="Hình học và Đo lường", subtopic="Chứng minh tam giác cân và tính số đo góc", level=CognitiveLevel.VAN_DUNG, points=1.5),
            ExamSlot(slot_id="s7g_14", slot_number=14, part=3, type=QuestionType.SHORT_ANSWER, topic="Thống kê và Xác suất", subtopic="Tính xác suất của biến cố trong trò chơi chọn ngẫu nhiên", level=CognitiveLevel.VAN_DUNG_CAO, points=1.5),
        ]
        return ExamMatrix(
            id="matrix_7_gk2",
            title="ĐỀ KIỂM TRA GIỮA HỌC KỲ 2 - TOÁN 7",
            description="Bao quát 4 chủ đề bộ sách mới: Dãy tỉ số bằng nhau, Đa thức một biến, Tam giác bằng nhau, Biến cố ngẫu nhiên (GDPT 2018)",
            subject="TOÁN HỌC",
            grade=7,
            semester="Giữa kỳ 2",
            time_minutes=90,
            academic_year="2025 - 2026",
            tags=["Lớp 7", "Giữa kỳ 2", "Tỉ lệ thức", "Tam giác cân", "KNTT / CTST / Cánh Diều", "Bộ GD 2026"],
            slots=slots
        )

    # =========================================================================
    # LỚP 8
    # =========================================================================
    @classmethod
    def get_matrix_8_hk1(cls) -> ExamMatrix:
        """Đề Kiểm Tra Cuối Học Kỳ 1 - Toán 8 (4 chủ đề chuẩn GDPT 2018)."""
        slots = [
            # Phần I: 8 câu trắc nghiệm (2.0 điểm)
            ExamSlot(slot_id="s8_1", slot_number=1, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Số và Đại số", subtopic="Đơn thức và đa thức nhiều biến, bậc của đa thức", level=CognitiveLevel.NHAN_BIET, points=0.25),
            ExamSlot(slot_id="s8_2", slot_number=2, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Số và Đại số", subtopic="Các phép tính cộng, trừ, nhân, chia đa thức nhiều biến", level=CognitiveLevel.THONG_HIEU, points=0.25),
            ExamSlot(slot_id="s8_3", slot_number=3, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Số và Đại số", subtopic="Bảy hằng đẳng thức đáng nhớ", level=CognitiveLevel.NHAN_BIET, points=0.25),
            ExamSlot(slot_id="s8_4", slot_number=4, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Số và Đại số", subtopic="Phân thức đại số và điều kiện xác định", level=CognitiveLevel.THONG_HIEU, points=0.25),
            ExamSlot(slot_id="s8_5", slot_number=5, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Hình học và Đo lường", subtopic="Tứ giác và tổng các góc của một tứ giác", level=CognitiveLevel.NHAN_BIET, points=0.25),
            ExamSlot(slot_id="s8_6", slot_number=6, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Hình học và Đo lường", subtopic="Hình thang cân, hình bình hành, hình thoi", level=CognitiveLevel.THONG_HIEU, points=0.25),
            ExamSlot(slot_id="s8_7", slot_number=7, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Hình học và Đo lường", subtopic="Hình chóp tam giác đều và hình chóp tứ giác đều", level=CognitiveLevel.NHAN_BIET, points=0.25),
            ExamSlot(slot_id="s8_8", slot_number=8, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Thống kê và Xác suất", subtopic="Thu thập dữ liệu và lựa chọn biểu đồ thích hợp", level=CognitiveLevel.THONG_HIEU, points=0.25),

            # Phần II: 2 câu Đúng / Sai (2.0 điểm)
            ExamSlot(slot_id="s8_9", slot_number=9, part=2, type=QuestionType.TRUE_FALSE, topic="Số và Đại số", subtopic="Rút gọn phân thức đại số và tính giá trị biểu thức", level=CognitiveLevel.THONG_HIEU, points=1.0),
            ExamSlot(slot_id="s8_10", slot_number=10, part=2, type=QuestionType.TRUE_FALSE, topic="Hình học và Đo lường", subtopic="Dấu hiệu nhận biết hình chữ nhật và hình vuông", level=CognitiveLevel.THONG_HIEU, points=1.0),

            # Phần III: 4 câu Trả lời ngắn / Tự luận (6.0 điểm)
            ExamSlot(slot_id="s8_11", slot_number=11, part=3, type=QuestionType.SHORT_ANSWER, topic="Số và Đại số", subtopic="Rút gọn biểu thức chứa phân thức đại số", level=CognitiveLevel.THONG_HIEU, points=1.5),
            ExamSlot(slot_id="s8_12", slot_number=12, part=3, type=QuestionType.SHORT_ANSWER, topic="Toán thực tế & Trải nghiệm", subtopic="Tính thể tích hoặc diện tích xung quanh mái lều hình chóp đều", level=CognitiveLevel.VAN_DUNG, points=1.5),
            ExamSlot(slot_id="s8_13", slot_number=13, part=3, type=QuestionType.SHORT_ANSWER, topic="Hình học và Đo lường", subtopic="Chứng minh tứ giác đặc biệt (hình chữ nhật/hình vuông)", level=CognitiveLevel.VAN_DUNG, points=1.5),
            ExamSlot(slot_id="s8_14", slot_number=14, part=3, type=QuestionType.SHORT_ANSWER, topic="Thống kê và Xác suất", subtopic="Phân tích bảng tần số số liệu và nhận xét xu hướng", level=CognitiveLevel.VAN_DUNG_CAO, points=1.5),
        ]
        return ExamMatrix(
            id="matrix_8_hk1",
            title="ĐỀ KIỂM TRA CUỐI HỌC KỲ 1 - TOÁN 8",
            description="Bao quát 4 chủ đề: Đa thức & Hằng đẳng thức, Tứ giác đặc biệt, Hình chóp đều, Thống kê biểu đồ",
            subject="TOÁN HỌC",
            grade=8,
            semester="Học kỳ 1",
            time_minutes=90,
            academic_year="2025 - 2026",
            tags=["Lớp 8", "Học kỳ 1", "Hằng đẳng thức", "Tứ giác", "Hình chóp đều", "Bộ GD 2026"],
            slots=slots
        )

    @classmethod
    def get_matrix_8_hk2(cls) -> ExamMatrix:
        """Đề Kiểm Tra Cuối Học Kỳ 2 - Toán 8 (4 chủ đề chuẩn GDPT 2018)."""
        slots = [
            # Phần I: 8 câu trắc nghiệm (2.0 điểm)
            ExamSlot(slot_id="s8b_1", slot_number=1, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Số và Đại số", subtopic="Khái niệm hàm số và đồ thị hàm số bậc nhất y = ax + b", level=CognitiveLevel.NHAN_BIET, points=0.25),
            ExamSlot(slot_id="s8b_2", slot_number=2, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Số và Đại số", subtopic="Hệ số góc của đường thẳng y = ax + b và vị trí tương đối", level=CognitiveLevel.THONG_HIEU, points=0.25),
            ExamSlot(slot_id="s8b_3", slot_number=3, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Số và Đại số", subtopic="Phương trình bậc nhất một ẩn và cách giải", level=CognitiveLevel.NHAN_BIET, points=0.25),
            ExamSlot(slot_id="s8b_4", slot_number=4, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Số và Đại số", subtopic="Phương trình đưa được về dạng ax + b = 0", level=CognitiveLevel.THONG_HIEU, points=0.25),
            ExamSlot(slot_id="s8b_5", slot_number=5, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Hình học và Đo lường", subtopic="Định lý Thalès trong tam giác và định lý đảo", level=CognitiveLevel.NHAN_BIET, points=0.25),
            ExamSlot(slot_id="s8b_6", slot_number=6, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Hình học và Đo lường", subtopic="Tính chất đường phân giác của tam giác", level=CognitiveLevel.THONG_HIEU, points=0.25),
            ExamSlot(slot_id="s8b_7", slot_number=7, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Hình học và Đo lường", subtopic="Các trường hợp đồng dạng của tam giác", level=CognitiveLevel.THONG_HIEU, points=0.25),
            ExamSlot(slot_id="s8b_8", slot_number=8, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Thống kê và Xác suất", subtopic="Mô tả xác suất của biến cố ngẫu nhiên", level=CognitiveLevel.NHAN_BIET, points=0.25),

            # Phần II: 2 câu Đúng / Sai (2.0 điểm)
            ExamSlot(slot_id="s8b_9", slot_number=9, part=2, type=QuestionType.TRUE_FALSE, topic="Số và Đại số", subtopic="Đồ thị hàm số bậc nhất và điểm thuộc đồ thị", level=CognitiveLevel.THONG_HIEU, points=1.0),
            ExamSlot(slot_id="s8b_10", slot_number=10, part=2, type=QuestionType.TRUE_FALSE, topic="Hình học và Đo lường", subtopic="Tam giác vuông đồng dạng và tỉ số diện tích", level=CognitiveLevel.THONG_HIEU, points=1.0),

            # Phần III: 4 câu Trả lời ngắn / Tự luận (6.0 điểm)
            ExamSlot(slot_id="s8b_11", slot_number=11, part=3, type=QuestionType.SHORT_ANSWER, topic="Số và Đại số", subtopic="Giải phương trình bậc nhất một ẩn và phương trình tích", level=CognitiveLevel.THONG_HIEU, points=1.5),
            ExamSlot(slot_id="s8b_12", slot_number=12, part=3, type=QuestionType.SHORT_ANSWER, topic="Toán thực tế & Trải nghiệm", subtopic="Giải bài toán bằng cách lập phương trình (toán chuyển động/năng suất)", level=CognitiveLevel.VAN_DUNG, points=1.5),
            ExamSlot(slot_id="s8b_13", slot_number=13, part=3, type=QuestionType.SHORT_ANSWER, topic="Hình học và Đo lường", subtopic="Chứng minh tam giác đồng dạng và hệ thức hình học", level=CognitiveLevel.VAN_DUNG, points=1.5),
            ExamSlot(slot_id="s8b_14", slot_number=14, part=3, type=QuestionType.SHORT_ANSWER, topic="Thống kê và Xác suất", subtopic="Tính xác suất lý thuyết và so sánh xác suất thực nghiệm", level=CognitiveLevel.VAN_DUNG_CAO, points=1.5),
        ]
        return ExamMatrix(
            id="matrix_8_hk2",
            title="ĐỀ KIỂM TRA CUỐI HỌC KỲ 2 - TOÁN 8",
            description="Bao quát 4 chủ đề: Hàm số bậc nhất & Phương trình, Định lý Thalès & Tam giác đồng dạng, Xác suất thực nghiệm, Toán thực tế",
            subject="TOÁN HỌC",
            grade=8,
            semester="Học kỳ 2",
            time_minutes=90,
            academic_year="2025 - 2026",
            tags=["Lớp 8", "Học kỳ 2", "Hàm số bậc nhất", "Tam giác đồng dạng", "Thalès", "Bộ GD 2026"],
            slots=slots
        )

    @classmethod
    def get_matrix_8_giuaki2(cls) -> ExamMatrix:
        """Đề Kiểm Tra Giữa Học Kỳ 2 - Toán 8 (Bộ sách Mới 2026: KNTT, Cánh Diều, CTST)."""
        slots = [
            ExamSlot(slot_id="s8g_1", slot_number=1, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Số và Đại số", subtopic="Khái niệm hàm số và mặt phẳng tọa độ Oxy", level=CognitiveLevel.NHAN_BIET, points=0.25),
            ExamSlot(slot_id="s8g_2", slot_number=2, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Số và Đại số", subtopic="Hàm số bậc nhất y = ax + b (a khác 0) và hệ số góc", level=CognitiveLevel.THONG_HIEU, points=0.25),
            ExamSlot(slot_id="s8g_3", slot_number=3, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Số và Đại số", subtopic="Hai đường thẳng song song, cắt nhau trên mặt phẳng tọa độ", level=CognitiveLevel.THONG_HIEU, points=0.25),
            ExamSlot(slot_id="s8g_4", slot_number=4, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Số và Đại số", subtopic="Phương trình bậc nhất một ẩn cơ bản", level=CognitiveLevel.NHAN_BIET, points=0.25),
            ExamSlot(slot_id="s8g_5", slot_number=5, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Hình học và Đo lường", subtopic="Định lý Thalès trong tam giác", level=CognitiveLevel.NHAN_BIET, points=0.25),
            ExamSlot(slot_id="s8g_6", slot_number=6, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Hình học và Đo lường", subtopic="Đường trung bình của tam giác và tính chất", level=CognitiveLevel.THONG_HIEU, points=0.25),
            ExamSlot(slot_id="s8g_7", slot_number=7, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Hình học và Đo lường", subtopic="Hình chóp tam giác đều và hình chóp tứ giác đều", level=CognitiveLevel.NHAN_BIET, points=0.25),
            ExamSlot(slot_id="s8g_8", slot_number=8, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Thống kê và Xác suất", subtopic="Mô tả và biểu diễn dữ liệu trên các bảng, biểu đồ", level=CognitiveLevel.NHAN_BIET, points=0.25),

            ExamSlot(slot_id="s8g_9", slot_number=9, part=2, type=QuestionType.TRUE_FALSE, topic="Số và Đại số", subtopic="Vẽ đồ thị hàm số bậc nhất và tìm giao điểm với các trục tọa độ", level=CognitiveLevel.THONG_HIEU, points=1.0),
            ExamSlot(slot_id="s8g_10", slot_number=10, part=2, type=QuestionType.TRUE_FALSE, topic="Hình học và Đo lường", subtopic="Tính chất đường phân giác trong tam giác và tỉ số đoạn thẳng", level=CognitiveLevel.THONG_HIEU, points=1.0),

            ExamSlot(slot_id="s8g_11", slot_number=11, part=3, type=QuestionType.SHORT_ANSWER, topic="Số và Đại số", subtopic="Giải phương trình đưa được về dạng ax + b = 0", level=CognitiveLevel.THONG_HIEU, points=1.5),
            ExamSlot(slot_id="s8g_12", slot_number=12, part=3, type=QuestionType.SHORT_ANSWER, topic="Toán thực tế & Trải nghiệm", subtopic="Mô hình bài toán chi phí cước taxi hoặc giá bán hàng bằng hàm số bậc nhất", level=CognitiveLevel.VAN_DUNG, points=1.5),
            ExamSlot(slot_id="s8g_13", slot_number=13, part=3, type=QuestionType.SHORT_ANSWER, topic="Hình học và Đo lường", subtopic="Áp dụng định lý Thalès tính chiều cao cây hoặc khoảng cách bờ sông", level=CognitiveLevel.VAN_DUNG, points=1.5),
            ExamSlot(slot_id="s8g_14", slot_number=14, part=3, type=QuestionType.SHORT_ANSWER, topic="Thống kê và Xác suất", subtopic="Tính xác suất thực nghiệm của biến cố trong thử nghiệm nhiều lần", level=CognitiveLevel.VAN_DUNG_CAO, points=1.5),
        ]
        return ExamMatrix(
            id="matrix_8_gk2",
            title="ĐỀ KIỂM TRA GIỮA HỌC KỲ 2 - TOÁN 8",
            description="Bao quát 4 chủ đề bộ sách mới: Hàm số bậc nhất, Định lý Thalès, Hình chóp đều, Xác suất thực nghiệm (GDPT 2018)",
            subject="TOÁN HỌC",
            grade=8,
            semester="Giữa kỳ 2",
            time_minutes=90,
            academic_year="2025 - 2026",
            tags=["Lớp 8", "Giữa kỳ 2", "Hàm số bậc nhất", "Định lý Thalès", "KNTT / CTST / Cánh Diều", "Bộ GD 2026"],
            slots=slots
        )

    # =========================================================================
    # LỚP 9 (TRỌNG TÂM THI VÀO 10 NĂM 2026)
    # =========================================================================
    @classmethod
    def get_matrix_9_hk1(cls) -> ExamMatrix:
        """Đề Kiểm Tra Cuối Học Kỳ 1 - Toán 9 (4 chủ đề chuẩn GDPT 2018)."""
        slots = [
            # Phần I: 8 câu trắc nghiệm (2.0 điểm)
            ExamSlot(slot_id="s9_1", slot_number=1, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Số và Đại số", subtopic="Căn bậc hai và căn thức bậc hai, điều kiện có nghĩa", level=CognitiveLevel.NHAN_BIET, points=0.25),
            ExamSlot(slot_id="s9_2", slot_number=2, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Số và Đại số", subtopic="Các phép biến đổi đưa thừa số ra ngoài/vào trong dấu căn", level=CognitiveLevel.THONG_HIEU, points=0.25),
            ExamSlot(slot_id="s9_3", slot_number=3, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Số và Đại số", subtopic="Căn bậc ba và tính chất", level=CognitiveLevel.NHAN_BIET, points=0.25),
            ExamSlot(slot_id="s9_4", slot_number=4, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Số và Đại số", subtopic="Hệ hai phương trình bậc nhất hai ẩn", level=CognitiveLevel.THONG_HIEU, points=0.25),
            ExamSlot(slot_id="s9_5", slot_number=5, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Hình học và Đo lường", subtopic="Một số hệ thức về cạnh và đường cao trong tam giác vuông", level=CognitiveLevel.NHAN_BIET, points=0.25),
            ExamSlot(slot_id="s9_6", slot_number=6, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Hình học và Đo lường", subtopic="Tỉ số lượng giác của góc nhọn (sin, cos, tan, cot)", level=CognitiveLevel.THONG_HIEU, points=0.25),
            ExamSlot(slot_id="s9_7", slot_number=7, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Hình học và Đo lường", subtopic="Đường tròn, đường kính và dây cung, tiếp tuyến của đường tròn", level=CognitiveLevel.THONG_HIEU, points=0.25),
            ExamSlot(slot_id="s9_8", slot_number=8, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Thống kê và Xác suất", subtopic="Bảng tần số và biểu đồ tần số tương đối", level=CognitiveLevel.NHAN_BIET, points=0.25),

            # Phần II: 2 câu Đúng / Sai (2.0 điểm)
            ExamSlot(slot_id="s9_9", slot_number=9, part=2, type=QuestionType.TRUE_FALSE, topic="Số và Đại số", subtopic="Rút gọn biểu thức chứa căn thức bậc hai và giá trị nguyên", level=CognitiveLevel.THONG_HIEU, points=1.0),
            ExamSlot(slot_id="s9_10", slot_number=10, part=2, type=QuestionType.TRUE_FALSE, topic="Hình học và Đo lường", subtopic="Tính chất hai tiếp tuyến cắt nhau và vị trí tương đối của hai đường tròn", level=CognitiveLevel.THONG_HIEU, points=1.0),

            # Phần III: 4 câu Trả lời ngắn / Tự luận (6.0 điểm)
            ExamSlot(slot_id="s9_11", slot_number=11, part=3, type=QuestionType.SHORT_ANSWER, topic="Số và Đại số", subtopic="Rút gọn biểu thức căn bậc hai và tìm x", level=CognitiveLevel.THONG_HIEU, points=1.5),
            ExamSlot(slot_id="s9_12", slot_number=12, part=3, type=QuestionType.SHORT_ANSWER, topic="Toán thực tế & Trải nghiệm", subtopic="Giải bài toán bằng cách lập hệ phương trình (kinh tế / chuyển động)", level=CognitiveLevel.VAN_DUNG, points=1.5),
            ExamSlot(slot_id="s9_13", slot_number=13, part=3, type=QuestionType.SHORT_ANSWER, topic="Hình học và Đo lường", subtopic="Chứng minh tiếp tuyến và hệ thức hình học trong đường tròn", level=CognitiveLevel.VAN_DUNG, points=1.5),
            ExamSlot(slot_id="s9_14", slot_number=14, part=3, type=QuestionType.SHORT_ANSWER, topic="Toán thực tế lượng giác", subtopic="Bài toán đo đạc chiều cao ngọn hải đăng / tháp truyền hình", level=CognitiveLevel.VAN_DUNG_CAO, points=1.5),
        ]
        return ExamMatrix(
            id="matrix_9_hk1",
            title="ĐỀ KIỂM TRA CUỐI HỌC KỲ 1 - TOÁN 9",
            description="Bao quát 4 chủ đề: Căn thức bậc hai & Hệ phương trình, Hệ thức lượng & Tiếp tuyến đường tròn, Bảng tần số, Toán thực tế",
            subject="TOÁN HỌC",
            grade=9,
            semester="Học kỳ 1",
            time_minutes=90,
            academic_year="2025 - 2026",
            tags=["Lớp 9", "Học kỳ 1", "Căn bậc hai", "Hệ thức lượng", "Đường tròn", "Bộ GD 2026"],
            slots=slots
        )

    @classmethod
    def get_matrix_9_hk2(cls) -> ExamMatrix:
        """Đề Kiểm Tra Cuối Học Kỳ 2 - Toán 9 (Chuẩn Bộ GD&ĐT 2026)."""
        slots = [
            # Phần I: 8 câu trắc nghiệm 4 lựa chọn (2.0 điểm)
            ExamSlot(slot_id="s9b_1", slot_number=1, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Số và Đại số", subtopic="Hàm số y = ax^2 (a khác 0) và đồ thị parabol", level=CognitiveLevel.NHAN_BIET, points=0.25),
            ExamSlot(slot_id="s9b_2", slot_number=2, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Số và Đại số", subtopic="Phương trình bậc hai một ẩn và biệt thức Delta", level=CognitiveLevel.NHAN_BIET, points=0.25),
            ExamSlot(slot_id="s9b_3", slot_number=3, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Số và Đại số", subtopic="Định lý Viète: tính tổng và tích hai nghiệm", level=CognitiveLevel.THONG_HIEU, points=0.25),
            ExamSlot(slot_id="s9b_4", slot_number=4, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Số và Đại số", subtopic="Phương trình quy về phương trình bậc hai (phương trình trùng phương)", level=CognitiveLevel.THONG_HIEU, points=0.25),
            ExamSlot(slot_id="s9b_5", slot_number=5, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Hình học và Đo lường", subtopic="Góc ở tâm, góc nội tiếp của đường tròn", level=CognitiveLevel.NHAN_BIET, points=0.25),
            ExamSlot(slot_id="s9b_6", slot_number=6, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Hình học và Đo lường", subtopic="Dấu hiệu nhận biết tứ giác nội tiếp đường tròn", level=CognitiveLevel.THONG_HIEU, points=0.25),
            ExamSlot(slot_id="s9b_7", slot_number=7, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Hình học và Đo lường", subtopic="Diện tích xung quanh và thể tích hình trụ, hình nón, hình cầu", level=CognitiveLevel.NHAN_BIET, points=0.25),
            ExamSlot(slot_id="s9b_8", slot_number=8, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Thống kê và Xác suất", subtopic="Bảng tần số ghép nhóm và biểu đồ tần số tương đối ghép nhóm", level=CognitiveLevel.THONG_HIEU, points=0.25),

            # Phần II: 2 câu Đúng / Sai (2.0 điểm)
            ExamSlot(slot_id="s9b_9", slot_number=9, part=2, type=QuestionType.TRUE_FALSE, topic="Số và Đại số", subtopic="Biện luận số nghiệm phương trình bậc hai chứa tham số m và hệ thức Vi-et", level=CognitiveLevel.THONG_HIEU, points=1.0),
            ExamSlot(slot_id="s9b_10", slot_number=10, part=2, type=QuestionType.TRUE_FALSE, topic="Hình học và Đo lường", subtopic="Tứ giác nội tiếp, góc tạo bởi tiếp tuyến và dây cung", level=CognitiveLevel.THONG_HIEU, points=1.0),

            # Phần III: 4 câu Trả lời ngắn / Tự luận (6.0 điểm)
            ExamSlot(slot_id="s9b_11", slot_number=11, part=3, type=QuestionType.SHORT_ANSWER, topic="Số và Đại số", subtopic="Hệ thức Viète với biểu thức không đối xứng hoặc tìm m để có 2 nghiệm phân biệt", level=CognitiveLevel.THONG_HIEU, points=1.5),
            ExamSlot(slot_id="s9b_12", slot_number=12, part=3, type=QuestionType.SHORT_ANSWER, topic="Toán thực tế & Trải nghiệm", subtopic="Giải bài toán thực tế bằng cách lập phương trình bậc hai (diện tích, chuyển động)", level=CognitiveLevel.VAN_DUNG, points=1.5),
            ExamSlot(slot_id="s9b_13", slot_number=13, part=3, type=QuestionType.SHORT_ANSWER, topic="Hình học và Đo lường", subtopic="Chứng minh tứ giác nội tiếp và tích hai đoạn thẳng không đổi", level=CognitiveLevel.VAN_DUNG, points=1.5),
            ExamSlot(slot_id="s9b_14", slot_number=14, part=3, type=QuestionType.SHORT_ANSWER, topic="Toán thực tế & Khối tròn xoay", subtopic="Bài toán tối ưu hóa chi phí sản xuất bể chứa nước hoặc thể tích hình nón", level=CognitiveLevel.VAN_DUNG_CAO, points=1.5),
        ]
        return ExamMatrix(
            id="matrix_9_hk2",
            title="ĐỀ KIỂM TRA CUỐI HỌC KỲ 2 - TOÁN 9",
            description="Bao quát 4 chủ đề: Phương trình bậc hai & Vi-et, Góc với đường tròn & Tứ giác nội tiếp, Khối tròn xoay, Bảng tần số & Xác suất",
            subject="TOÁN HỌC",
            grade=9,
            semester="Học kỳ 2",
            time_minutes=90,
            academic_year="2025 - 2026",
            tags=["Lớp 9", "Học kỳ 2", "Phương trình bậc hai", "Hệ thức Vi-et", "Tứ giác nội tiếp", "Bộ GD 2026"],
            slots=slots
        )

    @classmethod
    def get_matrix_9_tuyensinh(cls) -> ExamMatrix:
        """Đề Minh Họa Tuyển Sinh Lớp 10 Năm 2026 (Chuẩn cấu trúc định dạng Bộ GD&ĐT)."""
        slots = [
            # Phần I: 12 câu trắc nghiệm 4 lựa chọn (3.0 điểm, mỗi câu 0.25đ)
            ExamSlot(slot_id="ts9_1", slot_number=1, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Số và Đại số", subtopic="Rút gọn biểu thức chứa căn bậc hai", level=CognitiveLevel.NHAN_BIET, points=0.25),
            ExamSlot(slot_id="ts9_2", slot_number=2, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Số và Đại số", subtopic="Nghiệm của hệ hai phương trình bậc nhất hai ẩn", level=CognitiveLevel.NHAN_BIET, points=0.25),
            ExamSlot(slot_id="ts9_3", slot_number=3, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Số và Đại số", subtopic="Hàm số y = ax^2 (a khác 0) và đồ thị parabol", level=CognitiveLevel.THONG_HIEU, points=0.25),
            ExamSlot(slot_id="ts9_4", slot_number=4, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Số và Đại số", subtopic="Phương trình bậc hai và công thức nghiệm", level=CognitiveLevel.NHAN_BIET, points=0.25),
            ExamSlot(slot_id="ts9_5", slot_number=5, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Số và Đại số", subtopic="Định lý Viète: tính tổng và tích hai nghiệm", level=CognitiveLevel.THONG_HIEU, points=0.25),
            ExamSlot(slot_id="ts9_6", slot_number=6, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Hình học và Đo lường", subtopic="Tỉ số lượng giác góc nhọn trong tam giác vuông", level=CognitiveLevel.NHAN_BIET, points=0.25),
            ExamSlot(slot_id="ts9_7", slot_number=7, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Hình học và Đo lường", subtopic="Góc nội tiếp và góc ở tâm của đường tròn", level=CognitiveLevel.THONG_HIEU, points=0.25),
            ExamSlot(slot_id="ts9_8", slot_number=8, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Hình học và Đo lường", subtopic="Dấu hiệu nhận biết tứ giác nội tiếp đường tròn", level=CognitiveLevel.THONG_HIEU, points=0.25),
            ExamSlot(slot_id="ts9_9", slot_number=9, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Hình học và Đo lường", subtopic="Diện tích xung quanh và thể tích hình trụ, hình nón, hình cầu", level=CognitiveLevel.NHAN_BIET, points=0.25),
            ExamSlot(slot_id="ts9_10", slot_number=10, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Thống kê và Xác suất", subtopic="Bảng tần số ghép nhóm và số đặc trưng đo xu thế trung tâm", level=CognitiveLevel.NHAN_BIET, points=0.25),
            ExamSlot(slot_id="ts9_11", slot_number=11, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Thống kê và Xác suất", subtopic="Tính xác suất của biến cố bằng sơ đồ hình cây", level=CognitiveLevel.THONG_HIEU, points=0.25),
            ExamSlot(slot_id="ts9_12", slot_number=12, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Toán thực tế & Trải nghiệm", subtopic="Bài toán chi phí tiêu dùng / thuế VAT thực tế", level=CognitiveLevel.THONG_HIEU, points=0.25),

            # Phần II: 4 câu Đúng / Sai (4.0 điểm, mỗi câu 1.0đ)
            ExamSlot(slot_id="ts9_13", slot_number=13, part=2, type=QuestionType.TRUE_FALSE, topic="Số và Đại số", subtopic="Khảo sát phương trình bậc hai chứa tham số m và định lý Viète", level=CognitiveLevel.THONG_HIEU, points=1.0),
            ExamSlot(slot_id="ts9_14", slot_number=14, part=2, type=QuestionType.TRUE_FALSE, topic="Toán thực tế & Trải nghiệm", subtopic="Bài toán tối ưu hóa chi phí sản xuất hoặc diện tích thực tế", level=CognitiveLevel.VAN_DUNG, points=1.0),
            ExamSlot(slot_id="ts9_15", slot_number=15, part=2, type=QuestionType.TRUE_FALSE, topic="Hình học và Đo lường", subtopic="Tứ giác nội tiếp và các tính chất tiếp tuyến, đường kính", level=CognitiveLevel.VAN_DUNG, points=1.0),
            ExamSlot(slot_id="ts9_16", slot_number=16, part=2, type=QuestionType.TRUE_FALSE, topic="Thống kê và Xác suất", subtopic="Xác suất biến cố kết hợp và tần số ghép nhóm", level=CognitiveLevel.THONG_HIEU, points=1.0),

            # Phần III: 6 câu Trả lời ngắn / Tự luận (3.0 điểm, mỗi câu 0.5đ)
            ExamSlot(slot_id="ts9_17", slot_number=17, part=3, type=QuestionType.SHORT_ANSWER, topic="Số và Đại số", subtopic="Giải hệ phương trình hoặc phương trình quy về bậc hai", level=CognitiveLevel.VAN_DUNG, points=0.5),
            ExamSlot(slot_id="ts9_18", slot_number=18, part=3, type=QuestionType.SHORT_ANSWER, topic="Toán thực tế & Trải nghiệm", subtopic="Giải bài toán bằng cách lập hệ phương trình chuyển động", level=CognitiveLevel.VAN_DUNG, points=0.5),
            ExamSlot(slot_id="ts9_19", slot_number=19, part=3, type=QuestionType.SHORT_ANSWER, topic="Hình học và Đo lường", subtopic="Tính thể tích vật thể kết hợp hình nón và hình trụ", level=CognitiveLevel.VAN_DUNG, points=0.5),
            ExamSlot(slot_id="ts9_20", slot_number=20, part=3, type=QuestionType.SHORT_ANSWER, topic="Hình học và Đo lường", subtopic="Chứng minh ba điểm thẳng hàng hoặc tiếp tuyến đường tròn", level=CognitiveLevel.VAN_DUNG_CAO, points=0.5),
            ExamSlot(slot_id="ts9_21", slot_number=21, part=3, type=QuestionType.SHORT_ANSWER, topic="Thống kê và Xác suất", subtopic="Tính xác suất trúng thưởng trong trò chơi nhiều vòng", level=CognitiveLevel.VAN_DUNG, points=0.5),
            ExamSlot(slot_id="ts9_22", slot_number=22, part=3, type=QuestionType.SHORT_ANSWER, topic="Số và Đại số", subtopic="Bài toán tìm giá trị lớn nhất, nhỏ nhất (Bất đẳng thức)", level=CognitiveLevel.VAN_DUNG_CAO, points=0.5),
        ]
        return ExamMatrix(
            id="matrix_9_tuyensinh",
            title="ĐỀ MINH HỌA TUYỂN SINH VÀO LỚP 10 NĂM 2026",
            description="Cấu trúc mới nhất của Bộ GD&ĐT: 22 câu (12 TN 4 lựa chọn, 4 Đúng/Sai, 6 Trả lời ngắn), đầy đủ 4 chủ đề",
            subject="TOÁN HỌC",
            grade=9,
            semester="Thi vào 10",
            time_minutes=90,
            academic_year="2025 - 2026",
            tags=["Lớp 9", "Thi vào 10", "Tuyển sinh 2026", "Định lý Viète", "Tứ giác nội tiếp", "Bộ GD 2026"],
            slots=slots
        )

    @classmethod
    def get_matrix_9_kntt_chuyende(cls) -> ExamMatrix:
        """Đề Khảo Sát & Ôn Luyện Chuyên Đề Tuyển Sinh 10 - Bộ Sách Mới (KNTT / CTST / Cánh Diều)."""
        slots = [
            # 12 câu Trắc nghiệm 4 lựa chọn (3.0đ)
            ExamSlot(slot_id="ck9_1", slot_number=1, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Số và Đại số", subtopic="Điều kiện xác định và rút gọn biểu thức chứa căn bậc hai", level=CognitiveLevel.NHAN_BIET, points=0.25),
            ExamSlot(slot_id="ck9_2", slot_number=2, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Số và Đại số", subtopic="Giải hệ hai phương trình bậc nhất hai ẩn", level=CognitiveLevel.NHAN_BIET, points=0.25),
            ExamSlot(slot_id="ck9_3", slot_number=3, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Số và Đại số", subtopic="Hệ số góc của đường thẳng và vị trí tương đối hai đường thẳng", level=CognitiveLevel.THONG_HIEU, points=0.25),
            ExamSlot(slot_id="ck9_4", slot_number=4, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Số và Đại số", subtopic="Đồ thị hàm số y = ax^2 cắt đường thẳng y = mx + n", level=CognitiveLevel.THONG_HIEU, points=0.25),
            ExamSlot(slot_id="ck9_5", slot_number=5, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Số và Đại số", subtopic="Tổng và tích các nghiệm của phương trình bậc hai", level=CognitiveLevel.NHAN_BIET, points=0.25),
            ExamSlot(slot_id="ck9_6", slot_number=6, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Hình học và Đo lường", subtopic="Hệ thức lượng giữa cạnh và đường cao trong tam giác vuông", level=CognitiveLevel.NHAN_BIET, points=0.25),
            ExamSlot(slot_id="ck9_7", slot_number=7, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Hình học và Đo lường", subtopic="Tỉ số lượng giác sin, cos, tan của góc nhọn", level=CognitiveLevel.THONG_HIEU, points=0.25),
            ExamSlot(slot_id="ck9_8", slot_number=8, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Hình học và Đo lường", subtopic="Góc nội tiếp chắn nửa đường tròn", level=CognitiveLevel.NHAN_BIET, points=0.25),
            ExamSlot(slot_id="ck9_9", slot_number=9, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Hình học và Đo lường", subtopic="Thể tích hình cầu và hình trụ thực tế", level=CognitiveLevel.THONG_HIEU, points=0.25),
            ExamSlot(slot_id="ck9_10", slot_number=10, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Thống kê và Xác suất", subtopic="Tần số tương đối ghép nhóm và số trung bình", level=CognitiveLevel.NHAN_BIET, points=0.25),
            ExamSlot(slot_id="ck9_11", slot_number=11, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Thống kê và Xác suất", subtopic="Xác suất cổ điển và mô hình xác suất sơ đồ cây", level=CognitiveLevel.THONG_HIEU, points=0.25),
            ExamSlot(slot_id="ck9_12", slot_number=12, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Toán thực tế & Trải nghiệm", subtopic="Bài toán chiết khấu phần trăm và lãi suất ngân hàng", level=CognitiveLevel.THONG_HIEU, points=0.25),

            # 4 câu Đúng / Sai (4.0đ)
            ExamSlot(slot_id="ck9_13", slot_number=13, part=2, type=QuestionType.TRUE_FALSE, topic="Số và Đại số", subtopic="Phương trình bậc hai chứa tham số m và định lý Viète đối xứng", level=CognitiveLevel.THONG_HIEU, points=1.0),
            ExamSlot(slot_id="ck9_14", slot_number=14, part=2, type=QuestionType.TRUE_FALSE, topic="Toán thực tế & Trải nghiệm", subtopic="Giải bài toán thực tế bằng cách lập hệ phương trình bậc nhất hai ẩn", level=CognitiveLevel.VAN_DUNG, points=1.0),
            ExamSlot(slot_id="ck9_15", slot_number=15, part=2, type=QuestionType.TRUE_FALSE, topic="Hình học và Đo lường", subtopic="Tứ giác nội tiếp và tiếp tuyến chung của hai đường tròn", level=CognitiveLevel.VAN_DUNG, points=1.0),
            ExamSlot(slot_id="ck9_16", slot_number=16, part=2, type=QuestionType.TRUE_FALSE, topic="Thống kê và Xác suất", subtopic="Biểu đồ tần số ghép nhóm và tính xác suất thực tế", level=CognitiveLevel.THONG_HIEU, points=1.0),

            # 6 câu Trả lời ngắn / Tự luận (3.0đ)
            ExamSlot(slot_id="ck9_17", slot_number=17, part=3, type=QuestionType.SHORT_ANSWER, topic="Số và Đại số", subtopic="Rút gọn và tính giá trị nguyên của biểu thức chứa căn", level=CognitiveLevel.THONG_HIEU, points=0.5),
            ExamSlot(slot_id="ck9_18", slot_number=18, part=3, type=QuestionType.SHORT_ANSWER, topic="Số và Đại số", subtopic="Định lý Viète với biểu thức x1^2 + x2^2 hoặc x1 - x2", level=CognitiveLevel.VAN_DUNG, points=0.5),
            ExamSlot(slot_id="ck9_19", slot_number=19, part=3, type=QuestionType.SHORT_ANSWER, topic="Toán thực tế & Trải nghiệm", subtopic="Bài toán chuyển động thực tế trên sông (xuôi dòng, ngược dòng)", level=CognitiveLevel.VAN_DUNG, points=0.5),
            ExamSlot(slot_id="ck9_20", slot_number=20, part=3, type=QuestionType.SHORT_ANSWER, topic="Hình học và Đo lường", subtopic="Chứng minh hệ thức tiếp tuyến và tích cát tuyến", level=CognitiveLevel.VAN_DUNG, points=0.5),
            ExamSlot(slot_id="ck9_21", slot_number=21, part=3, type=QuestionType.SHORT_ANSWER, topic="Hình học và Đo lường", subtopic="Tính thể tích vật thể hình trụ - nón kết hợp", level=CognitiveLevel.VAN_DUNG_CAO, points=0.5),
            ExamSlot(slot_id="ck9_22", slot_number=22, part=3, type=QuestionType.SHORT_ANSWER, topic="Số và Đại số", subtopic="Bất đẳng thức Cauchy / Cực trị đại số tìm min, max", level=CognitiveLevel.VAN_DUNG_CAO, points=0.5),
        ]
        return ExamMatrix(
            id="matrix_9_kntt_chuyende",
            title="ĐỀ ÔN THI TUYỂN SINH 10 - BỘ SÁCH MỚI (KNTT / CTST / CÁNH DIỀU)",
            description="Cấu trúc ma trận chuẩn 22 câu tích hợp 4 chủ đề theo hướng dẫn mới nhất của Bộ GD&ĐT 2026",
            subject="TOÁN HỌC",
            grade=9,
            semester="Thi vào 10",
            time_minutes=90,
            academic_year="2025 - 2026",
            tags=["Lớp 9", "Thi vào 10", "KNTT / CTST / Cánh Diều", "Toán thực tế", "Chuẩn 2026"],
            slots=slots
        )

    # =========================================================================
    # LỚP 10, 11, 12
    # =========================================================================
    @classmethod
    def get_matrix_10_hk1(cls) -> ExamMatrix:
        """Đề Kiểm Tra Cuối Học Kỳ 1 - Toán 10."""
        slots = [
            ExamSlot(slot_id="s10_1", slot_number=1, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Số và Đại số", subtopic="Mệnh đề và tập hợp", level=CognitiveLevel.NHAN_BIET, points=0.25),
            ExamSlot(slot_id="s10_2", slot_number=2, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Số và Đại số", subtopic="Bất phương trình và hệ bất phương trình bậc nhất hai ẩn", level=CognitiveLevel.NHAN_BIET, points=0.25),
            ExamSlot(slot_id="s10_3", slot_number=3, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Hình học và Đo lường", subtopic="Hệ thức lượng trong tam giác và giải tam giác", level=CognitiveLevel.THONG_HIEU, points=0.25),
            ExamSlot(slot_id="s10_4", slot_number=4, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Hình học và Đo lường", subtopic="Vectơ và các phép toán cộng trừ vectơ", level=CognitiveLevel.NHAN_BIET, points=0.25),
            ExamSlot(slot_id="s10_5", slot_number=5, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Hình học và Đo lường", subtopic="Tích vô hướng của hai vectơ", level=CognitiveLevel.THONG_HIEU, points=0.25),
            ExamSlot(slot_id="s10_6", slot_number=6, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Thống kê và Xác suất", subtopic="Các số đặc trưng đo xu thế trung tâm mẫu số liệu", level=CognitiveLevel.NHAN_BIET, points=0.25),
            ExamSlot(slot_id="s10_7", slot_number=7, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Thống kê và Xác suất", subtopic="Khoảng biến thiên và khoảng tứ phân vị", level=CognitiveLevel.THONG_HIEU, points=0.25),
            ExamSlot(slot_id="s10_8", slot_number=8, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Toán thực tế & Trải nghiệm", subtopic="Bài toán đo đạc chiều cao thực tế bằng giác kế", level=CognitiveLevel.THONG_HIEU, points=0.25),

            ExamSlot(slot_id="s10_9", slot_number=9, part=2, type=QuestionType.TRUE_FALSE, topic="Số và Đại số", subtopic="Miền nghiệm hệ bất phương trình và bài toán tối ưu kinh tế", level=CognitiveLevel.VAN_DUNG, points=1.0),
            ExamSlot(slot_id="s10_10", slot_number=10, part=2, type=QuestionType.TRUE_FALSE, topic="Hình học và Đo lường", subtopic="Hệ thức vectơ và định lý sin, cosin trong tam giác", level=CognitiveLevel.THONG_HIEU, points=1.0),

            ExamSlot(slot_id="s10_11", slot_number=11, part=3, type=QuestionType.SHORT_ANSWER, topic="Số và Đại số", subtopic="Xác định tập hợp giao, hợp của các khoảng số thực", level=CognitiveLevel.THONG_HIEU, points=1.5),
            ExamSlot(slot_id="s10_12", slot_number=12, part=3, type=QuestionType.SHORT_ANSWER, topic="Toán thực tế & Trải nghiệm", subtopic="Bài toán tối ưu hóa lợi nhuận sản xuất trên miền nghiệm", level=CognitiveLevel.VAN_DUNG, points=1.5),
            ExamSlot(slot_id="s10_13", slot_number=13, part=3, type=QuestionType.SHORT_ANSWER, topic="Hình học và Đo lường", subtopic="Tính độ dài cạnh hoặc góc bằng định lý cosin", level=CognitiveLevel.VAN_DUNG, points=1.5),
            ExamSlot(slot_id="s10_14", slot_number=14, part=3, type=QuestionType.SHORT_ANSWER, topic="Thống kê và Xác suất", subtopic="Xác định giá trị ngoại lệ và phương sai mẫu số liệu", level=CognitiveLevel.VAN_DUNG_CAO, points=1.5),
        ]
        return ExamMatrix(
            id="matrix_10_hk1",
            title="ĐỀ KIỂM TRA CUỐI HỌC KỲ 1 - TOÁN 10",
            description="Bao quát 4 chủ đề: Mệnh đề & Bất phương trình, Vectơ & Hệ thức lượng, Thống kê số liệu, Toán thực tế",
            subject="TOÁN HỌC",
            grade=10,
            semester="Học kỳ 1",
            time_minutes=90,
            academic_year="2025 - 2026",
            tags=["Lớp 10", "Học kỳ 1", "Mệnh đề", "Vectơ", "Hệ thức lượng"],
            slots=slots
        )

    @classmethod
    def get_matrix_10_hk2(cls) -> ExamMatrix:
        """Đề Kiểm Tra Cuối Học Kỳ 2 - Toán 10."""
        slots = [
            ExamSlot(slot_id="s10b_1", slot_number=1, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Số và Đại số", subtopic="Dấu của tam thức bậc hai", level=CognitiveLevel.NHAN_BIET, points=0.25),
            ExamSlot(slot_id="s10b_2", slot_number=2, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Số và Đại số", subtopic="Bất phương trình bậc hai một ẩn", level=CognitiveLevel.NHAN_BIET, points=0.25),
            ExamSlot(slot_id="s10b_3", slot_number=3, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Số và Đại số", subtopic="Đại số tổ hợp: quy tắc đếm, hoán vị, chỉnh hợp, tổ hợp", level=CognitiveLevel.THONG_HIEU, points=0.25),
            ExamSlot(slot_id="s10b_4", slot_number=4, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Số và Đại số", subtopic="Khai triển nhị thức Newton", level=CognitiveLevel.THONG_HIEU, points=0.25),
            ExamSlot(slot_id="s10b_5", slot_number=5, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Hình học và Đo lường", subtopic="Phương pháp tọa độ Oxy: phương trình đường thẳng", level=CognitiveLevel.NHAN_BIET, points=0.25),
            ExamSlot(slot_id="s10b_6", slot_number=6, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Hình học và Đo lường", subtopic="Phương trình đường tròn trong mặt phẳng Oxy", level=CognitiveLevel.THONG_HIEU, points=0.25),
            ExamSlot(slot_id="s10b_7", slot_number=7, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Hình học và Đo lường", subtopic="Ba đường conic trong mặt phẳng tọa độ (elip, hypebol, parabol)", level=CognitiveLevel.NHAN_BIET, points=0.25),
            ExamSlot(slot_id="s10b_8", slot_number=8, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Thống kê và Xác suất", subtopic="Tính xác suất theo định nghĩa cổ điển", level=CognitiveLevel.THONG_HIEU, points=0.25),

            ExamSlot(slot_id="s10b_9", slot_number=9, part=2, type=QuestionType.TRUE_FALSE, topic="Số và Đại số", subtopic="Tam thức bậc hai chứa tham số m", level=CognitiveLevel.THONG_HIEU, points=1.0),
            ExamSlot(slot_id="s10b_10", slot_number=10, part=2, type=QuestionType.TRUE_FALSE, topic="Hình học và Đo lường", subtopic="Vị trí tương đối và tiếp tuyến của đường tròn Oxy", level=CognitiveLevel.VAN_DUNG, points=1.0),

            ExamSlot(slot_id="s10b_11", slot_number=11, part=3, type=QuestionType.SHORT_ANSWER, topic="Số và Đại số", subtopic="Giải phương trình chứa căn quy về bậc hai", level=CognitiveLevel.THONG_HIEU, points=1.5),
            ExamSlot(slot_id="s10b_12", slot_number=12, part=3, type=QuestionType.SHORT_ANSWER, topic="Toán thực tế & Trải nghiệm", subtopic="Bài toán đường hầm vòm cầu hình elip hoặc parabol", level=CognitiveLevel.VAN_DUNG, points=1.5),
            ExamSlot(slot_id="s10b_13", slot_number=13, part=3, type=QuestionType.SHORT_ANSWER, topic="Số và Đại số", subtopic="Bài toán đếm số tự nhiên thỏa mãn điều kiện", level=CognitiveLevel.VAN_DUNG, points=1.5),
            ExamSlot(slot_id="s10b_14", slot_number=14, part=3, type=QuestionType.SHORT_ANSWER, topic="Thống kê và Xác suất", subtopic="Xác suất chọn đội hình học sinh có điều kiện", level=CognitiveLevel.VAN_DUNG_CAO, points=1.5),
        ]
        return ExamMatrix(
            id="matrix_10_hk2",
            title="ĐỀ KIỂM TRA CUỐI HỌC KỲ 2 - TOÁN 10",
            description="Bao quát 4 chủ đề: Tam thức bậc hai & Tổ hợp, Tọa độ Oxy & Ba đường conic, Xác suất cổ điển, Toán thực tế",
            subject="TOÁN HỌC",
            grade=10,
            semester="Học kỳ 2",
            time_minutes=90,
            academic_year="2025 - 2026",
            tags=["Lớp 10", "Học kỳ 2", "Oxy", "Tổ hợp", "Tam thức bậc hai"],
            slots=slots
        )

    @classmethod
    def get_matrix_11_hk1(cls) -> ExamMatrix:
        """Đề Kiểm Tra Cuối Học Kỳ 1 - Toán 11."""
        slots = [
            ExamSlot(slot_id="s11_1", slot_number=1, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Số và Đại số", subtopic="Hàm số lượng giác và phương trình lượng giác", level=CognitiveLevel.NHAN_BIET, points=0.25),
            ExamSlot(slot_id="s11_2", slot_number=2, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Số và Đại số", subtopic="Dãy số, cấp số cộng và cấp số nhân", level=CognitiveLevel.NHAN_BIET, points=0.25),
            ExamSlot(slot_id="s11_3", slot_number=3, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Số và Đại số", subtopic="Giới hạn của dãy số và giới hạn của hàm số", level=CognitiveLevel.THONG_HIEU, points=0.25),
            ExamSlot(slot_id="s11_4", slot_number=4, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Số và Đại số", subtopic="Hàm số liên tục", level=CognitiveLevel.NHAN_BIET, points=0.25),
            ExamSlot(slot_id="s11_5", slot_number=5, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Hình học và Đo lường", subtopic="Đường thẳng và mặt phẳng trong không gian", level=CognitiveLevel.NHAN_BIET, points=0.25),
            ExamSlot(slot_id="s11_6", slot_number=6, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Hình học và Đo lường", subtopic="Quan hệ song song: đường song song mặt, hai mặt song song", level=CognitiveLevel.THONG_HIEU, points=0.25),
            ExamSlot(slot_id="s11_7", slot_number=7, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Thống kê và Xác suất", subtopic="Các số đặc trưng đo xu thế trung tâm mẫu số liệu ghép nhóm", level=CognitiveLevel.NHAN_BIET, points=0.25),
            ExamSlot(slot_id="s11_8", slot_number=8, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Toán thực tế & Trải nghiệm", subtopic="Bài toán sóng âm / thủy triều mô hình hóa lượng giác", level=CognitiveLevel.THONG_HIEU, points=0.25),

            ExamSlot(slot_id="s11_9", slot_number=9, part=2, type=QuestionType.TRUE_FALSE, topic="Số và Đại số", subtopic="Cấp số cộng, cấp số nhân và bài toán gửi tiết kiệm", level=CognitiveLevel.VAN_DUNG, points=1.0),
            ExamSlot(slot_id="s11_10", slot_number=10, part=2, type=QuestionType.TRUE_FALSE, topic="Hình học và Đo lường", subtopic="Thiết diện cắt bởi mặt phẳng song song trong hình chóp", level=CognitiveLevel.VAN_DUNG, points=1.0),

            ExamSlot(slot_id="s11_11", slot_number=11, part=3, type=QuestionType.SHORT_ANSWER, topic="Số và Đại số", subtopic="Giải phương trình lượng giác trên đoạn", level=CognitiveLevel.THONG_HIEU, points=1.5),
            ExamSlot(slot_id="s11_12", slot_number=12, part=3, type=QuestionType.SHORT_ANSWER, topic="Toán thực tế & Trải nghiệm", subtopic="Bài toán tăng trưởng dân số hoặc lãi suất kép", level=CognitiveLevel.VAN_DUNG, points=1.5),
            ExamSlot(slot_id="s11_13", slot_number=13, part=3, type=QuestionType.SHORT_ANSWER, topic="Hình học và Đo lường", subtopic="Tỉ số diện tích thiết diện trong hình lăng trụ", level=CognitiveLevel.VAN_DUNG, points=1.5),
            ExamSlot(slot_id="s11_14", slot_number=14, part=3, type=QuestionType.SHORT_ANSWER, topic="Thống kê và Xác suất", subtopic="Tìm mốt và trung vị của mẫu số liệu ghép nhóm", level=CognitiveLevel.VAN_DUNG_CAO, points=1.5),
        ]
        return ExamMatrix(
            id="matrix_11_hk1",
            title="ĐỀ KIỂM TRA CUỐI HỌC KỲ 1 - TOÁN 11",
            description="Bao quát 4 chủ đề: Lượng giác & Cấp số cộng, Giới hạn, Hình không gian song song, Thống kê ghép nhóm",
            subject="TOÁN HỌC",
            grade=11,
            semester="Học kỳ 1",
            time_minutes=90,
            academic_year="2025 - 2026",
            tags=["Lớp 11", "Học kỳ 1", "Lượng giác", "Cấp số cộng", "Giới hạn"],
            slots=slots
        )

    @classmethod
    def get_matrix_11_hk2(cls) -> ExamMatrix:
        """Đề Kiểm Tra Cuối Học Kỳ 2 - Toán 11."""
        slots = [
            ExamSlot(slot_id="s11b_1", slot_number=1, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Số và Đại số", subtopic="Hàm số mũ và hàm số logarit", level=CognitiveLevel.NHAN_BIET, points=0.25),
            ExamSlot(slot_id="s11b_2", slot_number=2, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Số và Đại số", subtopic="Phương trình, bất phương trình mũ và logarit cơ bản", level=CognitiveLevel.THONG_HIEU, points=0.25),
            ExamSlot(slot_id="s11b_3", slot_number=3, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Số và Đại số", subtopic="Đạo hàm của các hàm số sơ cấp", level=CognitiveLevel.NHAN_BIET, points=0.25),
            ExamSlot(slot_id="s11b_4", slot_number=4, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Số và Đại số", subtopic="Ý nghĩa hình học của đạo hàm và phương trình tiếp tuyến", level=CognitiveLevel.THONG_HIEU, points=0.25),
            ExamSlot(slot_id="s11b_5", slot_number=5, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Hình học và Đo lường", subtopic="Quan hệ vuông góc: đường thẳng vuông góc với mặt phẳng", level=CognitiveLevel.NHAN_BIET, points=0.25),
            ExamSlot(slot_id="s11b_6", slot_number=6, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Hình học và Đo lường", subtopic="Khoảng cách từ điểm đến mặt phẳng và giữa hai đường chéo nhau", level=CognitiveLevel.THONG_HIEU, points=0.25),
            ExamSlot(slot_id="s11b_7", slot_number=7, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Hình học và Đo lường", subtopic="Góc giữa đường thẳng và mặt phẳng, góc phẳng nhị diện", level=CognitiveLevel.THONG_HIEU, points=0.25),
            ExamSlot(slot_id="s11b_8", slot_number=8, part=1, type=QuestionType.MULTIPLE_CHOICE, topic="Thống kê và Xác suất", subtopic="Biến cố hợp, biến cố giao, quy tắc cộng và nhân xác suất", level=CognitiveLevel.NHAN_BIET, points=0.25),

            ExamSlot(slot_id="s11b_9", slot_number=9, part=2, type=QuestionType.TRUE_FALSE, topic="Số và Đại số", subtopic="Phương trình tiếp tuyến của đồ thị hàm số và chuyển động cơ học", level=CognitiveLevel.VAN_DUNG, points=1.0),
            ExamSlot(slot_id="s11b_10", slot_number=10, part=2, type=QuestionType.TRUE_FALSE, topic="Hình học và Đo lường", subtopic="Chứng minh quan hệ vuông góc và tính khoảng cách trong hình chóp", level=CognitiveLevel.VAN_DUNG, points=1.0),

            ExamSlot(slot_id="s11b_11", slot_number=11, part=3, type=QuestionType.SHORT_ANSWER, topic="Số và Đại số", subtopic="Tính đạo hàm cấp một và viết phương trình tiếp tuyến", level=CognitiveLevel.THONG_HIEU, points=1.5),
            ExamSlot(slot_id="s11b_12", slot_number=12, part=3, type=QuestionType.SHORT_ANSWER, topic="Toán thực tế & Trải nghiệm", subtopic="Bài toán vận tốc tức thời hoặc phóng xạ logarit", level=CognitiveLevel.VAN_DUNG, points=1.5),
            ExamSlot(slot_id="s11b_13", slot_number=13, part=3, type=QuestionType.SHORT_ANSWER, topic="Hình học và Đo lường", subtopic="Tính thể tích hoặc khoảng cách giữa hai đường chéo nhau", level=CognitiveLevel.VAN_DUNG, points=1.5),
            ExamSlot(slot_id="s11b_14", slot_number=14, part=3, type=QuestionType.SHORT_ANSWER, topic="Thống kê và Xác suất", subtopic="Tính xác suất của biến cố trong thực tế", level=CognitiveLevel.VAN_DUNG_CAO, points=1.5),
        ]
        return ExamMatrix(
            id="matrix_11_hk2",
            title="ĐỀ KIỂM TRA CUỐI HỌC KỲ 2 - TOÁN 11",
            description="Bao quát 4 chủ đề: Mũ & Logarit, Đạo hàm & Tiếp tuyến, Quan hệ vuông góc, Xác suất cổ điển",
            subject="TOÁN HỌC",
            grade=11,
            semester="Học kỳ 2",
            time_minutes=90,
            academic_year="2025 - 2026",
            tags=["Lớp 11", "Học kỳ 2", "Đạo hàm", "Logarit", "Hình vuông góc"],
            slots=slots
        )

    @classmethod
    def get_matrix_12_thpt_2025(cls) -> ExamMatrix:
        """Đề Minh Họa Tốt Nghiệp THPT 2025 - 2026 Chuẩn Bộ GD&ĐT."""
        slots = []
        p1 = [
            ("Số và Đại số", "Ứng dụng đạo hàm: Tính đơn điệu của hàm số", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Ứng dụng đạo hàm: Cực trị của hàm số", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Ứng dụng đạo hàm: Giá trị lớn nhất, nhỏ nhất", CognitiveLevel.THONG_HIEU),
            ("Số và Đại số", "Ứng dụng đạo hàm: Đường tiệm cận của đồ thị hàm số", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Ứng dụng đạo hàm: Khảo sát và nhận dạng đồ thị", CognitiveLevel.THONG_HIEU),
            ("Hình học và Đo lường", "Tọa độ vectơ trong không gian Oxyz", CognitiveLevel.NHAN_BIET),
            ("Hình học và Đo lường", "Tích vô hướng và góc trong không gian Oxyz", CognitiveLevel.THONG_HIEU),
            ("Hình học và Đo lường", "Phương trình mặt cầu cơ bản", CognitiveLevel.NHAN_BIET),
            ("Thống kê và Xác suất", "Các số đặc trưng đo độ phân tán mẫu ghép nhóm", CognitiveLevel.NHAN_BIET),
            ("Thống kê và Xác suất", "Xác suất có điều kiện cơ bản", CognitiveLevel.THONG_HIEU),
            ("Toán thực tế & Trải nghiệm", "Bài toán tương giao đồ thị và mô hình hóa chi phí", CognitiveLevel.THONG_HIEU),
            ("Số và Đại số", "Nguyên hàm và tích phân cơ bản", CognitiveLevel.NHAN_BIET),
        ]
        for i, (top, sub, lev) in enumerate(p1, 1):
            slots.append(ExamSlot(slot_id=f"slot_{i}", slot_number=i, part=1, type=QuestionType.MULTIPLE_CHOICE, topic=top, subtopic=sub, level=lev, points=0.25))

        p2 = [
            ("Số và Đại số", "Khảo sát tính biến thiên toàn diện và đồ thị hàm số", CognitiveLevel.THONG_HIEU),
            ("Hình học và Đo lường", "Phương trình mặt phẳng, đường thẳng và khoảng cách Oxyz", CognitiveLevel.VAN_DUNG),
            ("Số và Đại số", "Ứng dụng hình học của tích phân tính diện tích, thể tích", CognitiveLevel.THONG_HIEU),
            ("Thống kê và Xác suất", "Xác suất toàn phần và công thức Bayes trong y tế / kinh tế", CognitiveLevel.VAN_DUNG),
        ]
        for i, (top, sub, lev) in enumerate(p2, 13):
            slots.append(ExamSlot(slot_id=f"slot_{i}", slot_number=i, part=2, type=QuestionType.TRUE_FALSE, topic=top, subtopic=sub, level=lev, points=1.0))

        p3 = [
            ("Toán thực tế & Trải nghiệm", "Bài toán tối ưu hóa / cực trị thực tế (chi phí, dung tích)", CognitiveLevel.VAN_DUNG),
            ("Số và Đại số", "Ứng dụng tích phân tính thể tích vật thể tròn xoay", CognitiveLevel.VAN_DUNG),
            ("Hình học và Đo lường", "Cực trị khoảng cách hình học giải tích Oxyz", CognitiveLevel.VAN_DUNG_CAO),
            ("Thống kê và Xác suất", "Ứng dụng xác suất có điều kiện trong kiểm định chất lượng", CognitiveLevel.VAN_DUNG),
            ("Số và Đại số", "Phương trình, bất phương trình chứa tham số m", CognitiveLevel.VAN_DUNG_CAO),
            ("Hình học và Đo lường", "Mô hình hóa hình học không gian thực tế gắn hệ trục Oxyz", CognitiveLevel.VAN_DUNG),
        ]
        for i, (top, sub, lev) in enumerate(p3, 17):
            slots.append(ExamSlot(slot_id=f"slot_{i}", slot_number=i, part=3, type=QuestionType.SHORT_ANSWER, topic=top, subtopic=sub, level=lev, points=0.5))

        return ExamMatrix(
            id="matrix_12_thpt_2025",
            title="ĐỀ THI TỐT NGHIỆP THPT QUỐC GIA NĂM 2026",
            description="Đề thi chuẩn 22 câu theo format mới nhất của Bộ GD&ĐT (12 TN 4 lựa chọn, 4 Đúng/Sai, 6 Trả lời ngắn), đủ 4 chủ đề",
            subject="TOÁN HỌC",
            grade=12,
            semester="Tốt nghiệp THPT",
            time_minutes=90,
            academic_year="2025 - 2026",
            tags=["Tốt nghiệp THPT", "Bộ GD&ĐT", "Chuẩn 2026", "Lớp 12"],
            slots=slots
        )

    @classmethod
    def get_matrix_12_hk1(cls) -> ExamMatrix:
        """Đề Kiểm Tra Cuối Học Kỳ 1 - Toán 12."""
        slots = []
        p1 = [
            ("Số và Đại số", "Sự đồng biến, nghịch biến của hàm số", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Cực trị của hàm số", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Giá trị lớn nhất, nhỏ nhất trên đoạn", CognitiveLevel.THONG_HIEU),
            ("Số và Đại số", "Đường tiệm cận đứng, tiệm cận ngang", CognitiveLevel.NHAN_BIET),
            ("Số và Đại số", "Đường tiệm cận xiên", CognitiveLevel.THONG_HIEU),
            ("Số và Đại số", "Nhận dạng đồ thị hàm phân thức", CognitiveLevel.THONG_HIEU),
            ("Hình học và Đo lường", "Các phép toán vectơ trong không gian", CognitiveLevel.NHAN_BIET),
            ("Hình học và Đo lường", "Tọa độ điểm và tọa độ vectơ trong hệ Oxyz", CognitiveLevel.NHAN_BIET),
            ("Hình học và Đo lường", "Tích vô hướng và góc giữa hai vectơ", CognitiveLevel.THONG_HIEU),
            ("Thống kê và Xác suất", "Khoảng biến thiên và khoảng tứ vị phân mẫu ghép nhóm", CognitiveLevel.NHAN_BIET),
            ("Thống kê và Xác suất", "Phương sai và độ lệch chuẩn mẫu ghép nhóm", CognitiveLevel.THONG_HIEU),
            ("Toán thực tế & Trải nghiệm", "Mô hình hóa chi phí vận hành bằng đạo hàm", CognitiveLevel.THONG_HIEU),
        ]
        for i, (top, sub, lev) in enumerate(p1, 1):
            slots.append(ExamSlot(slot_id=f"slot_{i}", slot_number=i, part=1, type=QuestionType.MULTIPLE_CHOICE, topic=top, subtopic=sub, level=lev, points=0.25))

        p2 = [
            ("Số và Đại số", "Bài toán toàn diện về hàm số và đồ thị", CognitiveLevel.THONG_HIEU),
            ("Hình học và Đo lường", "Bài toán tìm tọa độ điểm và góc trong không gian Oxyz", CognitiveLevel.VAN_DUNG),
            ("Thống kê và Xác suất", "Phân tích và so sánh độ phân tán của hai mẫu số liệu", CognitiveLevel.THONG_HIEU),
            ("Toán thực tế & Trải nghiệm", "Tối ưu hóa kinh tế / vật lý thực tế", CognitiveLevel.VAN_DUNG),
        ]
        for i, (top, sub, lev) in enumerate(p2, 13):
            slots.append(ExamSlot(slot_id=f"slot_{i}", slot_number=i, part=2, type=QuestionType.TRUE_FALSE, topic=top, subtopic=sub, level=lev, points=1.0))

        p3 = [
            ("Toán thực tế & Trải nghiệm", "Bài toán thực tế chi phí / diện tích tối ưu", CognitiveLevel.VAN_DUNG),
            ("Số và Đại số", "Tìm tham số m để hàm số có cực trị thỏa mãn điều kiện", CognitiveLevel.VAN_DUNG_CAO),
            ("Hình học và Đo lường", "Mô hình hóa hình học không gian thực tế gắn hệ trục Oxyz", CognitiveLevel.VAN_DUNG),
            ("Thống kê và Xác suất", "Tính độ lệch chuẩn của số liệu đo lường", CognitiveLevel.VAN_DUNG),
            ("Số và Đại số", "Tương giao đồ thị chứa tham số", CognitiveLevel.VAN_DUNG_CAO),
            ("Hình học và Đo lường", "Khoảng cách và góc giữa hai đối tượng trong không gian", CognitiveLevel.VAN_DUNG),
        ]
        for i, (top, sub, lev) in enumerate(p3, 17):
            slots.append(ExamSlot(slot_id=f"slot_{i}", slot_number=i, part=3, type=QuestionType.SHORT_ANSWER, topic=top, subtopic=sub, level=lev, points=0.5))

        return ExamMatrix(
            id="matrix_12_hk1",
            title="ĐỀ KIỂM TRA CUỐI HỌC KỲ 1 - TOÁN 12",
            description="Bao quát 4 chủ đề: Khảo sát hàm số, Vectơ Oxyz, Thống kê ghép nhóm, Toán thực tế",
            subject="TOÁN HỌC",
            grade=12,
            semester="Học kỳ 1",
            time_minutes=90,
            academic_year="2025 - 2026",
            tags=["Học kỳ 1", "Lớp 12", "Khảo sát hàm số", "Oxyz"],
            slots=slots
        )

    # =========================================================================
    # CÁC PHƯƠNG THỨC TRUY XUẤT VÀ LƯU TRỮ
    # =========================================================================
    @classmethod
    def get_all_prebuilt_matrices(cls) -> List[ExamMatrix]:
        """Lấy tất cả các ma trận có sẵn từ Lớp 6 đến Lớp 12 chuẩn Bộ GD&ĐT 2026."""
        built_ins = [
            cls.get_matrix_12_thpt_2025(),
            cls.get_matrix_12_hk1(),
            cls.get_matrix_11_hk1(),
            cls.get_matrix_11_hk2(),
            cls.get_matrix_10_hk1(),
            cls.get_matrix_10_hk2(),
            cls.get_matrix_9_tuyensinh(),
            cls.get_matrix_9_kntt_chuyende(),
            cls.get_matrix_9_hk1(),
            cls.get_matrix_9_hk2(),
            cls.get_matrix_8_hk1(),
            cls.get_matrix_8_giuaki2(),
            cls.get_matrix_8_hk2(),
            cls.get_matrix_7_hk1(),
            cls.get_matrix_7_giuaki2(),
            cls.get_matrix_7_hk2(),
            cls.get_matrix_6_hk1(),
            cls.get_matrix_6_giuaki2(),
            cls.get_matrix_6_hk2(),
        ]
        custom_matrices = cls.load_custom_matrices()
        return built_ins + custom_matrices

    @classmethod
    def load_custom_matrices(cls) -> List[ExamMatrix]:
        """Tải các ma trận tùy biến được lưu trong thư mục data/matrices."""
        custom_list = []
        if os.path.exists(CUSTOM_MATRICES_DIR):
            for filename in os.listdir(CUSTOM_MATRICES_DIR):
                if filename.endswith(".json"):
                    file_path = os.path.join(CUSTOM_MATRICES_DIR, filename)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            custom_list.append(ExamMatrix(**data))
                    except Exception:
                        pass
        return custom_list

    @classmethod
    def save_custom_matrix(cls, matrix: ExamMatrix) -> ExamMatrix:
        """Lưu một ma trận mới do giáo viên tự thiết kế."""
        matrix.is_custom = True
        if not matrix.id or matrix.id == "matrix_default":
            matrix.id = f"custom_matrix_{matrix.grade}_{int(os.times().elapsed * 1000)}"
        
        file_path = os.path.join(CUSTOM_MATRICES_DIR, f"{matrix.id}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(matrix.model_dump(), f, ensure_ascii=False, indent=2)
        return matrix

    @classmethod
    def delete_custom_matrix(cls, matrix_id: str) -> bool:
        """Xóa ma trận tùy biến."""
        file_path = os.path.join(CUSTOM_MATRICES_DIR, f"{matrix_id}.json")
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False

    @classmethod
    def get_matrix_by_id(cls, matrix_id: str) -> Optional[ExamMatrix]:
        """Lấy chi tiết ma trận theo ID."""
        for m in cls.get_all_prebuilt_matrices():
            if m.id == matrix_id:
                return m
        return cls.get_matrix_12_thpt_2025()

    @classmethod
    def filter_matrices(cls, grade: Optional[int] = None, semester: Optional[str] = None, search: Optional[str] = None) -> List[ExamMatrix]:
        """Tìm kiếm và lọc ma trận theo Lớp, Học kỳ và từ khóa."""
        matrices = cls.get_all_prebuilt_matrices()
        results = []

        for m in matrices:
            if grade is not None and m.grade != grade:
                continue
            if semester and semester != "Tất cả" and semester != "all" and m.semester != semester:
                continue
            if search and search.strip():
                kw = search.strip().lower()
                text = f"{m.title} {m.description or ''} {' '.join(m.tags)}".lower()
                if kw not in text:
                    continue
            results.append(m)

        return results

    @classmethod
    def generate_excel_template(cls, matrix_id: Optional[str] = None) -> bytes:
        """Tạo file Excel mẫu ma trận để giáo viên tải về chỉnh sửa."""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Ma trận đề thi"

        headers = ["STT", "Phần", "Dạng thức", "Chuyên đề / Chủ đề", "Dạng bài chi tiết", "Mức độ", "Điểm"]
        ws.append(headers)

        header_font = Font(name="Arial", size=11, bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
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
    def parse_excel_matrix(cls, file_bytes: bytes) -> ExamMatrix:
        """Đọc file Excel giáo viên tải lên thành cấu trúc ExamMatrix."""
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
        }

        level_map = {
            "nhận biết": CognitiveLevel.NHAN_BIET,
            "thông hiểu": CognitiveLevel.THONG_HIEU,
            "vận dụng": CognitiveLevel.VAN_DUNG,
            "vận dụng cao": CognitiveLevel.VAN_DUNG_CAO,
        }

        slots: List[ExamSlot] = []
        slot_number = 1

        for row in ws.iter_rows(min_row=2, values_only=True):
            if not row or row[0] is None:
                continue

            part_str = str(row[1]) if len(row) > 1 and row[1] is not None else "1"
            part = 1
            if "2" in part_str or "II" in part_str.upper():
                part = 2
            elif "3" in part_str or "III" in part_str.upper():
                part = 3
            elif "4" in part_str or "IV" in part_str.upper():
                part = 4

            type_str = str(row[2]).lower() if len(row) > 2 and row[2] else "trắc nghiệm"
            q_type = QuestionType.MULTIPLE_CHOICE
            for k, v in type_map.items():
                if k in type_str:
                    q_type = v
                    break

            topic = str(row[3]) if len(row) > 3 and row[3] else "Toán học"
            subtopic = str(row[4]) if len(row) > 4 and row[4] else None

            level_str = str(row[5]).lower() if len(row) > 5 and row[5] else "nhận biết"
            level = CognitiveLevel.NHAN_BIET
            for k, v in level_map.items():
                if k in level_str:
                    level = v
                    break

            points = float(row[6]) if len(row) > 6 and row[6] is not None else 0.25

            slots.append(ExamSlot(
                slot_id=f"slot_{slot_number}",
                slot_number=slot_number,
                part=part,
                type=q_type,
                topic=topic,
                subtopic=subtopic,
                level=level,
                points=points
            ))
            slot_number += 1

        return ExamMatrix(
            id=f"upload_{int(os.times().elapsed * 1000)}",
            title="ĐỀ THI THEO MA TRẬN TẢI LÊN",
            description="Ma trận được bóc tách từ file Excel do giáo viên tải lên",
            subject="TOÁN HỌC",
            grade=12,
            time_minutes=90,
            academic_year="2025 - 2026",
            is_custom=True,
            slots=slots
        )
