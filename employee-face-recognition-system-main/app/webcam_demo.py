import os
import json
from pathlib import Path
from typing import List

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import JSONResponse

from database import (
    ensure_db,
    get_embeddings,
    list_attendance,
    list_employees,
    save_attendance_record,
    save_employee,
    save_embedding,
)
from face_service import service

app = FastAPI(title="Employee Face Recognition Attendance Demo")

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
EMPLOYEE_DIR = DATA_DIR / "employees"
EMPLOYEE_DIR.mkdir(parents=True, exist_ok=True)


def serialize_embedding(embedding) -> str:
    return json.dumps(embedding.tolist())


def parse_embedding(raw_string: str):
    values = json.loads(raw_string)
    return np.array(values, dtype=float)


@app.on_event("startup")
def startup_event():
    ensure_db()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/employees")
def get_employees():
    return {"employees": list_employees()}


@app.post("/employees/register")
async def register_employee(
    employee_id: str = Form(...),
    name: str = Form(...),
    images: List[UploadFile] = File(...),
):
    if not images:
        return JSONResponse(status_code=400, content={"error": "No images uploaded"})

    employee_dir = EMPLOYEE_DIR / employee_id
    employee_dir.mkdir(parents=True, exist_ok=True)

    save_employee(employee_id, name)

    for index, image in enumerate(images):
        file_bytes = await image.read()
        try:
            embedding = service.extract_embedding(file_bytes)
        except ValueError:
            return JSONResponse(status_code=400, content={"error": f"No face detected in image {index + 1}"})

        filename = f"{index + 1}.jpg"
        file_path = employee_dir / filename
        file_path.write_bytes(file_bytes)

        save_embedding(employee_id, serialize_embedding(embedding), str(file_path))

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
    threshold: float = Form(0.8),
):
    records = get_embeddings()
    known_embeddings = []
    for row in records:
        embedding = parse_embedding(row["embedding"])
        known_embeddings.append((row["employee_id"], embedding, row["image_path"]))

    if not known_embeddings:
        return JSONResponse(status_code=404, content={"error": "No employee faces registered yet"})

    try:
        file_bytes = await photo.read()
        best_match, confidence = service.detect_and_compare(file_bytes, known_embeddings)
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"error": str(exc)})

    if best_match is None:
        return {"status": "unknown", "mode": mode, "confidence": 0.0}

    employee_id, image_path = best_match
    if confidence < threshold:
        result = {
            "status": "rejected",
            "employee_id": employee_id,
            "confidence": confidence,
            "mode": mode,
            "message": "Face similarity below threshold",
        }
        save_attendance_record(employee_id, mode, confidence, image_path)
        return result

    save_attendance_record(employee_id, mode, confidence, image_path)

    return {
        "status": "success",
        "employee_id": employee_id,
        "mode": mode,
        "confidence": confidence,
        "image_path": image_path,
    }


@app.get("/attendance")
def attendance_records():
    return {"records": list_attendance()}
