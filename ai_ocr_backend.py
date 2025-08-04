from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
from PIL import Image
import numpy as np
import cv2
import io
import re
import pytesseract
import hashlib
import json
from pdf2image import convert_from_bytes
import easyocr

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

easyocr_reader = easyocr.Reader(['en'])

# 📌 Image Preprocessing Function
def preprocess_image(pil_img: Image.Image) -> np.ndarray:
    img = np.array(pil_img.convert("RGB"))
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    denoised = cv2.fastNlMeansDenoising(gray, h=10)
    _, thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thresh

# 📌 Field Extraction Function
def extract_fields(text: str) -> Dict[str, str]:
    fields = {
        "issuance_date": re.search(r"(?:issued|dated)?\s*(\d{1,2}[-/ ]\d{1,2}[-/ ]\d{4})", text, re.IGNORECASE),
        "certificate_holder": re.search(r"certify that\s+([A-Z][a-z]+\s+[A-Z][a-z]+)", text, re.IGNORECASE),
        "program_name": re.search(r"completed the\s+(.*?)\s+held during", text, re.IGNORECASE),
        "certificate_id": re.search(r"Certificate ID[:\-]?\s*([0-9]+)", text, re.IGNORECASE),
        "issuer": re.search(r"Dr\.\s+([^\n]+)", text)
    }

    return {
        key: (match.group(1).strip() if match else "")
        for key, match in fields.items()
    }

@app.post("/extract_fields")
async def extract_fields_endpoint(file: UploadFile = File(...), engine: str = Form(...)):
    content = await file.read()
    images = []

    if file.filename.lower().endswith(".pdf"):
        images = convert_from_bytes(content, dpi=400)
        images = [img.convert("RGB") for img in images]
    else:
        img = Image.open(io.BytesIO(content)).convert("RGB")
        images = [img]

    text = ""

    for img in images:
        preprocessed_img = preprocess_image(img)

        if engine == "easyocr":
            result = easyocr_reader.readtext(preprocessed_img)
            text += "\n".join([r[1] for r in result]) + "\n"
        else:
            config = r'--oem 3 --psm 6'
            text += pytesseract.image_to_string(preprocessed_img, config=config) + "\n"

    fields = extract_fields(text)
    structured_data = {**fields, "raw": text.strip()}
    json_output = json.dumps(structured_data, indent=2)
    hash_output = hashlib.sha256(json_output.encode()).hexdigest()

    return {
        "fields": fields,
        "raw": text.strip(),
        "json_output": json_output,
        "hash": hash_output
    }
