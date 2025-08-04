from paddleocr import PaddleOCR
import cv2
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_text_with_paddle(image_path):
    try:
        # Initialize PaddleOCR (with recommended settings)
        ocr = PaddleOCR(
            use_angle_cls=True,
            lang='en',
            show_log=False,
            use_gpu=False,  # Set to True if you have GPU
            det_db_box_thresh=0.6,
            rec_algorithm='SVTR_LCNet'
        )
        
        # Read image using OpenCV
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not read image at {image_path}")
            
        # Perform OCR
        result = ocr.ocr(img)
        
        # Process results (updated for current PaddleOCR version)
        extracted_text = []
        if result is not None:
            for line in result:
                if line:  # Check if line exists
                    for word_info in line:
                        try:
                            # Current PaddleOCR structure
                            text = word_info[1][0]
                            confidence = float(word_info[1][1])
                            if confidence > 0.6:
                                extracted_text.append(text)
                        except (IndexError, TypeError) as e:
                            logger.warning(f"Skipping word due to parsing error: {e}")
                            continue
        
        return ' '.join(extracted_text) if extracted_text else "No text detected"
    
    except Exception as e:
        logger.error(f"OCR processing failed: {str(e)}")
        return None

# Example usage
if __name__ == "__main__":
    result = extract_text_with_paddle("c2.jpeg")
    print("Extracted Text:", result)