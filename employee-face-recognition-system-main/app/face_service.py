import json
from pathlib import Path

import cv2
import numpy as np
from insightface.app import FaceAnalysis


class FaceRecognitionService:
    def __init__(self):
        self.app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
        self.app.prepare(ctx_id=0, det_size=(640, 640))

    def extract_embedding(self, image_bytes: bytes) -> np.ndarray:
        image = self._decode_image(image_bytes)
        faces = self.app.get(image)
        if not faces:
            raise ValueError("No face detected in the image")
        return faces[0].embedding.astype(np.float32)

    def detect_best_match(self, image_bytes: bytes, known_embeddings: list[tuple[str, np.ndarray]]):
        query_embedding = self.extract_embedding(image_bytes)
        best_employee_id = None
        best_similarity = -1.0

        for employee_id, embedding in known_embeddings:
            similarity = self._cosine_similarity(query_embedding, embedding)
            if similarity > best_similarity:
                best_similarity = similarity
                best_employee_id = employee_id

        return best_employee_id, float(best_similarity)

    @staticmethod
    def _decode_image(image_bytes: bytes):
        array = np.frombuffer(image_bytes, dtype=np.uint8)
        image = cv2.imdecode(array, cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError("Invalid image data")
        return image

    @staticmethod
    def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        dot_product = float(np.dot(a, b))
        norm_a = float(np.linalg.norm(a))
        norm_b = float(np.linalg.norm(b))
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return dot_product / (norm_a * norm_b)

    @staticmethod
    def serialize_embedding(embedding: np.ndarray) -> str:
        return json.dumps(embedding.tolist())

    @staticmethod
    def parse_embedding(raw: str) -> np.ndarray:
        values = json.loads(raw)
        return np.array(values, dtype=np.float32)


service = FaceRecognitionService()
