
# summarize_recognition.py

import json
from pathlib import Path
from util import *

# tuvastatavate märkide loetelu
samplePath = Path("gen", "singlechar.json")

# tulemuste kaust
basePath = Path("recognition")

with open(samplePath) as f:
    samples = json.load(f)

def makeSummary(path):
    with open(basePath / path) as f:
        found = json.load(f)
    rows = []    
    for i, (f, s) in enumerate(zip(found, samples), start=1):
        correct = 0
        caseCorrect = 0
        for fc, sc in zip(f['chars'], s):
            sc = sc[1]
            if fc.lower() == sc.lower():
                correct += 1
            if fc == sc:
                caseCorrect += 1
        correct /= len(s)
        caseCorrect /= len(s)
        t = f['time'] / len(s)
        rows.append(f"& {t:.2} & {1-correct:.3f} & {1-caseCorrect:.3f} \\\\".replace('.', ','))
    return rows

def makeSection(ls, baseName):
    print()
    for a1, a2, a3 in zip(*ls):
        print(f"{baseName} {a1}")
        print(f"{baseName} + müraeemaldus {a2}")
        print(f"{baseName} + müraeemaldus + skaleerimine {a3}")
        print()

l1 = makeSummary("tess1.json")
l2 = makeSummary("tess2.json")
l3 = makeSummary("tess3.json")
makeSection([l1, l2, l3], r"\tesseract")

l1 = makeSummary("contour1.json")
l2 = makeSummary("contour2.json")
l3 = makeSummary("contour3.json")
makeSection([l1, l2, l3], "Kontuuridepõhine")

l1 = makeSummary("pattern1.json")
l2 = makeSummary("pattern2.json")
l3 = makeSummary("pattern3.json")
makeSection([l1, l2, l3], "Maatrikskõrvutamine")
