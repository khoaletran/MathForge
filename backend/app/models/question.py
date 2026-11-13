import enum
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field

class QuestionType(str, enum.Enum):
    MULTIPLE_CHOICE = "MULTIPLE_CHOICE"  # Phần I: Trắc nghiệm 4 lựa chọn (A, B, C, D)
    TRUE_FALSE = "TRUE_FALSE"            # Phần II: Trắc nghiệm Đúng / Sai (4 ý a, b, c, d)
    SHORT_ANSWER = "SHORT_ANSWER"        # Phần III: Trắc nghiệm trả lời ngắn
    ESSAY = "ESSAY"                      # Tự luận

class CognitiveLevel(str, enum.Enum):
    NHAN_BIET = "NHAN_BIET"          # Nhận biết
    THONG_HIEU = "THONG_HIEU"        # Thông hiểu
    VAN_DUNG = "VAN_DUNG"            # Vận dụng
    VAN_DUNG_CAO = "VAN_DUNG_CAO"    # Vận dụng cao

class TrueFalseItem(BaseModel):
    statement: str = Field(..., description="Nội dung mệnh đề a, b, c hoặc d")
    is_correct: bool = Field(..., description="Mệnh đề Đúng (True) hay Sai (False)")
    explanation: Optional[str] = Field(None, description="Giải thích ngắn gọn cho mệnh đề")

class Question(BaseModel):
    id: str = Field(..., description="Mã định danh câu hỏi, ví dụ 'c1', 'c2'")
    type: QuestionType = Field(..., description="Dạng thức câu hỏi")
    topic: str = Field(..., description="Chủ đề / Chuyên đề toán học")
    subtopic: Optional[str] = Field(None, description="Dạng bài chi tiết")
    level: CognitiveLevel = Field(..., description="Mức độ nhận thức")
    stem: str = Field(..., description="Đề bài câu hỏi (công thức toán đặt trong $...$)")
    
    # Cho MULTIPLE_CHOICE: 4 phương án lựa chọn
    choices: Optional[List[str]] = Field(None, description="Danh sách 4 phương án cho trắc nghiệm A, B, C, D")
    correct_index: Optional[int] = Field(None, description="Chỉ số đáp án đúng (0: A, 1: B, 2: C, 3: D)")
    
    # Cho TRUE_FALSE: 4 mệnh đề
    statements: Optional[List[TrueFalseItem]] = Field(None, description="4 mệnh đề Đúng/Sai cho Phần II")
    
    # Cho SHORT_ANSWER: Kết quả điền số hoặc phân số
    correct_value: Optional[str] = Field(None, description="Đáp số cần điền, ví dụ: '3/4' hoặc '12.5'")
    
    # Chung
    solution: str = Field(..., description="Lời giải chi tiết từng bước (Chain-of-thought)")
    tikz_code: Optional[str] = Field(None, description="Mã TikZ hoặc tkz-tab (bảng biến thiên, hình không gian)")
    sympy_code: Optional[str] = Field(None, description="Đoạn mã SymPy để kiểm tra nghiệm/đáp án")
    verified: Optional[bool] = Field(False, description="Đã được kiểm chứng toán học bằng SymPy hay chưa")
    template_id: Optional[str] = Field(None, description="Mã định danh template sinh câu hỏi")
    rubric: Optional[Dict[str, float]] = Field(None, description="Thang điểm chi tiết cho câu tự luận")

class ExamSlot(BaseModel):
    slot_id: str
    slot_number: int
    part: int = Field(1, description="Phần thi: 1, 2, 3 hoặc 4")
    type: QuestionType
    topic: str
    subtopic: Optional[str] = None
    level: CognitiveLevel
    points: float = 0.25

class ExamMatrix(BaseModel):
    id: str = "matrix_default"
    title: str = "ĐỀ THI TỐT NGHIỆP THPT QUỐC GIA NĂM 2025"
    description: Optional[str] = "Ma trận chuẩn theo định dạng mới GDPT 2018 của Bộ GD&ĐT"
    subject: str = "TOÁN HỌC"
    grade: int = 12
    semester: Optional[str] = "Tốt nghiệp THPT"
    time_minutes: int = 90
    academic_year: str = "2024 - 2025"
    tags: List[str] = Field(default_factory=list)
    is_custom: bool = False
    slots: List[ExamSlot] = Field(default_factory=list)

class ExamPaper(BaseModel):
    reference_sources: List[Dict[str, str]] = Field(default_factory=list)
    id: str
    title: str
    school_name: str = "SỞ GIÁO DỤC VÀ ĐÀO TẠO"
    exam_name: str = "KỲ THI THỬ TỐT NGHIỆP THPT"
    academic_year: str = "2024 - 2025"
    exam_code: str = "101"
    time_minutes: int = 90
    questions: List[Question] = Field(default_factory=list)
