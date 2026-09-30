from datetime import datetime

from pydantic import BaseModel, Field


class EmployeeBase(BaseModel):
    employee_id: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=128)
    department: str | None = None


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeRead(EmployeeBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class FaceEmbeddingRead(BaseModel):
    id: int
    employee_id: int
    image_path: str
    created_at: datetime

    class Config:
        from_attributes = True


class AttendanceRecordRead(BaseModel):
    id: int
    employee_id: int
    mode: str
    confidence: float
    image_path: str | None
    created_at: datetime

    class Config:
        from_attributes = True
