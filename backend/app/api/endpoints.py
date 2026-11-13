import os
import random
import copy
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Response, Query
from pydantic import BaseModel

from app.models.question import ExamMatrix, ExamSlot, Question, ExamPaper, QuestionType
from app.services.matrix_service import MatrixService
from app.services.latex_service import LaTeXService
from app.services.ai_service import AIService
from app.services.sympy_service import SympyVerifier
from app.services.compiler_service import CompilerService

router = APIRouter()

class GenerateSlotRequest(BaseModel):
    slot: ExamSlot
    custom_prompt: Optional[str] = None
    api_key: Optional[str] = None

class GenerateExamRequest(BaseModel):
    matrix: ExamMatrix
    school_name: str = "SỞ GIÁO DỤC VÀ ĐÀO TẠO"
    exam_name: str = "KỲ THI TỐT NGHIỆP TRUNG HỌC PHỔ THÔNG NĂM 2025"
    academic_year: str = "2024 - 2025"
    exam_code: str = "101"
    api_key: Optional[str] = None

class VerifyMathRequest(BaseModel):
    code: str

class ExportLaTeXRequest(BaseModel):
    paper: ExamPaper
    include_solution: bool = True

class ShuffleRequest(BaseModel):
    paper: ExamPaper
    codes: List[str] = ["101", "102", "103", "104"]

@router.get("/health")
def health_check():
    """Kiểm tra tình trạng các dịch vụ phụ trợ."""
    has_gemini = bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))
    local_compiler = CompilerService.check_local_compiler()
    docker_ready = CompilerService.check_docker_available()
    
    return {
        "status": "online",
        "gemini_api_configured": has_gemini,
        "local_latex_compiler": local_compiler,
        "docker_available": docker_ready,
        "sympy_version": "1.14.0",
        "supported_standards": ["GDPT 2018", "ex_test.sty", "tkz-tab"]
    }

@router.get("/matrix/library", response_model=List[ExamMatrix])
def get_matrix_library(
    grade: Optional[int] = Query(None),
    semester: Optional[str] = Query(None),
    search: Optional[str] = Query(None)
):
    """Lấy danh mục ma trận có sẵn và tùy biến của giáo viên theo Lớp/Kỳ/Từ khóa."""
    return MatrixService.filter_matrices(grade=grade, semester=semester, search=search)

@router.get("/matrix/default", response_model=ExamMatrix)
def get_default_matrix():
    """Lấy ma trận đề thi chuẩn 2025 (22 câu)."""
    return MatrixService.get_matrix_12_thpt_2025()

@router.get("/matrix/{matrix_id}", response_model=ExamMatrix)
def get_matrix_detail(matrix_id: str):
    """Lấy chi tiết một ma trận theo ID."""
    m = MatrixService.get_matrix_by_id(matrix_id)
    if not m:
        raise HTTPException(status_code=404, detail="Không tìm thấy ma trận")
    return m

@router.post("/matrix/save", response_model=ExamMatrix)
def save_matrix(matrix: ExamMatrix):
    """Lưu ma trận mới hoặc cập nhật ma trận của giáo viên."""
    return MatrixService.save_custom_matrix(matrix)

@router.delete("/matrix/{matrix_id}")
def delete_matrix(matrix_id: str):
    """Xóa ma trận tùy biến."""
    success = MatrixService.delete_custom_matrix(matrix_id)
    if not success:
        raise HTTPException(status_code=400, detail="Không thể xóa ma trận hệ thống hoặc ma trận không tồn tại")
    return {"success": True, "deleted_id": matrix_id}

@router.get("/matrix/download-template")
def download_excel_template(matrix_id: Optional[str] = None):
    """Tải file Excel mẫu ma trận đề thi."""
    excel_bytes = MatrixService.generate_excel_template(matrix_id)
    filename = f"Ma_tran_{matrix_id or 'chuan_2025'}.xlsx"
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.post("/matrix/upload-excel", response_model=ExamMatrix)
async def upload_excel_matrix(file: UploadFile = File(...)):
    """Tải file Excel ma trận lên để hệ thống bóc tách thành danh sách slots."""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Vui lòng tải lên file Excel (.xlsx)")
    
    contents = await file.read()
    try:
        matrix = MatrixService.parse_excel_matrix(contents)
        return matrix
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Không thể đọc file Excel: {str(e)}")

@router.post("/generate/slot", response_model=Question)
def generate_single_slot(req: GenerateSlotRequest):
    """Sinh hoặc sinh lại 1 câu hỏi cho 1 slot ma trận (nút 'Đổi câu khác')."""
    ai_service = AIService(api_key=req.api_key)
    try:
        question = ai_service.generate_question(req.slot, req.custom_prompt)
        return question
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi sinh câu hỏi: {str(e)}")

@router.post("/generate/exam", response_model=ExamPaper)
def generate_full_exam(req: GenerateExamRequest):
    """Sinh toàn bộ câu hỏi cho các slots trong ma trận."""
    ai_service = AIService(api_key=req.api_key)
    questions = []
    
    for slot in req.matrix.slots:
        q = ai_service.generate_question(slot)
        questions.append(q)

    paper = ExamPaper(
        id=f"exam_{req.exam_code}",
        title=req.matrix.title,
        school_name=req.school_name,
        exam_name=req.exam_name,
        academic_year=req.academic_year,
        exam_code=req.exam_code,
        time_minutes=req.matrix.time_minutes,
        questions=questions
    )
    return paper

@router.post("/generate/shuffle", response_model=Dict[str, ExamPaper])
def shuffle_exam(req: ShuffleRequest):
    """
    Trộn mã đề thi thành các mã khác nhau (VD: 101, 102, 103, 104)
    Giữ nguyên thứ tự câu hỏi theo từng Phần, đảo hoán vị các đáp án A, B, C, D của Phần I.
    """
    results: Dict[str, ExamPaper] = {}
    orig = req.paper

    for code in req.codes:
        new_paper = copy.deepcopy(orig)
        new_paper.id = f"exam_{code}"
        new_paper.exam_code = code

        # Trộn các phương án của câu trắc nghiệm 4 lựa chọn (Phần I)
        shuffled_questions = []
        for q in new_paper.questions:
            q_copy = copy.deepcopy(q)
            if q_copy.type == QuestionType.MULTIPLE_CHOICE and q_copy.choices and len(q_copy.choices) == 4:
                # Trộn 4 phương án
                indices = [0, 1, 2, 3]
                random.shuffle(indices)
                old_choices = q_copy.choices
                new_choices = [old_choices[idx] for idx in indices]
                # Cập nhật lại correct_index
                if q_copy.correct_index is not None:
                    q_copy.correct_index = indices.index(q_copy.correct_index)
                q_copy.choices = new_choices
            shuffled_questions.append(q_copy)

        new_paper.questions = shuffled_questions
        results[code] = new_paper

    return results

@router.post("/verify/math")
def verify_math(req: VerifyMathRequest):
    """Kiểm tra tính đúng đắn của biểu thức toán học hoặc code SymPy."""
    success, result, msg = SympyVerifier.execute_code(req.code)
    return {
        "success": success,
        "result": str(result) if result is not None else None,
        "message": msg
    }

@router.post("/export/latex")
def export_latex(req: ExportLaTeXRequest):
    """Ghép khung LaTeX chuẩn `ex_test.sty` từ danh sách câu hỏi."""
    latex_code = LaTeXService.generate_full_exam_latex(req.paper, include_solution=req.include_solution)
    return {
        "latex_code": latex_code,
        "char_count": len(latex_code),
        "question_count": len(req.paper.questions)
    }

@router.post("/export/compile-pdf")
def compile_pdf(req: ExportLaTeXRequest):
    """Biên dịch sang PDF bằng TeX Live (Docker hoặc pdflatex local)."""
    latex_code = LaTeXService.generate_full_exam_latex(req.paper, include_solution=req.include_solution)
    success, pdf_bytes, log = CompilerService.compile_latex(latex_code, job_name=f"de_thi_{req.paper.exam_code}")
    
    if success and pdf_bytes:
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=De_thi_{req.paper.exam_code}.pdf"}
        )
    else:
        return {
            "success": False,
            "message": log,
            "latex_code": latex_code
        }
