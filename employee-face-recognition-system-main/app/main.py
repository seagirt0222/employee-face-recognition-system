import json
import logging
from pathlib import Path
from typing import List

from fastapi import Depends, FastAPI, File, Form, UploadFile, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import FACE_THRESHOLD, STATIC_DIR, LOG_LEVEL
from app.database import get_db, init_db
from app.face_service import service
from app.logging_config import setup_logging
from app.models import AttendanceRecord, Employee, FaceEmbedding
from app.schemas import AttendanceRecordRead, EmployeeRead

# Setup logging
logger = setup_logging(LOG_LEVEL)

app = FastAPI(
    title="Employee Face Recognition Attendance System",
    description="Production-ready employee attendance system with face recognition",
    version="1.0.0",
)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.on_event("startup")
def startup_event():
    logger.info("Starting up...")
    init_db()
    logger.info("Database initialized")


@app.on_event("shutdown")
def shutdown_event():
    logger.info("Shutting down...")


@app.get("/")
def index():
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.get("/health")
def health():
    logger.info("Health check")
    return {"status": "ok", "version": "1.0.0"}


@app.get("/employees", response_model=List[EmployeeRead])
def list_employees(db: Session = Depends(get_db)):
    employees = db.query(Employee).order_by(Employee.created_at.desc()).all()
    logger.info(f"Listed {len(employees)} employees")
    return employees


@app.post("/employees/register")
async def register_employee(
    employee_id: str = Form(...),
    name: str = Form(...),
    department: str | None = Form(None),
    images: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    if not images:
        logger.warning(f"Registration attempt without images for {employee_id}")
        return JSONResponse(status_code=400, content={"error": "At least one employee image is required"})

    try:
        existing = db.query(Employee).filter(Employee.employee_id == employee_id).first()
        if existing is None:
            employee = Employee(employee_id=employee_id, name=name, department=department)
            db.add(employee)
            db.commit()
            db.refresh(employee)
            logger.info(f"Registered new employee: {employee_id}")
        else:
            employee = existing
            employee.name = name
            employee.department = department
            db.commit()
            logger.info(f"Updated employee: {employee_id}")

        employee_dir = UPLOAD_DIR / employee_id
        employee_dir.mkdir(parents=True, exist_ok=True)

        for old_embedding in db.query(FaceEmbedding).filter(FaceEmbedding.employee_id == employee.id).all():
            db.delete(old_embedding)
        db.commit()

        for index, image in enumerate(images):
            file_bytes = await image.read()
            try:
                embedding = service.extract_embedding(file_bytes)
            except ValueError as e:
                logger.error(f"Face detection failed for {employee_id} image {index + 1}: {str(e)}")
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
        logger.info(f"Successfully registered {len(images)} faces for {employee_id}")
        return {
            "status": "success",
            "employee_id": employee_id,
            "name": name,
            "registered_images": len(images),
        }
    except Exception as e:
        logger.error(f"Error registering employee {employee_id}: {str(e)}")
        return JSONResponse(status_code=500, content={"error": "Internal server error"})


@app.post("/attendance/check")
async def check_attendance(
    photo: UploadFile = File(...),
    mode: str = Form("check_in"),
    threshold: float = Form(FACE_THRESHOLD),
    db: Session = Depends(get_db),
):
    try:
        candidates = db.query(FaceEmbedding).all()
        known_embeddings = []
        for item in candidates:
            known_embeddings.append((item.employee.employee_id, service.parse_embedding(item.embedding)))

        if not known_embeddings:
            logger.warning("Attendance check attempted but no employee faces registered")
            return JSONResponse(status_code=404, content={"error": "No employee faces registered yet"})

        file_bytes = await photo.read()
        matched_employee_id, confidence = service.detect_best_match(file_bytes, known_embeddings)

        if matched_employee_id is None:
            logger.info(f"Attendance check failed - no matching employee (mode: {mode})")
            return {"status": "rejected", "confidence": 0.0, "mode": mode, "message": "No matching employee"}

        employee = db.query(Employee).filter(Employee.employee_id == matched_employee_id).first()
        if employee is None:
            logger.error(f"Employee {matched_employee_id} not found")
            return JSONResponse(status_code=404, content={"error": "Employee not found"})

        if confidence < threshold:
            record = AttendanceRecord(
                employee_id=employee.id,
                mode=mode,
                confidence=confidence,
                image_path="unknown",
                status="rejected",
            )
            db.add(record)
            db.commit()
            logger.warning(f"Attendance rejected for {matched_employee_id} - confidence {confidence:.4f} below threshold {threshold}")
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
            status="success",
        )
        db.add(record)
        db.commit()

        logger.info(f"Attendance recorded for {matched_employee_id} - mode: {mode}, confidence: {confidence:.4f}")
        return {
            "status": "success",
            "employee_id": matched_employee_id,
            "employee_name": employee.name,
            "confidence": confidence,
            "mode": mode,
            "message": "Attendance recorded",
        }
    except Exception as e:
        logger.error(f"Error checking attendance: {str(e)}")
        return JSONResponse(status_code=500, content={"error": "Internal server error"})


@app.get("/attendance", response_model=List[AttendanceRecordRead])
def get_attendance(db: Session = Depends(get_db)):
    records = db.query(AttendanceRecord).order_by(AttendanceRecord.created_at.desc()).limit(100).all()
    return records


@app.get("/attendance/summary")
def attendance_summary(db: Session = Depends(get_db)):
    total = db.query(func.count(AttendanceRecord.id)).scalar() or 0
    unique_employees = db.query(func.count(func.distinct(AttendanceRecord.employee_id))).scalar() or 0
    last_record = db.query(AttendanceRecord).order_by(AttendanceRecord.created_at.desc()).first()
    logger.info(f"Summary requested - total: {total}, unique: {unique_employees}")
    return {
        "total_records": total,
        "unique_employees": unique_employees,
        "latest_record": {
            "employee_id": last_record.employee_id if last_record else None,
            "mode": last_record.mode if last_record else None,
            "created_at": last_record.created_at.isoformat() if last_record else None,
        },
    }
