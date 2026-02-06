from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException
from pymongo.database import Database

from ..auth.dependencies import require_admin
from ..database import get_db
from ..schemas.core import (
    ExamCreate,
    ExamOut,
    StudentCreate,
    StudentOut,
    SubjectCreate,
    SubjectOut,
    TeacherCreate,
    TeacherOut,
)

router = APIRouter()


def _student_doc_to_out(doc: dict) -> StudentOut:
    return StudentOut(
        id=str(doc["_id"]),
        roll_number=doc["roll_number"],
        name=doc["name"],
        department=doc.get("department"),
        year=doc.get("year"),
        section=doc.get("section"),
    )


def _teacher_doc_to_out(doc: dict) -> TeacherOut:
    return TeacherOut(
        id=str(doc["_id"]),
        user_id=str(doc["user_id"]),
        name=doc["name"],
        department=doc.get("department"),
    )


def _subject_doc_to_out(doc: dict) -> SubjectOut:
    return SubjectOut(
        id=str(doc["_id"]),
        name=doc["name"],
        code=doc["code"],
    )


def _exam_doc_to_out(doc: dict) -> ExamOut:
    return ExamOut(
        id=str(doc["_id"]),
        name=doc["name"],
        subject_id=str(doc["subject_id"]),
        max_marks=doc["max_marks"],
        date=doc["date"],
    )


@router.post("/students", response_model=StudentOut)
def create_student(
    payload: StudentCreate,
    _: dict = Depends(require_admin),
    db: Database = Depends(get_db),
):
    existing = db["students"].find_one({"roll_number": payload.roll_number})
    if existing:
        raise HTTPException(status_code=400, detail="Student with this roll number exists")
    doc = payload.dict()
    result = db["students"].insert_one(doc)
    doc["_id"] = result.inserted_id
    return _student_doc_to_out(doc)


@router.get("/students", response_model=list[StudentOut])
def list_students(
    _: dict = Depends(require_admin),
    db: Database = Depends(get_db),
):
    return [_student_doc_to_out(d) for d in db["students"].find()]


@router.post("/teachers", response_model=TeacherOut)
def create_teacher(
    payload: TeacherCreate,
    _: dict = Depends(require_admin),
    db: Database = Depends(get_db),
):
    doc = {
        "name": payload.name,
        "department": payload.department,
        "user_id": ObjectId(payload.user_id),
    }
    result = db["teachers"].insert_one(doc)
    doc["_id"] = result.inserted_id
    return _teacher_doc_to_out(doc)


@router.post("/subjects", response_model=SubjectOut)
def create_subject(
    payload: SubjectCreate,
    _: dict = Depends(require_admin),
    db: Database = Depends(get_db),
):
    existing = db["subjects"].find_one({"code": payload.code})
    if existing:
        raise HTTPException(status_code=400, detail="Subject with this code exists")
    doc = payload.dict()
    result = db["subjects"].insert_one(doc)
    doc["_id"] = result.inserted_id
    return _subject_doc_to_out(doc)


@router.post("/exams", response_model=ExamOut)
def create_exam(
    payload: ExamCreate,
    _: dict = Depends(require_admin),
    db: Database = Depends(get_db),
):
    doc = {
        "name": payload.name,
        "subject_id": ObjectId(payload.subject_id),
        "max_marks": payload.max_marks,
        "date": payload.date,
    }
    result = db["exams"].insert_one(doc)
    doc["_id"] = result.inserted_id
    return _exam_doc_to_out(doc)


@router.get("/exams", response_model=list[ExamOut])
def list_exams(
    _: dict = Depends(require_admin),
    db: Database = Depends(get_db),
):
    return [_exam_doc_to_out(d) for d in db["exams"].find()]

