from stickframe import StickFrame, StickFramePlayer
from PIL import Image, ImageDraw
import os
import filecmp
from copy import deepcopy


def list_eq(list1, list2):
    if(len(list1) != len(list2)):
        #print("list_eq", "len(list1)", len(list1), "len(list2)", len(list2))
        return False
    comp = [list1[i] == list2[i] for i in range(len(list1))]
    #print("comp list_eq", comp)
    
    return all(comp)

def list_list_eq(list1, list2):
    #print("list_list_eq", "list1", list1, "list2", list2)
        
    if(len(list1) != len(list2)):
        print("list_list_eq", "len(list1)", len(list1), "len(list2)", len(list2))
        return False
    comp = [list_eq(list1[i], list2[i]) for i in range(len(list1))]
    #print("comp list_list_eq", comp)
    return all(comp)



outputPath = "output/"

files = [
    "../country-flags/png1000px/bl.png",
    "../country-flags/png1000px/de.png",
    "../country-flags/png1000px/lv.png",
    "../country-flags/png1000px/ch.png",
    "../country-flags/png1000px/gb.png",
    "../country-flags/png1000px/eu.png",
    "../country-flags/png1000px/ca.png",

    "../country-flags/png1000px/af.png",
    "../country-flags/png1000px/aq.png",

    "../country-flags/png1000px/lk.png",
    "../country-flags/png1000px/kr.png",
    "images/Rainbow-gradient-fully-saturated.svg.png",
    "images/Photo.jpg",
    "images/rainbow2.jpg",
]

for filename in files:

    with Image.open(filename) as im2:
        head, tail = os.path.split(filename)
        name, ext = os.path.splitext(tail)

        resizedFilename = outputPath+name+"_resized.png"
        compressedFilename = outputPath+name+"_uncompressed.png"

        stick2 = StickFrame(im2)
        stick2.name=name
        stick2.im.save(resizedFilename, compress_level=0)

        data2 = deepcopy(stick2.dat)
        assert list_list_eq(data2, stick2.dat), "Testing Deep Copy "+name

        stick2.compress()
        
        compressed = stick2.dumps()
        stick2.dump()
        stick2.uncompress()

        stick2.im.save(compressedFilename, compress_level=0)
        assert list_list_eq(data2, stick2.dat), "Compress Uncompress "+name

        ministick = StickFramePlayer()
        #ministick.loads(compressed)
        ministick.load(name)
        
        #print("ministick.getNextColumn()", ministick.getNextColumn())

        #assert filecmp.cmp(resizedFilename, compressedFilename, shallow=True), "File Comparison " + resizedFilename + " " + compressedFilename 
