
# stats_segment.py

import time
from pathlib import Path
import cv2 as cv
import json
import os
from util import *
import traceback
import processing
import segment
import os

# Piltide kaust
imageBase = Path("gen", "out")

# Väljundkaust (põhi)
outBase = Path("segment")

# Märgijärjendite arv
sequenceCount = 3

# Piltide arv iga märgijärjendi kohta
imageCount = 100


os.makedirs(outBase, exist_ok=True)

def runSingle(f, currBase, si, i, write=True):
    currBase = outBase / currBase
    imagePath = imageBase / f"img{si}_{i:03}.jpg"
    metaPath = imageBase / f"meta{si}_{i:03}.json"
    with open(metaPath) as metaFile:
        whitelist = json.load(metaFile)['whitelist']
    img = cv.imread(str(imagePath))

    start = time.time()
    data = f(img, whitelist)
    end = time.time()
    t = end - start
    print(t, flush=True)

    if write:
        os.makedirs(currBase, exist_ok=True)
        with open(currBase / f"out{si}_{i:03}.json", "w") as outFile:
            json.dump({'time': t, 'data': data}, outFile)

# Jooksuta antud funktsiooni iga pildi puhul ja mõõda aeg
def run(f, outBase):
    for si in range(sequenceCount):
        for i in range(imageCount):
            try:
                runSingle(f, outBase, si, i)
            except Exception:
                print(f"Viga {outBase} {si} {i}")
                print(traceback.format_exc(), flush=True)
        
    print(f"Valmis {outBase}")


def tess1(img, whitelist):
    return segment.tessBoxes(img, whitelist)

def tess2(img, whitelist):
    img = processing.denoise(img)
    return segment.tessBoxes(img, whitelist)

def tess3(img, whitelist):
    img = processing.scale(processing.denoise(img), 2)
    data = segment.tessBoxes(img, whitelist)
    return unscale(data, 2)

def contour1(img, whitelist):
    bin = processing.toBin(img)
    return segment.contourBoxes(bin)

def contour2(img, whitelist):
    img = processing.denoise(img)
    bin = processing.toBin(img)
    return segment.contourBoxes(bin)

def contour3(img, whitelist):
    img = processing.scale(processing.denoise(img), 2)
    bin = processing.toBin(img)
    data = segment.contourBoxes(bin)
    return unscale(data, 2)

def pattern1(img, whitelist):
    return segment.patternBoxes(img, whitelist)

def pattern2(img, whitelist):
    img = processing.denoise(img)
    return segment.patternBoxes(img, whitelist)

def pattern3(img, whitelist):
    img = processing.denoise(img)
    return segment.patternBoxes(img, whitelist, scale=True)

run(tess1, Path("tess1"))
run(tess2, Path("tess2"))
run(tess3, Path("tess3"))
run(contour1, Path("contour1"))
run(contour2, Path("contour2"))
run(contour3, Path("contour3"))
run(pattern1, Path("pattern1"))
run(pattern2, Path("pattern2"))
run(pattern3, Path("pattern3"))

