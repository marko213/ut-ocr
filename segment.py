
# segment.py

import cv2 as cv
import numpy as np
from PIL import Image, ImageFont, ImageDraw
import processing
import pytesseract
import shlex
from bisect import bisect_left, bisect_right
from multiprocessing import Pool
from util import *

# Maksimaalne rekursiivsete kontuuride arv
maxRec = 1

# Maksimaalne samal tasemel olevate alamkontuuride arv
maxSub = 3

# "tavamõõtme" määramiseks asukoht mõõtmete hulgas
# skaala 0..1, 0 on kõige väiksem leitud suurus, 1 kõige suurem, 0.5 mediaan
dimIndexMul = 0.8

# Kordaja maksimaalse suuruserinevuse jaoks leitud "tavamõõtmest"
maxSizeMul = 10

# Minimaalne mõõde ühel kontuuril - kui mõõde on alla selle, siis seda ei arvestata
minDimension = 3

# Fondid
fontNames = [
    "LiberationSans-Regular.ttf",
    "LiberationSans-Bold.ttf",
    "LiberationMono-Regular.ttf"
]

# Fondisuurused, millest pildid genereerida
fontSampleSizes = range(14, 49, 2)

# Fondisuurused skaleerimata pildi puhul
smallFontSizes = range(14, 31, 2)

# Fondisuurused skaleeritud pildi puhul
largeFontSizes = range(20, 49, 2)

# Kui palju pilti suurendada (kui see on sisse lülitatud)
# (vaid pattern match puhul)
templateScale = 1.5

# Piir, kui palju peab märk pildiga "sobima"
templateThreshold = 0.75

# Piir, kui palju vähemalt üks kast teisega kattuma peab
# (pindala osa), et need kastid liita
overlapMergeFactor = 0.7

#########################################

fonts = []
for fn in fontNames:
    for fs in fontSampleSizes:
        fonts.append((ImageFont.truetype(fn, size=fs), fn, fs))


# Kontuurist ekstreemumkoordinaatide võtmine
def contourBounds(points):
    xmi = xma = points[0][0]
    ymi = yma = points[0][1]
    for (x, y) in points:
        xmi = min(xmi, x)
        xma = max(xma, x)
        ymi = min(ymi, y)
        yma = max(yma, y)
    
    return xmi, ymi, xma, yma

# Üks kontuur koos sellele vastavate lisaparameetritega
class Contour:
    def __init__(self, raw):
        self.points = raw[:, 0, :]
        self.bounds = contourBounds(self.points)
        self.shape = (self.bounds[2] - self.bounds[0],
                      self.bounds[3] - self.bounds[1])
        self.rawPoints = raw

# https://docs.opencv.org/3.4/d4/d73/tutorial_py_contours_begin.html
# Leia tähtede (osade) kontuurid (piirjooned)
# Sisendiks binariseeritud pilt
# Kontuuridest filtreeritakse välja tähtedest suuremad ja
# liialt väikesed kontuurid
def contourBoxes(thresh):
    # Kontuurid ja nende hierarhia
    contours, (hierarchy,) = cv.findContours(thresh, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
    
    contours = [Contour(c) for c in contours]
    
    # Kas sellel indeksil olev kontuur võtta
    take = [True for _ in contours]

    # Eemaldada kontuurid, millel on rohkem kui 1 rekursiivne alamkontuur
    # ning kontuurid, millel on rohkem kui 3 sisemist kontuuri
    # Sügavuse põhjal: võtta järgmise samal hierarhilisel tasemel oleva
    # kontuuri indeks ning selle kontuuri "vanema" indeks
    for i, (_, ni, _, pi) in enumerate(hierarchy):
        if pi != -1:
            ci = pi
            for _ in range(maxRec):
                ci = hierarchy[ci][3]
                if ci == -1:
                    break
            else:
                # Liialt palju rekursiivseid tasemeid
                take[ci] = False
            if ni != -1:
                for _ in range(maxSub):
                    ni = hierarchy[ni][1]
                    if ni == -1:
                        break
                else:
                    # Liialt palju samal tasemel olevaid alamkontuure
                    take[pi] = False
    
    # Eemalda kontuurid, mille suurus ei klapi teistega või on liialt väiksed
    # eeldades, et peamiselt on kontuurid tähed
    
    # Leida maksimaalsed mõõtmed
    widths = [c.shape[0] for c, t in zip(contours, take) if t]
    heights = [c.shape[1] for c, t in zip(contours, take) if t]
    widths.sort()
    heights.sort()
    mw = widths[round((len(widths) - 1) * dimIndexMul)] * maxSizeMul
    mh = heights[round((len(heights) - 1) * dimIndexMul)] * maxSizeMul
    
    for i, c in enumerate(contours):
        if c.shape[0] > mw or c.shape[1] > mh or min(c.shape) < minDimension:
            take[i] = False

    # Eemalda kontuurid, mille piirdekastid on täielikult teise
    # kontuuri piirdekasti sees
    ci = [i for i, t in enumerate(take) if t]
    for a in ci:
        abox = contours[a].bounds
        for b in ci:
            if b == a:
                continue
            bbox = contours[b].bounds
            if inside(bbox, abox):
                take[b] = False
                break
    
    return [tuple(map(int, c.bounds)) for c, t in zip(contours, take) if t]


charCache = {}


# Liida kattuvad kastid üheks
def mergeOverlap(boxes):
    # sorteeri kastid ülemise piiri põhjal
    boxes.sort(key=lambda b: b[1])

    # Leia maksimaalsed mõõtmed ja maksimaalne horisontaalne koordinaat
    mxw = 0
    mxh = 0
    mxx = 0
    for b in boxes:
        w, h = boxSize(b)
        mxw = max(mxw, w)
        mxh = max(mxh, h)
        mxx = max(mxx, b[2])

    # Jaota kastid gruppidesse vertikaalsete lõikude järgi
    # Iga kast on igas horisontaalses lõigus, millega see lõikub
    vw = int(mxw)
    vgroups = [[] for _ in range(ceilDiv(int(mxx) + 1, vw) + 1)]
    for i, b in enumerate(boxes):
        for gi in range(int(b[0] / vw), int(b[2] / vw) + 1):
            vgroups[gi].append(i)
    
    # iga grupi kastide ülemiste piiride kõrgused
    vheights = [[boxes[i][1] for i in g] for g in vgroups]

    # grupid on sorteeritud kastide ülemise piiri järgi

    keep = [True for _ in range(len(boxes))]

    for i in range(len(boxes)):
        if not keep[i]:
            continue
        a = boxes[i]
        aw, ah = boxSize(a)
        # kastid vaid lubatud lõikudest
        for gi in range(max(int((a[0] - mxw) / vw), 0), min(int((a[2] + mxw) / vw) + 1, len(vgroups))):
            # vaid kastid, mis on vertikaalselt õiges kohas
            # ehk kattuvad vertikaalsihis antud kastiga
            si = bisect_left(vheights[gi], a[1] - mxh)
            ei = bisect_right(vheights[gi], a[3])
            for jg in range(si, ei):
                j = vgroups[gi][jg]
                if i == j or not keep[j]:
                    continue
                b = boxes[j]
                intersect = intersection(a, b)
                iw, ih = boxSize(intersect)
                if iw <= 0 or ih <= 0:
                    continue
                
                p = (iw * ih) / (aw * ah)
                if p >= overlapMergeFactor:
                    boxes[j] = union(a, b)
                    mxh = max(mxh, boxSize(boxes[j])[1])
                    keep[i] = False
                    break
            else:
                continue
            break
    return [b for b, k in zip(boxes, keep) if k]

def singlePattern(img, template, size, offset):
    match = cv.matchTemplate(img, template, cv.TM_CCOEFF_NORMED)
    loc = np.where(match >= templateThreshold)
    boxes = []
    for pr in zip(*loc[::-1]):
        boxes.append(tuple(map(int,
                        (pr[0] + offset[0],
                        pr[1] + offset[1],
                        pr[0] + offset[0] + size[0],
                        pr[1] + offset[1] + size[1]))))
    return boxes

# Teine algoritm
# Pattern match üle kõigi märkide / fontide / tähesuuruste
def patternBoxes(img, whitelist, scale=False):
    # Genereeri vajalike märkide võrdlusmaatriksid
    for c in whitelist:
        if c not in charCache:
            chArr = []
            for font in fonts:
                chBox = getCharBox(c, font[0])
                chSize = (chBox[2] - chBox[0], chBox[3] - chBox[1])
                size = chSize[0], font[0].getsize("Ayj")[1] + 4
                
                chImg = Image.new("L", size, 255)
                draw = ImageDraw.Draw(chImg)
                chOffset = (0, chBox[1] + 2)
                draw.text((0, 2), c, fill=0, font=font[0])
                chImg = np.array(chImg)
                chArr.append((chOffset, chSize, chImg, font[2]))
            charCache[c] = chArr
    
    if scale:
        img = processing.scale(img, templateScale)
    
    img = processing.toBin(img)
    img = 255 - img
    boxes = []
    
    if scale:
        r = largeFontSizes
    else:
        r = smallFontSizes
    
    calls = []
    # https://opencv-python-tutroals.readthedocs.io/en/latest/py_tutorials/py_imgproc/py_template_matching/py_template_matching.html            
    for c in whitelist:
        for offset, size, template, fs in charCache[c]:
            if fs not in r:
                continue
            calls.append((img, template, size, offset))
    
    with Pool(4) as p:
        boxes = p.starmap(singlePattern, calls)
    boxes = [b for sb in boxes for b in sb]        
            
    if scale:
        boxes = unscale(boxes, templateScale)
    if 0 < len(boxes) < 50000:
        boxes = mergeOverlap(boxes)
    return boxes

# https://stackoverflow.com/questions/57033120/bounding-boxes-around-characters-for-tesseract-4-0-0-beta-1
def tessBoxes(img, whitelist):
    d = pytesseract.image_to_boxes(img,
                                   output_type=pytesseract.Output.DICT,
                                   config="-l est -c tessedit_char_whitelist=" + shlex.quote(whitelist))
    # vertikaalis algab pildi allosast...
    h = img.shape[0]
    data = list((l, h - t, r, h - b) for l, t, r, b in zip(d['left'], d['top'], d['right'], d['bottom']))
    return data
