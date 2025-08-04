import streamlit as st
import requests

st.set_page_config(page_title="AI Certificate OCR", layout="centered")
st.title("📄 AI Certificate OCR with Multi-Font Engine")

# Engine toggle
engine = st.selectbox("Choose OCR Engine", ["easyocr", "tesseract"])

col1, col2 = st.columns(2)

with col1:
    image_file = st.file_uploader("Upload Image (PNG/JPG)", type=["png", "jpg", "jpeg"], key="image_upload")

with col2:
    pdf_file = st.file_uploader("Upload PDF", type=["pdf"], key="pdf_upload")

uploaded_file = image_file or pdf_file

if uploaded_file:
    if st.button("Extract Fields"):
        with st.spinner("🔍 Extracting text... please wait..."):
            files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
            data = {"engine": engine}

            try:
                response = requests.post("http://localhost:8000/extract_fields", files=files, data=data)
                response.raise_for_status()
                result = response.json()
                fields = result.get("fields", {})

                st.success("✅ Extraction Complete!")

                st.subheader("Extracted Fields")
                st.text_input("Issuance Date", value=fields.get("issuance_date", ""))
                st.text_input("Certificate Holder", value=fields.get("certificate_holder", ""))
                st.text_input("Program Name", value=fields.get("program_name", ""))
                st.text_input("Certificate ID", value=fields.get("certificate_id", ""))
                st.text_input("Issuer", value=fields.get("issuer", ""))

                st.subheader("📝 Raw OCR Text")
                st.text_area("Raw Text", result.get("raw", ""), height=200)

                st.subheader("📦 Structured JSON Output")
                st.code(result.get("json_output", ""), language="json")

                st.subheader("🔐 SHA256 Hash of Output")
                st.code(result.get("hash", ""), language="text")

            except Exception as e:
                st.error(f"❌ Failed to extract fields: {str(e)}")
