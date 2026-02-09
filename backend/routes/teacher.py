import base64
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, Body, UploadFile, File
from pydantic import BaseModel
from pymongo.database import Database

from ..auth.dependencies import require_teacher
from ..database import get_db
from ..ocr.service import run_ocr_on_base64_image
from ..services.grid_excel import extract_grid_marks, append_marks_to_excel
from ..schemas.core import (
    OCRScanResponse,
    SubmitMarksRequest,
    ExamOut,
    StudentOut,
)

router = APIRouter()


def _exam_doc_to_out(doc: dict) -> ExamOut:
    return ExamOut(
        id=str(doc["_id"]),
        name=doc["name"],
        subject_id=str(doc["subject_id"]),
        max_marks=doc["max_marks"],
        date=doc["date"],
    )


def _student_doc_to_out(doc: dict) -> StudentOut:
    return StudentOut(
        id=str(doc["_id"]),
        roll_number=doc["roll_number"],
        name=doc["name"],
        department=doc.get("department"),
        year=doc.get("year"),
        section=doc.get("section"),
    )


@router.get("/exams", response_model=list[ExamOut])
def list_exams_for_teacher(
    _: dict = Depends(require_teacher),
    db: Database = Depends(get_db),
):
    return [_exam_doc_to_out(d) for d in db["exams"].find()]


@router.get("/students", response_model=list[StudentOut])
def search_students(
    search: str = Query("", description="Search by roll number or name"),
    _: dict = Depends(require_teacher),
    db: Database = Depends(get_db),
):
    query: dict = {}
    if search:
        query = {
            "$or": [
                {"roll_number": {"$regex": search, "$options": "i"}},
                {"name": {"$regex": search, "$options": "i"}},
            ]
        }
    return [_student_doc_to_out(d) for d in db["students"].find(query)]


class ScanRequest(BaseModel):
    image_base64: str


@router.post("/scan", response_model=OCRScanResponse)
def scan_marks(
    payload: ScanRequest,
    _: dict = Depends(require_teacher),
):
    entries = run_ocr_on_base64_image(payload.image_base64)
    return OCRScanResponse(entries=entries)


class GridScanResponse(BaseModel):
    marks: list[int]
    total: int
    excel_file: str


@router.post("/scan-grid-excel", response_model=GridScanResponse)
def scan_grid_and_append_excel(
    image_base64: str = Body(..., embed=True),
    excel_file: str | None = Body(None, embed=True),
    rows: int = Body(4, embed=True),
    cols: int = Body(2, embed=True),
    _: dict = Depends(require_teacher),
):
    # excel_file comes as base64 string if provided
    excel_bytes = None
    if excel_file:
        if "," in excel_file:
            _, excel_file = excel_file.split(",", 1)
        excel_bytes = base64.b64decode(excel_file)

    # Use provided rows/cols
    try:
        marks = extract_grid_marks(image_base64, rows=rows, cols=cols)
    except Exception as e:
        if "Tesseract" in str(e):
             raise HTTPException(status_code=500, detail="Server Error: Tesseract OCR is not installed. Please install Tesseract-OCR to use scanning.")
        raise HTTPException(status_code=500, detail=f"OCR Warning: {str(e)}")

    total, updated_excel_bytes = append_marks_to_excel(marks, excel_content=excel_bytes)
    
    updated_excel_b64 = base64.b64encode(updated_excel_bytes).decode("utf-8")
    
    return GridScanResponse(
        marks=marks, 
        total=total, 
        excel_file=updated_excel_b64
    )


@router.post("/submit-marks")
def submit_marks(
    payload: SubmitMarksRequest,
    _: dict = Depends(require_teacher),
    db: Database = Depends(get_db),
):
    try:
        student_oid = ObjectId(payload.student_id)
        exam_oid = ObjectId(payload.exam_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid student or exam ID")

    student = db["students"].find_one({"_id": student_oid})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    exam = db["exams"].find_one({"_id": exam_oid})
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    db["marks"].delete_many({"student_id": student_oid, "exam_id": exam_oid})

    if payload.entries:
        db["marks"].insert_many(
            [
                {
                    "student_id": student_oid,
                    "exam_id": exam_oid,
                    "question_label": entry.question_label,
                    "marks": entry.marks,
                }
                for entry in payload.entries
            ]
        )

    return {"status": "ok"}

