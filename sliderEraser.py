import os
import sys

with open("map.osu") as f:
    lines = f.readlines()
indeks = 0
for line in lines:
    indeks += 1
    if line == "[HitObjects]\n":
        break
linesPom = lines[:indeks]
linesHit = lines[indeks:]
for i in range(len(linesHit)):
    linesHit[i] = linesHit[i].split(",")
for i in range(len(linesHit)):
    linesHit[i] = linesHit[i][:3]
for i in linesHit:
    i.append("1")
    i.append("8")
    i.append("0:1:0:0:")
zapis = open("nowaMapa.osu", "w")
for x in linesPom:
    zapis.write(x)
for x in linesHit:
    line = ""
    for y in x:
        line += y + ","
    line = line[:-1]
    zapis.write(line + "\n")
zapis.close()

