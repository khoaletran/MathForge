import os
import shutil
import tempfile
import subprocess
import logging
from typing import Tuple, Optional
from app.templates.ex_test import EX_TEST_STY_CONTENT

logger = logging.getLogger(__name__)

class CompilerService:
    """
    Dịch vụ biên dịch mã nguồn LaTeX sang file PDF:
    - Ưu tiên 1: Chạy pdflatex / xelatex nội bộ nếu có trong PATH
    - Ưu tiên 2: Chạy qua Docker Container TeX Live (cách ly bảo mật)
    - Fallback: Trả về thông báo hướng dẫn và xuất file .tex + ex_test.sty
    """

    @classmethod
    def check_local_compiler(cls) -> Optional[str]:
        """Kiểm tra xem hệ thống có pdflatex hoặc xelatex không."""
        for cmd in ['xelatex', 'pdflatex']:
            if shutil.which(cmd):
                return cmd
        return None

    @classmethod
    def check_docker_available(cls) -> bool:
        """Kiểm tra xem Docker daemon có đang chạy không."""
        try:
            res = subprocess.run(
                ["docker", "info"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=3
            )
            return res.returncode == 0
        except Exception:
            return False

    @classmethod
    def compile_latex(cls, tex_code: str, job_name: str = "de_thi") -> Tuple[bool, Optional[bytes], str]:
        """
        Biên dịch chuỗi mã nguồn LaTeX sang bytes PDF.
        Trả về: (thành_công, dữ_liệu_pdf_bytes, log_thông_báo)
        """
        temp_dir = tempfile.mkdtemp(prefix="latex_build_")
        try:
            # 1. Ghi file .tex
            tex_file_path = os.path.join(temp_dir, f"{job_name}.tex")
            with open(tex_file_path, "w", encoding="utf-8") as f:
                f.write(tex_code)

            # 2. Ghi kèm file ex_test.sty vào cùng thư mục để LaTeX load được ngay
            sty_file_path = os.path.join(temp_dir, "ex_test.sty")
            with open(sty_file_path, "w", encoding="utf-8") as f:
                f.write(EX_TEST_STY_CONTENT)

            local_cmd = cls.check_local_compiler()
            if local_cmd:
                logger.info(f"Biên dịch bằng công cụ local: {local_cmd}")
                cmd = [local_cmd, "-interaction=nonstopmode", f"{job_name}.tex"]
                proc = subprocess.run(cmd, cwd=temp_dir, capture_output=True, text=True, timeout=60)
                pdf_path = os.path.join(temp_dir, f"{job_name}.pdf")
                if os.path.exists(pdf_path):
                    with open(pdf_path, "rb") as f:
                        return True, f.read(), "Biên dịch PDF cục bộ thành công"
                return False, None, f"Lỗi biên dịch: {proc.stdout[-500:] if proc.stdout else proc.stderr}"

            if cls.check_docker_available():
                logger.info("Biên dịch qua Docker container TeX Live")
                # Chạy container TeX Live
                docker_cmd = [
                    "docker", "run", "--rm",
                    "-v", f"{temp_dir}:/workdir",
                    "-w", "/workdir",
                    "texlive/texlive:latest",
                    "pdflatex", "-interaction=nonstopmode", f"{job_name}.tex"
                ]
                proc = subprocess.run(docker_cmd, capture_output=True, text=True, timeout=120)
                pdf_path = os.path.join(temp_dir, f"{job_name}.pdf")
                if os.path.exists(pdf_path):
                    with open(pdf_path, "rb") as f:
                        return True, f.read(), "Biên dịch PDF qua Docker thành công"
                return False, None, f"Lỗi biên dịch qua Docker: {proc.stderr}"

            return False, None, (
                "Chưa tìm thấy pdflatex cục bộ hoặc Docker chưa được bật. "
                "Bạn có thể tải về file mã nguồn .tex để mở và biên dịch bằng TeXstudio, Overleaf hoặc kích hoạt Docker."
            )

        except Exception as e:
            return False, None, f"Lỗi ngoại lệ khi biên dịch: {str(e)}"
        finally:
            # Dọn dẹp thư mục tạm
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception:
                pass
