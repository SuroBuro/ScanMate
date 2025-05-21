import cv2
import easyocr
import numpy as np
import os


def contour_remover(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    filter_contours = []

    for cont in contours:
        area = cv2.contourArea(cont)
        if 500 < area < 800:
            approx = cv2.approxPolyDP(cont, 0.02 * cv2.arcLength(cont,True), True)
            if len(approx) > 5:
                filter_contours.append(cont)

    cv2.drawContours(image, filter_contours, -1, (255,255,255), thickness= cv2.FILLED)

    return image

def ocr_remover(image):
    reader = easyocr.Reader(['ja'], gpu=False)
    results = reader.readtext(image)

    for (bbox, text, prob) in results:
        pts = np.array(bbox).astype(int)
        cv2.fillPoly(image, [pts], color=(255,255,255))

    return image

def process_image(path, out_path):
    
    image = cv2.imread(path)

    print("Applying OCR based...")
    image = ocr_remover(image)
    
    print("Applying Contour based... ")
    image = contour_remover(image)

    cv2.imwrite(out_path, image)
    print("Finished whitening")


if __name__ =="__main__":
    image_path = ["1.jpg","2.jpg","3.jpg", "4.jpg","5.jpg"]
    for i in range(len(image_path)):
        output_path = f"page_cleaned_{i+1}.jpg"
        process_image(image_path[i], output_path)