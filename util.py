
# util.py

allChars = '''ABCDEFGHIJKLMNOPQRSŠZŽTUVWÕÄÖÜXYabcdefghijklmnopqrsšzžtuvwõäöüxy0123456789%&/"'.,:;_<=>|+-@#()!?€$'''

inf = float("inf")

def boxScale(box, s):
    return tuple(x * s for x in box)

def scale(data, s):
    return [boxScale(box, s) for box in data]

def unscale(data, s):
    return scale(data, 1 / s)

# Kontrolli, kas kast a on kasti b sees
def inside(a, b):
    return a[0] >= b[0] and a[1] >= b[1] and a[2] <= b[2] and a[3] <= b[3]

# Kahe vahemiku kattuvus (täisarvudel)
def overlap(a, b):
    return max(min(a[1], b[1]) - max(a[0], b[0]) + 1, 0)

# kahe ristküliku ühisosa (kattuvus)
# negatiivsete mõõtmetega, kui ristkülikud ei kattu
def intersection(a, b):
    return max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])

# väikseim ristkülik, milles sisalduvad mõlemad sisendiks olevad ristkülikud
def union(a, b):
    return min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3])

# piirdekasti mõõtmed
def boxSize(b):
    return b[2] - b[0] + 1, b[3] - b[1] + 1

def ceilDiv(a, b):
    return (a - 1) // b + 1

# Märgikasti asukoht täiskõrgusega reas
# https://github.com/python-pillow/Pillow/issues/4789#issuecomment-659609574
def getCharBox(c, font):
    return font.getbbox(c)

class ListMap:
    def __init__(self, arr, f):
        self.arr = arr
        self.f = f

    def __getitem__(self, i):
        return self.f(self.arr[i])

    def __len__(self):
        return len(self.arr)

