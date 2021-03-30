import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# https://stackoverflow.com/a/4270437

fig = plt.figure(figsize=(6, 4))
ax = fig.add_subplot(111)

def plotData(data, color):
    for d in data:
        d = list(d)
        d.sort()
        xv = []
        yv = []
        for x, y in d:
            xv.append(x)
            yv.append(y)
        
        ax.plot(xv, yv, color=color, linewidth=1)
        ax.scatter(xv, yv, color=color, s=2, marker="s")

data1 = [[(0.083, 0.074), (0.097, 0.063), (0.086, 0.088)],
         [(0.119, 0.090), (0.121, 0.073), (0.116, 0.099)],
         [(0.152, 0.090), (0.181, 0.082), (0.154, 0.104)]]

plotData(data1, "red")

data2 = [[(0.308, 0.079), (0.309, 0.078), (0.164, 0.090)],
         [(0.334, 0.098), (0.339, 0.094), (0.193, 0.172)],
         [(0.357, 0.117), (0.366, 0.113), (0.187, 0.210)]]
plotData(data2, "green")

data3 = [[(0.199, 0.072), (0.205, 0.075), (0.213, 0.057)],
         [(0.265, 0.053), (0.262, 0.058), (0.279, 0.042)],
         [(0.267, 0.349), (0.265, 0.283), (0.278, 0.217)]]

plotData(data3, "blue")

# https://matplotlib.org/stable/gallery/text_labels_and_annotations/custom_legends.html
metaLines = [Line2D([0], [0], color="red"),
             Line2D([0], [0], color="green"),
             Line2D([0], [0], color="blue")]

ax.legend(metaLines, ["Tesseract", "Kontuuripõhine tuvastamine", "Maatrikskõrvutamine"])

plt.xlabel("$f_n$")
plt.ylabel("$f_p$")
plt.show()
