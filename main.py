from fastapi import FastAPI, UploadFile, File
from paddleocr import PaddleOCR
import cv2
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI()

# Initialize PaddleOCR with correct parameters
try:
    ocr = PaddleOCR(
        use_angle_cls=True,
        lang='en',
        use_gpu=False,
        show_log=False
    )
    logger.info("PaddleOCR initialized successfully")
except Exception as e:
    logger.error(f"PaddleOCR initialization failed: {e}")
    raise

@app.post("/ocr")
async def extract_text(file: UploadFile = File(...)):
    temp_path = None
    try:
        # Save uploaded file temporarily
        temp_path = "temp_upload.jpg"
        with open(temp_path, "wb") as buffer:
            buffer.write(await file.read())
        
        # Read image
        img = cv2.imread(temp_path)
        if img is None:
            return {"error": "Could not read image file"}
        
        # Perform OCR
        result = ocr.ocr(img)
        
        # Process results
        extracted_text = []
        if result:
            for line in result:
                if line:
                    for word_info in line:
                        try:
                            text = word_info[1][0]
                            confidence = float(word_info[1][1])
                            if confidence > 0.6:
                                extracted_text.append(text)
                        except (IndexError, TypeError) as e:
                            logger.warning(f"Skipping word due to error: {e}")
                            continue
        
        return {"text": " ".join(extracted_text) if extracted_text else "No text detected"}
    
    except Exception as e:
        logger.error(f"OCR processing failed: {e}")
        return {"error": str(e)}
    
    finally:
        # Clean up temp file
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)