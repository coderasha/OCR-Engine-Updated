import streamlit as st
import easyocr
import numpy as np
from PIL import Image
import cv2
import re
import json

# Load EasyOCR
reader = easyocr.Reader(['en'], gpu=False)

# === Image Preprocessing ===
def preprocess_image(pil_img):
    img = np.array(pil_img)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    img = cv2.resize(img, (img.shape[1] * 2, img.shape[0] * 2))  # upscale
    img = cv2.bilateralFilter(img, 9, 75, 75)  # denoise
    return Image.fromarray(img)

# === OCR Text Extraction ===
def extract_text(image):
    result = reader.readtext(np.array(image), detail=0, paragraph=True)
    return "\n".join(result)

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
st.set_page_config(page_title="🧾 Certificate Extractor", layout="centered")
st.title("📜 OCR Certificate Data Extractor")

uploaded_file = st.file_uploader("📤 Upload a certificate image (JPG, PNG)", type=["jpg", "jpeg", "png"])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Image", use_column_width=True)

    with st.spinner("🔍 Extracting text..."):
        preprocessed_image = preprocess_image(image)
        text = extract_text(preprocessed_image)
        structured_data = extract_fields(text)

    st.subheader("📄 Raw OCR Text")
    st.text(text)

    st.subheader("📋 Extracted Fields")
    st.json(structured_data)

    st.subheader("📥 Download Outputs")
    col1, col2 = st.columns(2)
    col1.download_button("⬇️ Download JSON", data=json.dumps(structured_data, indent=4), file_name="output.json", mime="application/json")
    col2.download_button("⬇️ Download Raw Text", data=text, file_name="raw_text.txt", mime="text/plain")
