import streamlit as st
import easyocr
import numpy as np
from PIL import Image
import io
import json
import re

# Initialize EasyOCR reader
reader = easyocr.Reader(['en'])

def extract_text(image):
    result = reader.readtext(np.array(image), detail=0, paragraph=True)
    return "\n".join(result)

def extract_fields(text):
    data = {}
    data["issuance_date"] = re.search(r"Issuance Date[:\- ]+([\d\-]+)", text)
    data["ccc_reference_number"] = re.search(r"CCC Reference Number[:\- ]+(\S+)", text)
    data["company_name"] = re.search(r"confirm that\s+([^\n]+)", text)
    data["commercial_registration_number"] = re.search(r"CRN[-:]?(\d+)", text)
    data["address"] = re.search(r"\d+ .+?Blvd", text)
    data["assessment_standard"] = re.search(r"compliance with (.+?)\.", text)
    data["assessment_period"] = re.search(r"between\s+([\d\-]+)\s+and\s+([\d\-]+)", text)
    data["classification_type"] = re.search(r"classification of[:\- ]+([A-Z]), Type[:\- ]+(\w+)", text)

    structured = {
        "issuance_date": data["issuance_date"].group(1) if data["issuance_date"] else None,
        "ccc_reference_number": data["ccc_reference_number"].group(1) if data["ccc_reference_number"] else None,
        "company_name": data["company_name"].group(1) if data["company_name"] else None,
        "commercial_registration_number": data["commercial_registration_number"].group(1) if data["commercial_registration_number"] else None,
        "address": data["address"].group(0) if data["address"] else None,
        "assessment_standard": data["assessment_standard"].group(1) if data["assessment_standard"] else None,
        "assessment_period": {
            "start_date": data["assessment_period"].group(1) if data["assessment_period"] else None,
            "end_date": data["assessment_period"].group(2) if data["assessment_period"] else None
        },
        "classification": data["classification_type"].group(1) if data["classification_type"] else None,
        "type": data["classification_type"].group(2) if data["classification_type"] else None
    }
    return structured

# Streamlit UI
st.title("🛡️ Certificate Extractor (OCR + JSON)")
uploaded_file = st.file_uploader("Upload a certificate image (JPG, PNG)", type=["jpg", "jpeg", "png"])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Image", use_column_width=True)

    with st.spinner("🔍 Extracting text..."):
        text = extract_text(image)
        structured_data = extract_fields(text)

    st.subheader("📄 Raw OCR Text")
    st.text(text)

    st.subheader("📋 Extracted Fields")
    st.json(structured_data)

    st.subheader("📥 Download Outputs")
    col1, col2 = st.columns(2)

    json_output = json.dumps(structured_data, indent=4)
    col1.download_button("Download JSON", data=json_output, file_name="output.json", mime="application/json")
    col2.download_button("Download Raw Text", data=text, file_name="raw_text.txt", mime="text/plain")
