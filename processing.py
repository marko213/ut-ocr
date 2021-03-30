
# processing.py

import cv2 as cv
import numpy as np

# https://docs.opencv.org/master/d7/d4d/tutorial_py_thresholding.html
# Binariseerib värvipildi
# Eeldab, et kogu pildi ulatuses on kas hele taust ja tume tekst või vastupidi
def toBin(mat):
    # Halliskaalale
    gray = toGray(mat)
    # Binariseerimine
    thresh = cv.adaptiveThreshold(gray, 255, cv.ADAPTIVE_THRESH_MEAN_C, cv.THRESH_BINARY, 15, 5)
    # Eelda, et teksti on vähem kui tausta
    # Tekst peaks olema OpenCV tarbeks valge, taust must
    if np.sum(thresh == 255) > mat.shape[0] * mat.shape[1] * 0.5:
        thresh = cv.bitwise_not(thresh)
    
    return thresh

# Teisendab värvipildi halliskaalale
def toGray(mat):
    return cv.cvtColor(mat, cv.COLOR_BGR2GRAY)

# https://docs.opencv.org/3.4/d5/d69/tutorial_py_non_local_means.html
# Üritab vähendada müra (JPEG) pildil
def denoise(mat):
    return cv.fastNlMeansDenoisingColored(mat, None, 10, 10, 7, 21)

# Skaleerib pildi mõlemat mõõdet mingi tegur f korda
def scale(mat, f):
    return cv.resize(mat, None, fx = f, fy = f)
