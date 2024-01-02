import numpy as np
import filecmp
import sys
import os
import math
from copy import deepcopy
from PIL import Image, ImageDraw
import rle as RLE
from functools import reduce as _reduce
from pathlib import Path
import ujson as json
import struct as struct
import pickle

DATASTORE = "store/"

np.set_printoptions(threshold=sys.maxsize)

class StickFramePlayer():
    compressionType = "RowsRLEofColsRLE"
    compressed = None
    height = 144
    width = None
    heightCM = 100
    widthCM = None
    ourPalette = None
    name="default"

    def __init__(self, height = 144):
        self.height = height
        
    def loads(self, sJSON):
        data = pickle.loads(sJSON)
        compressionType = data['compressionType']
        compressed = data['compressed']
        height = data['height']
        width =  data['width']
        heightCM =  data['heightCM']
        widthCM =  data['widthCM']
        ourPalette =  data['ourPalette']
    
    @property
    def filename(self):
        return DATASTORE + self.name+".pkl"
    
    def load(self, name = None):
        if(name):
            self.name = name

        file = open(self.filename, 'rb')

        data = pickle.load(file)
        compressionType = data['compressionType']
        compressed = data['compressed']
        height = data['height']
        width =  data['width']
        heightCM =  data['heightCM']
        widthCM =  data['widthCM']
        ourPalette =  data['ourPalette']

    def getNextColumn(self):
        if self.compressionType == 'RowsRLEofColsRLE':
            return self.getNextColumn_RowsRLEofColsRLE()
    
    def getNextColumn_RowsRLEofColsRLE(self):
        decoding = RLE.decode(self.compressed[0], self.compressed[1])
        
        col = []
        indexes = []
        remaining = []
        
        for y in range(self.height): #values, counts
            indexes.append(0)
            col.append(decoding[y][0][0])
            remaining.append(decoding[y][1][0]-1)
        yield col
        
        i = 1
        
        while True:
            for y in range(self.height): #values, counts
                if remaining[y] == 0:
                    indexes[y] += 1
                    col[y] = decoding[y][0][indexes[y]]
                    remaining[y] = decoding[y][1][indexes[y]]-1
                else:
                    remaining[y] -= 1
            yield col
            i += 1
            if i >= self.width:
                break
    

class StickFrame(StickFramePlayer): 
    '''
    +String stickImageFilename
    StickFrame : +Int frameNumber
    StickFrame : -[PIL] data 
    StickFrame : +String type 
    StickFrame : +analyse()
    '''

    im = None
    dat = None
    PILmode = None
    debug = False
    
    def __init__(self, im = None, height = 144):
        self.height = height
        if im:
            self.setImage(im)
            
    def setImage(self, im):
        self.im = im.quantize(dither = Image.NONE)
        self.bitDepth = int(round(math.log2(len(self.im.getcolors())),0))
        self.ourPalette = self.im.getpalette()[:3*pow(2,self.bitDepth)]
        self.resizeImage()
        if(self.debug):
            print("Total", self.width * self.height)
            print(self.__class__.__name__, "Palette", self.ourPalette)#self.im.getpalette())
            #print(self.__class__.__name__, "Palette2", self.im.palette.tostring())
            #print(self.__class__.__name__, "bitDepth",self.bitDepth, "getcolors", self.im.getcolors())
        
    def resizeImage(self):
        ratio = self.height / self.im.height    
        self.width = int(self.im.width * ratio)
        if(self.debug):
            print(self.__class__.__name__, "im.width", self.im.width, "im.height", self.im.height, "ratio", ratio, "width", self.width, "height", self.height)
        self.im = self.im.resize((self.width, self.height))
        self.PILmode = deepcopy(self.im.mode)
        
        self.size = self.im.size
        self.dat = np.asarray(self.im)
                        
        self.width = self.im.width
    
    #Priority
    # 1 / 2 colour images
    # 256 palette vertical and horizontal 

    ## ideas and maybe we check which is smallest for an image and use that
    # rle up the column
    
    # rle left to right counting of each item as we go
    # rle left to right building each group as we read it and popping off the top of the mini lists
    # rle left to right (either of the above) but with start column first then length and change arrays played separately
    # First column then changes so fourth col has [(0, 255),(1,0)] changing row 0 to 255 and row 1 to 0 and changing nothing else 
    # changes up form initial row( very unlikely to be good but occasionally my work)
    # just rotated and palletized
    # just rotated but in small enough bits that it doesn't kill everything 
    # some algorithms actually probably not because the choice of horizontal or vert rle / changes would do it 
    def compress(self):
        RowsRLEofColsRLE = self.compress_RowsRLEofColsRLE()

        methods = [
            ["RowsRLEofColsRLE" , self.compress_RowsRLEofColsRLE()],
            ["RowsRLEofCols" , self.compress_RowsRLEofCols()],
            ["RowsofColsRLE" , self.compress_RowsofColsRLE()],
        ]

        sortedMethods = sorted(methods, key=lambda x:len(pickle.dumps(x[1])))

        print(self.name,  "sortedMethods", sortedMethods[0][0])

        print("self.dat", type(self.dat))

        self.compressed = RowsRLEofColsRLE

        return self.compressed
       
        # TODO? : Max out the length to 255 and spread
        # TODO? : Make it a byte array
        # https://docs.python.org/3.5/library/struct.html#module-struct
        # https://docs.micropython.org/en/latest/library/struct.html

        
    def compress_RowsRLEofColsRLE(self):
        lines = []
        for x in self.dat:
            rle = RLE.encode(x)
            lines.append(rle)
        out = RLE.encode(lines)
        return out
    
    def compress_RowsofColsRLE(self):
        lines = []
        for x in self.dat:
            rle = RLE.encode(x)
            lines.append(rle)
        return lines


    def compress_RowsRLEofCols(self):
        lines = []
        for x in self.dat:
            lines.append(list(x))
        out = RLE.encode(lines)
        return out
    






        
    def uncompress(self):
        x = 0
        self.im = Image.new(self.PILmode, self.size, color=0)
        if self.PILmode == "P":
            self.im.putpalette(self.ourPalette) 
        for col in self.getNextColumn():
            for y in range(len(col)):
                self.dat[y][x] = deepcopy(col[y])
                self.im.putpixel((x,y), int(self.dat[y][x]) )
            x += 1 
        

    def dumps(self):
        data = {
            "compressionType": self.compressionType,
            "compressed": self.compressed,
            "height": self.height,
            "width": self.width,
            "heightCM": self.heightCM,
            "widthCM": self.widthCM,
            "ourPalette": self.ourPalette
        }
        return pickle.dumps(data)
        
    def dump(self):
        
        file = open(self.filename, 'wb')
        data = {
            "compressionType": self.compressionType,
            "compressed": self.compressed,
            "height": self.height,
            "width": self.width,
            "heightCM": self.heightCM,
            "widthCM": self.widthCM,
            "ourPalette": self.ourPalette
        }
        return pickle.dump(data, file)

    

class StickFrame1bit(StickFrame):
    ourPalette = [0,0,0,255,255,255]
    def setImage(self, im):
        self.im = im
        self.resizeImage()

    #1 bit RLE always starts with True so is first is False that is a 0 length True
    def compress(self):
        # Compresses single line
        out = []
        for x in deepcopy(self.dat):
            #x = self.dat[0]
            pos, = np.where(np.diff(x) != 0)
            pos = np.concatenate(([0],pos+1,[len(x)]))
            rle = [(b-a) for (a,b) in zip(pos[:-1],pos[1:])]
            #print("self.dat[0]", self.dat[0])
            if (x[0] == False):
                rle = [0]+rle
            #print(rle)
            out.append(rle)
        #print("out", out)
        self.compressed = out
        return out
    
    def getNextColumn(self):
        i = 0
        col = [True] * len(self.compressed)
        compressed = deepcopy(self.compressed)
        #print("compressed", compressed)
        ended = 0
        while True:
            for y in range(len(compressed)):
                #print("y", y, "compressed[y]", compressed[y])
                if compressed[y][0] == 0:
                    #print("swap col[",y,"]", col[y])
                    col[y] = not col[y]
                    #print("swapped col[",y,"]", col[y])
                    
                    compressed[y].pop(0)
                if len(compressed[y]):
                    compressed[y][0] -= 1
                    #print("len(self.compressed[",y,"]) > i", len(self.compressed[y]),  i)
            yield col
            i += 1  # Next execution resumes
            if i >= self.width:
                break

#from PIL import Image, ImageDraw

im = Image.new("1", (10,144), color=0)
draw = ImageDraw.Draw(im)
draw.line((0, 0) + im.size, fill=1)
draw.line((0, im.size[1]-1, im.size[0]-1, 0), fill=1)

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
im.save(outputPath+"test.png", compress_level=0)

stick = StickFrame1bit(im)

data = deepcopy(stick.dat)
assert list_list_eq(data, stick.dat), "Testing Deep Copy"

stick.compress() 
stick.uncompress()

assert list_list_eq(data, stick.dat), "Compress Uncompress"

stick.im.save(outputPath+"test2.png", compress_level=0)

assert filecmp.cmp(outputPath+"test.png", outputPath+"test2.png", shallow=True), "File comparison" 
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
]

for filename in files:

    with Image.open(filename) as im2:
        head, tail = os.path.split(filename)
        name, ext = os.path.splitext(tail)
        
        print(name)

        resizedFilename = outputPath+name+"_resized"+ext
        compressedFilename = outputPath+name+"_uncompressed"+ext

        stick2 = StickFrame(im2)
        stick2.name=name
        stick2.im.save(resizedFilename, compress_level=0)

        data2 = deepcopy(stick2.dat)
        assert list_list_eq(data2, stick2.dat), "Testing Deep Copy "+name

        stick2.compress() 

        compressed = stick2.dumps()
        stick2.dump()

        print("compressed len", len(compressed))

        stick2.uncompress()

        stick2.im.save(compressedFilename, compress_level=0)
        assert list_list_eq(data2, stick2.dat), "Compress Uncompress "+name

        ministick = StickFramePlayer()
        #ministick.loads(compressed)
        ministick.load(name)
        
        #print("ministick.getNextColumn()", ministick.getNextColumn())

        #assert filecmp.cmp(resizedFilename, compressedFilename, shallow=True), "File Comparison " + resizedFilename + " " + compressedFilename 
