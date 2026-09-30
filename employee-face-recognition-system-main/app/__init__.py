import json
from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import FACE_THRESHOLD, STATIC_DIR
from app.database import get_db, init_db
from app.face_service import service
from app.models import AttendanceRecord, Employee, FaceEmbedding
from app.schemas import AttendanceRecordRead, EmployeeRead

app = FastAPI(
    title="Employee Face Recognition Attendance System",
    description="Employee attendance system powered by face recognition",
    version="1.0.0",
)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.on_event("startup")
def startup_event():
    init_db()


@app.get("/")
def index():
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/employees", response_model=list[EmployeeRead])
def list_employees(db: Session = next(get_db())):
    employees = db.query(Employee).order_by(Employee.created_at.desc()).all()
    return employees


@app.post("/employees/register")
async def register_employee(
    employee_id: str = Form(...),
    name: str = Form(...),
    department: str | None = Form(None),
    images: list[UploadFile] = File(...),
    db: Session = next(get_db()),
):
    if not images:
        return JSONResponse(status_code=400, content={"error": "At least one employee image is required"})

    existing = db.query(Employee).filter(Employee.employee_id == employee_id).first()
    if existing is None:
        employee = Employee(employee_id=employee_id, name=name, department=department)
        db.add(employee)
        db.commit()
        db.refresh(employee)
    else:
        employee = existing
        employee.name = name
        employee.department = department
        db.commit()

    employee_dir = UPLOAD_DIR / employee_id
    employee_dir.mkdir(parents=True, exist_ok=True)

    for old_embedding in db.query(FaceEmbedding).filter(FaceEmbedding.employee_id == employee.id).all():
        db.delete(old_embedding)
    db.commit()

    for index, image in enumerate(images):
        file_bytes = await image.read()
        try:
            embedding = service.extract_embedding(file_bytes)
        except ValueError:
            return JSONResponse(status_code=400, content={"error": f"No face detected in image {index + 1}"})

        filename = f"{index + 1}.jpg"
        file_path = employee_dir / filename
        file_path.write_bytes(file_bytes)

        db.add(
            FaceEmbedding(
                employee_id=employee.id,
                embedding=service.serialize_embedding(embedding),
                image_path=str(file_path),
            )
        )

    db.commit()
    return {
        "status": "success",
        "employee_id": employee_id,
        "name": name,
        "registered_images": len(images),
    }


@app.post("/attendance/check")
async def check_attendance(
    photo: UploadFile = File(...),
    mode: str = Form("check_in"),
    threshold: float = Form(FACE_THRESHOLD),
    db: Session = next(get_db()),
):
    candidates = db.query(FaceEmbedding).all()
    known_embeddings = []
    for item in candidates:
        known_embeddings.append((item.employee.employee_id, service.parse_embedding(item.embedding)))

    if not known_embeddings:
        return JSONResponse(status_code=404, content={"error": "No employee faces registered yet"})

    try:
        file_bytes = await photo.read()
        matched_employee_id, confidence = service.detect_best_match(file_bytes, known_embeddings)
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"error": str(exc)})

    if matched_employee_id is None:
        return {"status": "rejected", "confidence": 0.0, "mode": mode, "message": "No matching employee"}

    employee = db.query(Employee).filter(Employee.employee_id == matched_employee_id).first()
    if employee is None:
        return JSONResponse(status_code=404, content={"error": "Employee not found"})

    if confidence < threshold:
        record = AttendanceRecord(
            employee_id=employee.id,
            mode=mode,
            confidence=confidence,
            image_path="unknown",
        )
        db.add(record)
        db.commit()
        return {
            "status": "rejected",
            "employee_id": matched_employee_id,
            "confidence": confidence,
            "mode": mode,
            "message": "Face similarity below threshold",
        }

    record = AttendanceRecord(
        employee_id=employee.id,
        mode=mode,
        confidence=confidence,
        image_path=str(UPLOAD_DIR / matched_employee_id / "capture.jpg"),
    )
    db.add(record)
    db.commit()

    return {
        "status": "success",
        "employee_id": matched_employee_id,
        "employee_name": employee.name,
        "confidence": confidence,
        "mode": mode,
        "message": "Attendance recorded",
    }


@app.get("/attendance", response_model=list[AttendanceRecordRead])
def get_attendance(db: Session = next(get_db())):
    records = db.query(AttendanceRecord).order_by(AttendanceRecord.created_at.desc()).all()
    return records


@app.get("/attendance/summary")
def attendance_summary(db: Session = next(get_db())):
    total = db.query(func.count(AttendanceRecord.id)).scalar() or 0
    unique_employees = db.query(func.count(func.distinct(AttendanceRecord.employee_id))).scalar() or 0
    last_record = db.query(AttendanceRecord).order_by(AttendanceRecord.created_at.desc()).first()
    return {
        "total_records": total,
        "unique_employees": unique_employees,
        "latest_record": {
            "employee_id": last_record.employee_id if last_record else None,
            "mode": last_record.mode if last_record else None,
            "created_at": last_record.created_at.isoformat() if last_record else None,
        },
    }
