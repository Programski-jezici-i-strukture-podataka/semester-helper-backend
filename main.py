import os
from fastapi import FastAPI, Form, File, UploadFile, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from dotenv import load_dotenv
from typing import Generator
import logging

from models import Base, Attendance, Student
from csvhelper import parse_csv_binary_to_entities
import csv
import io

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",                           # Angular dev
        "https://semester-helper-frontend.vercel.app",     # production frontend
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

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

@app.post("/upload-student")
async def upload_students(
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

    
    students = parse_csv_binary_to_entities(file_bytes, Student)

    db.add_all(students)
    db.commit()

    return {
        "message": "File stored successfully",
        "imported": len(students)
    }

@app.put("/upload-test-scores")
async def upload_test_scores(
    test: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    score_column_by_test = {
        "T1": "t1_score",
        "T2": "t2_score",
        "T3": "t3_score",
        "PI1": "first_partial_score",
        "PI2": "second_partial_score",
    }

    test = test.upper()

    if test not in score_column_by_test:
        raise HTTPException(status_code=400, detail="Test must be T1, T2 or T3, PI1 or PI2")

    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")

    content = await file.read()

    try:
        decoded = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="CSV must be UTF-8 encoded")

    reader = csv.DictReader(io.StringIO(decoded))

    required_columns = ["Broj indeksa", "Broj poena"] if test == "T1" or test == "T2" or test == "T3" else ["indeks", "poeni"]

    if not reader.fieldnames or [col for col in required_columns if col not in reader.fieldnames]:
        raise HTTPException(
            status_code=400,
            detail='CSV must contain columns: "Broj indeksa", "Broj poena" for Tests or "indeks", "poeni" for Partial exams',
        )

    score_attr = score_column_by_test[test]

    updated = 0
    not_found = []
    invalid_rows = []

    for row_number, row in enumerate(reader, start=2):
        student_id = row.get(required_columns[0], "").strip()
        points_raw = row.get(required_columns[1], "").strip()

        if not student_id:
            invalid_rows.append({"row": row_number, "reason": "Missing Broj indeksa"})
            continue

        try:
            points = int(points_raw)
        except ValueError:
            invalid_rows.append({
                "row": row_number,
                "student_id": student_id,
                "reason": "Invalid Broj poena",
            })
            continue

        student = db.query(Student).filter(Student.student_id == student_id).first()

        if not student:
            not_found.append(student_id)
            continue

        setattr(student, score_attr, points)
        updated += 1

    db.commit()

    return {
        "message": f"{test} scores uploaded",
        "updated": updated,
        "not_found": not_found,
        "invalid_rows": invalid_rows,
    }
