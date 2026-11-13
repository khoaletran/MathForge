import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.api.endpoints import router as api_router

app = FastAPI(
    title="MathForge",
    description="Pipeline 4 bước sinh đề thi Toán tự động: Ma trận -> AI/RAG -> Khung LaTeX ex_test -> KaTeX Preview & TeX Live",
    version="1.0.0"
)

# Cấu hình CORS để Frontend Next.js / Vite React kết nối thuận tiện
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gắn các route API
app.include_router(api_router, prefix="/api")

# Phục vụ giao diện Frontend tĩnh (nếu đã build)
frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "dist"))
assets_dir = os.path.join(frontend_dist, "assets")

if os.path.exists(assets_dir):
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    # Nếu là route API thì để FastAPI tự xử lý
    if full_path.startswith("api"):
        return None
    file_path = os.path.join(frontend_dist, full_path)
    if os.path.isfile(file_path):
        return FileResponse(file_path)
    index_file = os.path.join(frontend_dist, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "MathForge API is running. Build frontend to view the UI."}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
