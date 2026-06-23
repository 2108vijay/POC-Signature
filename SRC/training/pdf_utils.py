from pdf2image import convert_from_bytes
import numpy as np
import cv2

def pdf_to_image(pdf_bytes):

    pages = convert_from_bytes(pdf_bytes)  
    first_page = pages[0]

    image = cv2.cvtColor(
        np.array(first_page),
        cv2.COLOR_RGB2BGR
    )

    return image