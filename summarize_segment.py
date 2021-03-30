
# summarize_segment.py

from pathlib import Path
import os
import json
from bisect import bisect_left, bisect_right
from util import *

# Algsed andmed
dataPath = Path("gen", "out")

# Väljundandmete põhikaust
statsDir = Path("segment")

# Märgijärjendite arv
sequenceCount = 3

maxRelErr = 0.5**2 * 4

def sqFacDiff(a, b, f):
    return ((a - b) / f)**2

def boxError(orig, run):
    ow, oh = boxSize(orig)
    return sum(sqFacDiff(o, r, f) for o, r, f in zip(orig, run, (ow, oh, ow, oh)))

def boxErrors(orig, run):
    # sorteeri kastid ülemise piiri põhjal
    orig.sort(key=lambda b: b[1])

    # Kõige paremini sobiv kast
    fits = [(-1, inf) for _ in orig]

    # Originaalsega sobivad kastid
    remotes = [set() for _ in run]

    # Leia maksimaalsed mõõtmed ja maksimaalne horisontaalne koordinaat
    mxw = 0
    mxh = 0
    mxx = 0
    for b in orig:
        w, h = boxSize(b)
        mxw = max(mxw, w)
        mxh = max(mxh, h)
        mxx = max(mxx, b[2])

    # Jaota kastid gruppidesse vertikaalsete lõikude järgi
    # Iga kast on igas horisontaalses lõigus, millega see lõikub
    vw = int(mxw)
    vgroups = [[] for _ in range(ceilDiv(int(mxx) + 1, vw) + 1)]
    for i, b in enumerate(orig):
        for gi in range(int(b[0] / vw), int(b[2] / vw) + 1):
            vgroups[gi].append(i)
    
    # iga grupi kastide ülemiste piiride kõrgused
    vheights = [[orig[i][1] for i in g] for g in vgroups]

    # grupid on sorteeritud kastide ülemise piiri järgi

    for i, a in enumerate(run):
        # kastid vaid lubatud lõikudest
        for gi in range(max(int((a[0] - mxw) / vw), 0), min(int((a[2] + mxw) / vw) + 1, len(vgroups))):
            # vaid kastid, mis on vertikaalselt õiges kohas
            # ehk kattuvad vertikaalsihis antud kastiga
            si = bisect_left(vheights[gi], a[1] - mxh)
            ei = bisect_right(vheights[gi], a[3])
            for jg in range(si, ei):
                j = vgroups[gi][jg]
                b = orig[j]
                err = boxError(b, a)
                if err < maxRelErr and err < fits[j][1]:
                    if fits[j][0] != -1:
                        remotes[fits[j][0]].remove(j)
                    fits[j] = (i, err)
                    remotes[i].add(j)

    fp = 0
    for i in range(len(run)):
        if len(remotes[i]) == 0:
            fp += 1
        else:
            best = (-1, inf)
            for r in remotes[i]:
                if fits[r][1] < best[1]:
                    best = r, fits[r][1]

            for r in remotes[i]:
                if r != best[0]:
                    fits[r] = (-1, inf)
    fn = 0
    err = 0
    foundC = 0
    for _, e in fits:
        if e != inf:
            err += e
            foundC += 1
        else:
            fn += 1
    
    if foundC == 0:
        err = maxRelErr
    else:
        err /= foundC
    
    return err, fp, fn
    


# Ühe kausta kohta kokkuvõte
def makeSummary(path):
    name = str(path)
    path = statsDir / path
    print()
    print(name)
    stl = []
    for s in range(sequenceCount):
        count = 0
        timeAvg = 0
        errAvg = 0
        fpAvg = 0
        fnAvg = 0
        for f in path.glob(f"out{s}_*.json"):
            count += 1
            fn = f.parts[-1]
            with open(f) as runF:
                runData = json.load(runF)
            timeAvg += runData['time']

            with open(dataPath / ("meta" + fn[3:])) as origF:
                origData = json.load(origF)
            
            scaleFactor = origData['scaleFactor']
            origBoxes = []
            for p in origData['paragraphs']:
                for r in p['rows']:
                    for _, b in r:
                        origBoxes.append(b)
            origBoxes = scale(origBoxes, scaleFactor)
            err, fp, fn = boxErrors(origBoxes, runData['data'])
            if fn / len(origBoxes) > 0.5:
                print(f)
            errAvg += err
            fpAvg += fp / len(origBoxes)
            fnAvg += fn / len(origBoxes)
            
        
        timeAvg = timeAvg / count
        errAvg /= count
        fpAvg /= count
        fnAvg /= count
        print(f" {s}")
        print(f"  Keskmine kulunud aeg: {timeAvg:.3} s")
        print(f"  Keskmine kasti viga: {errAvg:.3}")
        print(f"  Keskmine lisakastide osakaal: {fpAvg:.3}")
        print(f"  Keskmine puuduvate kastide osakaal: {fnAvg:.3}")
        st = f"& {timeAvg:.3} & {errAvg:.3f} & {fpAvg:.3f} & {fnAvg:.3f} \\\\".replace('.', ',')
        stl.append(st)
        print("", st)
        print()
    print()
    return stl

def makeSection(ls, baseName):
    print()
    for a1, a2, a3 in zip(*ls):
        print(f"{baseName} {a1}")
        print(f"{baseName} + müraeemaldus {a2}")
        print(f"{baseName} + müraeemaldus + skaleerimine {a3}")
        print()
    print()

l1 = makeSummary("tess1")
l2 = makeSummary("tess2")
l3 = makeSummary("tess3")
makeSection([l1, l2, l3], r"\tesseract")

l1 = makeSummary("contour1")
l2 = makeSummary("contour2")
l3 = makeSummary("contour3")
makeSection([l1, l2, l3], "Kontuuride leidmine")

l1 = makeSummary("pattern1")
l2 = makeSummary("pattern2")
l3 = makeSummary("pattern3")
makeSection([l1, l2, l3], "Maatrikskõrvutamine")

