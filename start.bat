@echo off
chcp 65001 > nul
echo =====================================================================
echo    HỆ THỐNG SINH ĐỀ THI TOÁN THPT BẰNG AI (CHUẨN ex_test.sty & 2025)
echo =====================================================================
echo.
echo Đang khởi động Backend FastAPI và Web UI...
echo Mở trình duyệt tại địa chỉ: http://127.0.0.1:8000
echo.

cd /d "%~dp0"
python backend\main.py

pause
