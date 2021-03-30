
# generateSingle.py

from pathlib import Path
import json
import random

# Genereeritud piltide arv iga märgijärjendi kohta
imageCount = 100

# Genereeritavate märkide arv iga märgijärjendi kohta
boxCount = 500

# Märgijärjendite arv
sequenceCount = 3

# Genereeritud andmete kaust
dataDir = Path("out")

#####################################################

random.seed(312)

samples = []
for si in range(sequenceCount):
    seqSamples = []
    for _ in range(boxCount):
        # Väldi tühjasid hulkasid
        while True:
            # pilt
            ci = random.randint(0, imageCount - 1)
            with open(dataDir / f"meta{si}_{ci:03}.json") as f:
                data = json.load(f)
            
            # lõik
            par = random.choice(data['paragraphs'])
            if len(par['rows']) == 0:
                continue
            
            # rida
            row = random.choice(par['rows'])
            if len(row) == 0:
                continue
            
            # märk
            char = random.choice(row)
            break

        # skaleeri pildi põhjal
        char[1] = [x * data['scaleFactor'] for x in char[1]]

        # lisa pildi number
        s = ci, char[0], char[1]

        seqSamples.append(s)

    samples.append(seqSamples)

with open("singlechar.json", "w") as f:
    json.dump(samples, f)
