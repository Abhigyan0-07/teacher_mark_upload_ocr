from datetime import date
from typing import List, Optional

from pydantic import BaseModel


class StudentBase(BaseModel):
    roll_number: str
    name: str
    department: Optional[str] = None
    year: Optional[str] = None
    section: Optional[str] = None


class StudentCreate(StudentBase):
    pass


class StudentOut(StudentBase):
    id: str

    class Config:
        orm_mode = True


class TeacherBase(BaseModel):
    name: str
    department: Optional[str] = None


class TeacherCreate(TeacherBase):
    user_id: str


class TeacherOut(TeacherBase):
    id: str
    user_id: str

    class Config:
        orm_mode = True


class SubjectBase(BaseModel):
    name: str
    code: str


class SubjectCreate(SubjectBase):
    pass


class SubjectOut(SubjectBase):
    id: str

    class Config:
        orm_mode = True


class ExamBase(BaseModel):
    name: str
    subject_id: str
    max_marks: int
    date: date


class ExamCreate(ExamBase):
    pass


class ExamOut(ExamBase):
    id: str

    class Config:
        orm_mode = True


class MarkItem(BaseModel):
    question_label: str
    marks: int


class SubmitMarksRequest(BaseModel):
    student_id: str
    exam_id: str
    entries: List[MarkItem]


class OCRScanResponse(BaseModel):
    entries: List[MarkItem]

