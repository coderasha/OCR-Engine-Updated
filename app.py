import streamlit as st
import pytesseract
import numpy as np
import cv2
import json
import re
from PIL import Image

# Optional: specify path to tesseract executable if not in PATH
# pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'  # Linux
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Windows

# Preprocess image for better OCR
def preprocess_image(pil_img):
    img = np.array(pil_img)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    img = cv2.resize(img, (img.shape[1]*2, img.shape[0]*2))
    img = cv2.bilateralFilter(img, 9, 75, 75)
    _, img = cv2.threshold(img, 150, 255, cv2.THRESH_BINARY)
    return img

# Run Tesseract OCR
def extract_text(image):
    return pytesseract.image_to_string(image)

# Fuzzy pattern matching
def fuzzy_search(patterns, text):
    for pat in patterns:
        match = re.search(pat, text, re.IGNORECASE)
        if match:
            return match
    return None

# Extract structured fields
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
st.set_page_config(page_title="Tesseract OCR Extractor", layout="centered")
st.title("📜 OCR Certificate Extractor (with Tesseract)")

uploaded_file = st.file_uploader("📤 Upload a certificate image (JPG, PNG)", type=["jpg", "jpeg", "png"])

if uploaded_file:
    pil_image = Image.open(uploaded_file)
    st.image(pil_image, caption="Uploaded Image", use_column_width=True)

    with st.spinner("🔍 Running OCR..."):
        processed = preprocess_image(pil_image)
        text = extract_text(processed)
        structured = extract_fields(text)

    st.subheader("📄 Raw OCR Text")
    st.text(text)

    st.subheader("📋 Extracted Fields")
    st.json(structured)

    st.subheader("📥 Download")
    col1, col2 = st.columns(2)
    col1.download_button("⬇️ Download JSON", json.dumps(structured, indent=4), "output.json", "application/json")
    col2.download_button("⬇️ Download Raw Text", text, "raw_text.txt", "text/plain")
