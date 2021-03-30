
# recognition.py

import shlex
import pytesseract
import cv2 as cv
import numpy as np
import processing
from bisect import bisect_left, bisect_right
from PIL import Image, ImageDraw, ImageFont
from multiprocessing import Pool
from itertools import starmap
from util import *

# Fondid
fontNames = [
    "LiberationSans-Regular.ttf",
    "LiberationSans-Bold.ttf",
    "LiberationSerif-Regular.ttf",
    "LiberationMono-Regular.ttf"
]

# Minimaalne ja maksimaalne katsetatava märgi laiuse
# suhe sisendiks antud märgi laiusega
minWidthMul = 0.8
maxWidthMul = 1.2

# kasutatavad fondisuurused
fontSizes = range(10, 59, 2)

#######################################

# suurim kõrguse ja laiuse suhe üle fontide
# arvutatakse järgnevas tsüklis
hwRatio = 1

fonts = []
for fn in fontNames:
    cf = []
    for fs in fontSizes:
        cf.append(ImageFont.truetype(fn, size=fs))
        w, h = boxSize(getCharBox('|', cf[-1]))
        hwRatio = max(hwRatio, h / w)
        
    fonts.append(cf)


def border(img, w, h, val):
    return cv.copyMakeBorder(img, h, h, w, w, cv.BORDER_CONSTANT, value=val)

def cropToBox(img, box):
    return img[box[1]:box[3], box[0]:box[2]]

# https://stackoverflow.com/a/31643997
def tessChar(img, box, whitelist):
    img = border(cropToBox(img, box), 3, 3, (255, 255, 255))
    ch = pytesseract.image_to_string(
        img,
        config="-l est --psm 10 -c tessedit_char_whitelist=" + shlex.quote(whitelist)
    ).strip()[:1]
    return ch

patternCharCache = {}

# Genereeri ühe märgi võrldlusmaatriksid
def genCharImages(ch):
    if ch in patternCharCache:
        return
    
    mats = []
    for fl in fonts:
        currm = []
        for font in fl:
            chBox = getCharBox(ch, font)
            chSize = (chBox[2] - chBox[0], chBox[3] - chBox[1])
            size = chSize[0], font.getsize("Ayj")[1] + 4
            
            chImg = Image.new("L", size, 255)
            draw = ImageDraw.Draw(chImg)
            chOffset = (0, chBox[1] + 2)
            draw.text((0, 2), ch, fill=0, font=font)
            chImg = np.array(chImg)
            currm.append(chImg)
        mats.append(currm)
    patternCharCache[ch] = mats

# Ühe märgi võrdlusmaatriksid
def charImages(ch, w):
    for cl in patternCharCache[ch]:
        wl = ListMap(cl, lambda img: img.shape[1])
        lo = bisect_left(wl, int(round(w * minWidthMul)))
        hi = bisect_right(wl, int(round(w * maxWidthMul)))
        for i in range(lo, hi):
            yield cl[i]

# Ühe märgi kohta "kindlus", et tegemist on õige märgiga
def singleChar(img, ch, w):
    best = -1
    ih, iw = img.shape
    for template in charImages(ch, w):
        th, tw = template.shape
        if th > ih or tw > iw:
            break
        match = cv.matchTemplate(img, template, cv.TM_CCOEFF_NORMED)
        curr = np.amax(match)
        best = max(best, curr)
    return best

# Maatrikskõrvutamine
def patternChar(img, box, whitelist):
    # Binariseeri pilt ja lisa ääred maatriksite tarbeks
    w, h = boxSize(box)
    nw = int(round(w * (maxWidthMul - 1) / 2)) + 3
    nh = int(round((w * maxWidthMul * hwRatio - h) / 2)) + 3
    img = 255 - border(cropToBox(processing.toBin(img), box), nw, nh, 0)

    # veendu, et kõik vajalikud märgid on olemas
    for ch in whitelist:
        genCharImages(ch)

    # maksimaalse "kindlusega" märgi leidmine
    with Pool(4) as p:
        best = max(zip(p.starmap(singleChar, ((img, ch, w) for ch in whitelist)), whitelist))
    return best[1]


contourCharCache = {}

# Leia pildilt kontuurid
# väljundiks positiivsete ja negatiivsete kontuuride invariandid
def contoursPosNeg(img):
    # Jaga positiivseteks ja negatiivseteks kontuurideks
    # https://docs.opencv.org/3.4/d9/d8b/tutorial_py_contours_hierarchy.html
    x = cv.findContours(img, cv.RETR_CCOMP, cv.CHAIN_APPROX_SIMPLE)
    if x[1] is None:
        return [], []
    
    contours, (hierarchy,) = x

    pos, neg = [], []
    for c, h in zip(contours, hierarchy):
        if h[3] == -1:
            pos.append(c)
        else:
            neg.append(c)
    
    return pos, neg    


def genCharContours(ch):
    if ch in contourCharCache:
        return

    # genereeri maatriksid sellest märgist
    genCharImages(ch)

    cl = []

    # iga eri fondi suurim pilt
    for il in patternCharCache[ch]:
        img = border(255 - il[-1], 2, 2, 0)
        contours = contoursPosNeg(img)
        cl.append(contours)
    
    contourCharCache[ch] = cl
        

# Ühe märgi kontuurid
def charContours(ch):
    return contourCharCache[ch]

# kahe kontuuri erinevus
def contourDiff(a, b):
    return cv.matchShapes(a, b, cv.CONTOURS_MATCH_I1, 0.0)

# Leia kontuuride erinevus tähemärgist
def matchCharContours(contours, ch):
    # https://docs.opencv.org/master/d5/d45/tutorial_py_contours_more_functions.html
    pos, neg = contours

    best = inf
    for tpos, tneg in charContours(ch):
        dp = 0
        for tc in tpos:
            dp += min(contourDiff(tc, c) for c in pos)
        dp /= len(tpos)

        if (len(tneg) == 0) == (len(neg) == 0):
            dn = 0
            for tc in tneg:
                dn += min(contourDiff(tc, c) for c in neg)
            dn /= max(len(tneg), 1)
        if len(tneg) != len(neg):
            dn = inf
        d = dp + dn
        best = min(best, d)
    return best


# Kontuuridepõhine
def contourChar(img, box, whitelist):
    orig = img
    img = border(cropToBox(processing.toBin(img), box), 3, 3, 0)
    for ch in whitelist:
        genCharContours(ch)

    contours = contoursPosNeg(img)
    if len(contours[0]) == 0:
        return ' '
    
    best = min((matchCharContours(contours, ch), ch) for ch in whitelist)
    return best[1]
