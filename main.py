import os
from fastapi import FastAPI
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

from models import Attendance

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

app = FastAPI()

@app.get("/")
def root():
    return {"message": "API is running"}

@app.get("/health/db")
def db_health():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1")).scalar()
    return {"database_ok": result == 1}

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/upload-attendance")
async def upload_attendance(
    assistant: str = Form(...),
    group: str = Form(...),
    theme: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")

    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    record = Attendance(
        assistant=assistant,
        group=group,
        theme=theme,
        csv_blob=file_bytes,
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return {
        "message": "File stored successfully",
        "id": record.id,
    }
