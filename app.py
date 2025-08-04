from paddleocr import PaddleOCR
import numpy as np
from PIL import Image
import cv2

# Load
ocr = PaddleOCR(use_angle_cls=True, lang='en',
                det_db_thresh=0.1, det_db_box_thresh=0.1)

img = np.array(Image.open("c2.jpeg").convert("RGB"))
# Try inverted version if necessary
gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
_, inv = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
inv = cv2.cvtColor(inv, cv2.COLOR_GRAY2RGB)
for test_img in [img, inv]:
    print("Testing image variant")
    res = ocr.ocr(test_img)
    for line in res[0]: print(line[1][0])
    print()
