import streamlit as st
from paddleocr import PaddleOCR
import numpy as np
import cv2
import json
import re
from PIL import Image

# Initialize PaddleOCR
ocr = PaddleOCR(use_angle_cls=True, lang='en')  # No use_gpu

# === Image Preprocessing ===
def preprocess_image(pil_img):
    img = np.array(pil_img.convert("RGB"))  # Ensure 3-channel RGB
    img = cv2.resize(img, (img.shape[1]*2, img.shape[0]*2))
    img = cv2.bilateralFilter(img, 9, 75, 75)  # Denoise
    return img  # Keep as 3D array (H x W x 3)

# === OCR Text Extraction ===
def extract_text(image):
    result = ocr.ocr(image)
    lines = []
    for line in result[0]:  # result[0] contains (box, (text, confidence))
        lines.append(line[1][0])
    return "\n".join(lines)

# === Fuzzy Pattern Matching ===
def fuzzy_search(patterns, text):
    for pat in patterns:
        match = re.search(pat, text, re.IGNORECASE)
        if match:
            return match
    return None

# === Extract Fields ===
def extract_fields(text):
    data = {}

    data["issuance_date"] = fuzzy_search([
        r"Issuance\s*Date[:\- ]+([\d]{2}[\-/][\d]{2}[\-/][\d]{4})",
        r"Issuan.*Date.*?([\d\-\/]+)"
    ], text)

    data["ccc_reference_number"] = fuzzy_search([
        r"CCC Reference Number[:\- ]+([A-Z0-9\-]+)",
        r"CCC.*?Number.*?([A-Z0-9\-]+)"
    ], text)

    data["company_name"] = fuzzy_search([
        r"confirm that\s+([^\n]+)"
    ], text)

    data["commercial_registration_number"] = fuzzy_search([
        r"CRN[-: ]?(\d+)",
        r"Commercial Registration No.*?(\d+)"
    ], text)

    data["address"] = fuzzy_search([
        r"\d{1,4} [A-Za-z0-9 ]+Blvd",
        r"\d{1,4}.+Blvd"
    ], text)

    data["assessment_standard"] = fuzzy_search([
        r"compliance with (.+?)\.",
        r"compliance.+?Standard\s*\((.*?)\)"
    ], text)

    data["assessment_period"] = fuzzy_search([
        r"between\s+([\d\-\/]+)\s+and\s+([\d\-\/]+)"
    ], text)

    data["classification_type"] = fuzzy_search([
        r"classification of[:\- ]+([A-Z]), Type[:\- ]+(\w+)",
        r"Type[:\- ]+(\w+)"
    ], text)

    structured = {
        "issuance_date": data["issuance_date"].group(1) if data["issuance_date"] else None,
        "ccc_reference_number": data["ccc_reference_number"].group(1) if data["ccc_reference_number"] else None,
        "company_name": data["company_name"].group(1).strip() if data["company_name"] else None,
        "commercial_registration_number": data["commercial_registration_number"].group(1) if data["commercial_registration_number"] else None,
        "address": data["address"].group(0) if data["address"] else None,
        "assessment_standard": data["assessment_standard"].group(1) if data["assessment_standard"] else None,
        "assessment_period": {
            "start_date": data["assessment_period"].group(1) if data["assessment_period"] else None,
            "end_date": data["assessment_period"].group(2) if data["assessment_period"] else None
        },
        "classification": data["classification_type"].group(1) if data["classification_type"] and data["classification_type"].lastindex > 1 else None,
        "type": data["classification_type"].group(2) if data["classification_type"] and data["classification_type"].lastindex > 1 else (
            data["classification_type"].group(1) if data["classification_type"] else None
        )
    }

    return structured

# === Streamlit UI ===
st.set_page_config(page_title="📜 Certificate Extractor (PaddleOCR)", layout="centered")
st.title("📑 OCR Certificate Extractor (Powered by PaddleOCR)")

uploaded_file = st.file_uploader("📤 Upload certificate image", type=["jpg", "jpeg", "png"])

if uploaded_file:
    pil_image = Image.open(uploaded_file)
    st.image(pil_image, caption="Uploaded Image", use_container_width=True)

    with st.spinner("🔍 Running OCR with PaddleOCR..."):
        preprocessed = preprocess_image(pil_image)
        text = extract_text(preprocessed)
        structured = extract_fields(text)

    st.subheader("📄 Raw OCR Text")
    st.text(text)

    st.subheader("📋 Extracted Fields")
    st.json(structured)

    st.subheader("📥 Download Outputs")
    col1, col2 = st.columns(2)
    col1.download_button("⬇️ Download JSON", data=json.dumps(structured, indent=4), file_name="output.json", mime="application/json")
    col2.download_button("⬇️ Download Raw Text", data=text, file_name="raw_text.txt", mime="text/plain")
