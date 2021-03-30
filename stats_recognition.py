
# stats_recognition.py

import PIL
import json
from pathlib import Path
import traceback
import time
import cv2 as cv
import recognition
import processing
from util import *
import os

# pildifailide asukoht
imageBase = Path("gen", "out")

# tuvastatavate märkide loetelu
samplePath = Path("gen", "singlechar.json")

# väljundkaust
outBase = Path("recognition")

# Konteksti tarbeks lisaruum märgi ümbert
padX = 10
padY = 10

os.makedirs(outBase, exist_ok=True)

with open(samplePath) as f:
    rawSamples = json.load(f)
def cropToBox(img, box):
    return img[box[1]:box[3], box[0]:box[2]]
samples = []
for si, rs in enumerate(rawSamples):
    ssamples = []
    for ci, ch, b in rs:
        imagePath = imageBase / f"img{si}_{ci:03}.jpg"
        metaPath = imageBase / f"meta{si}_{ci:03}.json"
        with open(metaPath) as metaFile:
            whitelist = json.load(metaFile)['whitelist']
        ob = [int(round(x)) for x in b]
        img = cv.imread(str(imagePath))
        h, w, _ = img.shape
        b = max(0, ob[0] - padX), max(0, ob[1] - padY), min(w, ob[2] + padX), min(h, ob[3] + padY)
        img = img[b[1]:b[3], b[0]:b[2]]
        box = [ob[0] - b[0], ob[1] - b[1], ob[0] - b[0] + ob[2] - ob[0], ob[1] - b[1] + ob[3] - ob[1]]
        ssamples.append({"img": img, "box": box, "whitelist": whitelist})
    samples.append(ssamples)

def runSingle(f, si, ci):
    s = samples[si][ci]
    img, box, whitelist = s["img"], s["box"], s["whitelist"]
    ch = f(img, box, whitelist)
    return ch

def run(f, outFile):
    print(outFile, flush=True)
    results = []
    for si in range(len(samples)):
        sresults = []
        start = time.time()
        for ci in range(len(samples[si])):
            res = None
            try:
                res = runSingle(f, si, ci)
            except:
                print(f"Viga {outFile} {si} {ci}")
                print(traceback.format_exc())
            sresults.append(res)
        end = time.time()
        t = end - start
        print(t, flush=True)
        results.append({"time": t, "chars": sresults})
    with open(outBase / outFile, "w") as f:
        json.dump(results, f)
    print(flush=True)

def tess1(img, box, whitelist):
    ch = recognition.tessChar(img, box, whitelist)
    return ch

def tess2(img, box, whitelist):
    img = processing.denoise(img)
    ch = recognition.tessChar(img, box, whitelist)
    return ch

def tess3(img, box, whitelist):
    img = processing.scale(processing.denoise(img), 2)
    box = boxScale(box, 2)
    ch = recognition.tessChar(img, box, whitelist)
    return ch

def contour1(img, box, whitelist):
    ch = recognition.contourChar(img, box, whitelist)
    return ch

def contour2(img, box, whitelist):
    img = processing.denoise(img)
    ch = recognition.contourChar(img, box, whitelist)
    return ch

def contour3(img, box, whitelist):
    img = processing.scale(processing.denoise(img), 2)
    box = boxScale(box, 2)
    ch = recognition.contourChar(img, box, whitelist)
    return ch

def pattern1(img, box, whitelist):
    ch = recognition.patternChar(img, box, whitelist)
    return ch

def pattern2(img, box, whitelist):
    img = processing.denoise(img)
    ch = recognition.patternChar(img, box, whitelist)
    return ch

def pattern3(img, box, whitelist):
    img = processing.scale(processing.denoise(img), 2)
    box = boxScale(box, 2)
    ch = recognition.patternChar(img, box, whitelist)
    return ch

# genereeri eelnevalt kõik vajaminevad (loodetavasti)
# märkide võrdlusmaatriksid ja invariandid
for ch in allChars:
    recognition.genCharImages(ch)
    recognition.genCharContours(ch)

run(tess1, "tess1.json")
run(tess2, "tess2.json")
run(tess3, "tess3.json")
run(contour1, "contour1.json")
run(contour2, "contour2.json")
run(contour3, "contour3.json")
run(pattern1, "pattern1.json")
run(pattern2, "pattern2.json")
run(pattern3, "pattern3.json")


