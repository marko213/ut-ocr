
# generate.py

from PIL import Image, ImageDraw, ImageFont
import random
import numpy as np
import json
from pathlib import Path
import os

# https://pillow.readthedocs.io/en/stable/reference/Image.html


##########################################################

# Genereeritavate piltide arv iga märgijärjendi kohta
imageCount = 100

# Algne pildi suurus (pikslites, x ja y)
sizeX = range(300, 801, 10)
sizeY = range(300, 801, 10)

# Tekstilõigu (kasti) suurus
boxSizeX = range(100, 401)
boxSizeY = range(30, 101)

# Minimaalne "tühi ruum" tekstilõigu ümber (pikslites, x ja y)
padX = 20
padY = 5

# Reavahe suurus (pikslites)
rowSkip = range(4, 11)

# Maksimaalne tekstilõikude arv pildil
maxParagraphs = 7

# Maksimaalne "sõna" pikkus (ligikaudu)
maxWord = 10

# Konstandid märgijärjendite defineerimiseks
LATIN_UPPERCASE    = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
LATIN_LOWERCASE    = "abcdefghijklmnopqrstuvwxyz"
ESTONIAN_UPPERCASE = "ABCDEFGHIJKLMNOPQRSŠZŽTUVWÕÄÖÜXY"
ESTONIAN_LOWERCASE = "abcdefghijklmnopqrsšzžtuvwõäöüxy"
NUMBER             = "0123456789" 
PUNCTUATION        = '''%&/"'.,:;_<=>|+-@#()!?€$'''

# Kasutatavad märgijärjendid
sequences = [
    {"whitelist": LATIN_UPPERCASE + LATIN_LOWERCASE + NUMBER,
     "seq": [
        [(LATIN_UPPERCASE, 1, maxWord)], # ABCD
        [(LATIN_UPPERCASE, 1, 1), (LATIN_LOWERCASE, 1, maxWord - 1)], # Abcd
        [(LATIN_LOWERCASE, 1, maxWord)],  # abcd
        [(NUMBER, 1, maxWord)] # 0123
    ]},
    {"whitelist": ESTONIAN_UPPERCASE + ESTONIAN_LOWERCASE + NUMBER,
     "seq": [
        [(ESTONIAN_UPPERCASE, 1, maxWord)], # ÄÜCD
        [(ESTONIAN_UPPERCASE, 1, 1), (ESTONIAN_LOWERCASE, 1, maxWord - 1)], # Äücd
        [(ESTONIAN_LOWERCASE, 1, maxWord)],  # äücd
        [(NUMBER, 1, maxWord)] # 0123
    ]},
    {"whitelist": ESTONIAN_UPPERCASE + ESTONIAN_LOWERCASE + NUMBER + PUNCTUATION,
     "seq": [
        [(PUNCTUATION, 0, 2), (ESTONIAN_UPPERCASE, 1, maxWord - 2), (PUNCTUATION, 0, 2)], # ..ÄÜCD..
        [(PUNCTUATION, 0, 2), (ESTONIAN_UPPERCASE, 1, 1), (ESTONIAN_LOWERCASE, 1, maxWord - 3), (PUNCTUATION, 0, 2)], # ..Äücd..
        [(PUNCTUATION, 0, 2), (ESTONIAN_LOWERCASE, 1, maxWord - 2), (PUNCTUATION, 0, 2)],  # ..äücd..
        [(PUNCTUATION, 0, 2), (NUMBER, 1, maxWord // 2 - 2), (PUNCTUATION, 0, 1), (NUMBER, 0, maxWord // 2 - 1), (PUNCTUATION, 0, 2)] # ..01.23..
    ]}
]

# Suuruse kordaja (skaleerimine)
scaleFactor = np.arange(0.6, 1.51, 0.1)

# Skaleerimisel kasutatavad meetodid
# https://pillow.readthedocs.io/en/stable/handbook/concepts.html#concept-filters
scaleMethods = [
    Image.BILINEAR,
    Image.BICUBIC
]

# Värvid
lightRange = range(180, 256)
darkRange = range(0, 71)

# Fondid (nimed)
fontNames = [
    "LiberationSans-Regular.ttf",
    "LiberationSans-Bold.ttf",
    "LiberationMono-Regular.ttf",
    "LiberationSerif-Regular.ttf",
    "LiberationSerif-Bold.ttf"
]

# Fontide suurused
fontSizes = [12, 14, 16, 18]

# Maksimaalne ühel pildil olevate eri fontide (suurus / tüüp) arv
fontsPerImage = 2

# Väljundkaust
outDir = Path("out")

# Väljundkvaliteet (JPEG)
qualityRange = range(60, 81)

##########################################################

# Fikseeritud andmestik
# Ülalolevate sätete muutmisel võib kogu andmestik muutuda
random.seed(312)

# Fondid fondinimest ja suurusest
fonts = []
for fn in fontNames:
    for fs in fontSizes:
        fonts.append((ImageFont.truetype(fn, size=fs), fn, fs))

# Väljunkaust
os.makedirs(outDir, exist_ok=True)

        
# Värv väärtusevahemikust
def RGBFromRange(r):
    return tuple(random.choice(r) for _ in range(3))

# Kas kaks ristkülikut kattuvad
def intersect(a, b):
    return not (a[0] >= b[2] or b[0] >= a[2] or a[1] >= b[3] or b[1] >= a[3])

# Mustri järgi ühe "sõna" loomine
def genWord(pattern):
    word = []
    for p in pattern:
        word += random.choices(p[0], k=random.randint(p[1], p[2]))
    
    return "".join(word)

# Ühe tekstirea loomine
def genRow(maxWidth, font, sequence):
    text = ""
    textWidth = 0

    t = 0
    while t < 5:
        newText = ""
        if text != "":
            newText += " "
        newText += genWord(random.choice(sequence))

        w = font.getsize(newText)[0]
        if textWidth + w <= maxWidth:
            text += newText
            textWidth += w
            t = 0
        else:
            t += 1
    return text

# Märgikastide asukohad ühes reas
# https://github.com/python-pillow/Pillow/issues/4789#issuecomment-659609574
def getBoxes(s, font, offsetX, offsetY):
    boxes = []
    x0, y0 = offsetX, offsetY
    for i, c in enumerate(s):
        x1, y1, x2, y2 = font.getbbox(c)
        boxes.append([x0 + x1, y0 + y1, x0 + x2, y0 + y2])
        x0 += font.getlength(c)
    return boxes

# Ürita lisada üks lõik pildile
def addTextBox(draw, font, sequence, data):
    size = data['initialSize']
    for _ in range(20):
        while True:
            left = random.randint(0, size[0] - 1)
            top = random.randint(0, size[1] - 1)
            width = random.choice(boxSizeX)
            height = random.choice(boxSizeY)
            if left + width < size[0] and top + height < size[1]:
                break
        right = left + width
        bottom = top + height
        box = [left, top, right, bottom]
        for o in data['paragraphs']:
            if intersect(box, o['box']):
                break
        else:
            rowSpace = random.choice(rowSkip)
            paragraph = {
                'box': [left, top, right, bottom],
                'font': {'name': font[1], 'size': font[2]},
                'rowSpace': rowSpace
            }
            #draw.rectangle(box, outline="red") # debug
            
            maxWidth = width - 2 * padX
            maxHeight = height - 2 * padY
            textHeight = font[0].getsize("Ajy")[1]

            currHeight = textHeight
            rows = [genRow(maxWidth, font[0], sequence)]
            while currHeight + rowSpace + textHeight <= maxHeight:
                rows.append(genRow(maxWidth, font[0], sequence))
                currHeight += rowSpace + textHeight
            
            paragraph['rows'] = []

            curY = top + padY
            for r in rows:
                draw.text((left + padX, curY), r, fill=data['textColor'], font=font[0])
                boxes = getBoxes(r, font[0], left + padX, curY)
                rowData = [(c, b) for c, b in zip(r, boxes) if c != ' ']
                paragraph['rows'].append(rowData)
                curY += textHeight + rowSpace
            data['paragraphs'].append(paragraph)
            return True
    return False

# Pildile teksti kirjutamine
def addText(img, sequence, data):
    data['paragraphs'] = []

    textColor = RGBFromRange(darkRange)
    data['textColor'] = textColor

    draw = ImageDraw.Draw(img)
    imageFonts = random.sample(fonts, k=fontsPerImage)
    for _ in range(maxParagraphs):
        currFont = random.choice(imageFonts)
        addTextBox(draw, currFont, sequence, data)
    

# Pildi ümber skaleerimine
def transform(img, data):
    factor = random.choice(scaleFactor)
    data['scaleFactor'] = factor

    newSize = tuple(int(round(s * factor)) for s in img.size)
    data['newSize'] = newSize

    mode = random.choice(scaleMethods)
    data['scaleMode'] = mode

    img = img.resize(newSize, resample=mode)
    return img

# Üks genereeritud pilt
def sample(sequence):
    data = {}

    bgColor = RGBFromRange(lightRange)
    data['bgColor'] = bgColor

    size = random.choice(sizeX), random.choice(sizeY)
    data['initialSize'] = size

    img = Image.new("RGB", size, color=bgColor)

    addText(img, sequence, data)
    img = transform(img, data)

    data['quality'] = random.choice(qualityRange)

    return img, data


for si, seq in enumerate(sequences):
    for i in range(imageCount):
        img, data = sample(seq['seq'])
        data['sequenceNum'] = si
        data['whitelist'] = seq['whitelist']
        filebase = f"{si}_{i:03}"
        img.save(outDir / ("img" + filebase + ".jpg"), "JPEG", quality=data['quality'])
        with open(outDir / ("meta" + filebase + ".json"), "w") as metaFile:
            json.dump(data, metaFile)
