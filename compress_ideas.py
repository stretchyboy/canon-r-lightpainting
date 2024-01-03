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
    compressionType = "VertRleOfHoriRle"
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
        if self.compressionType == 'VertRleOfHoriRle':
            return self.getNextColumn_VertRleOfHoriRle()
        elif self.compressionType == 'VertRleOfHori':
            return self.getNextColumn_VertRleOfHori()
        elif self.compressionType == 'VertOfHoriRle':
            return self.getNextColumn_VertOfHoriRle()
        elif self.compressionType == 'HoriOfVert':
            return self.getNextColumn_HoriOfVert()
        elif self.compressionType == 'HoriOfVertRle':
            return self.getNextColumn_HoriOfVertRle()
        elif self.compressionType == 'HoriRleOfVert':
            return self.getNextColumn_HoriRleOfVert()
        elif self.compressionType == 'HoriRleOfVertRle':
            return self.getNextColumn_HoriRleOfVertRle()
        else:
            raise Exception("Decompressing "+ self.compressionType +" not implemented")


    def getNextColumn_HoriRleOfVertRle(self):
        decoding = self.compressed
        col = []
        index = 0
        remaining = None
        col = RLE.decode(decoding[0][0][0], decoding[0][0][1])
        
        remaining = decoding[1][0]-1
        yield col
        
        j = 1
        
        while True:
            if remaining == 0:
                index += 1
                col = RLE.decode(decoding[0][index][0], decoding[0][index][1])
                remaining = decoding[1][index]-1
            else:
                remaining -= 1
            yield col
            j += 1
            if j >= self.width:
                break
    

    def getNextColumn_HoriOfVert(self):
        decoding = self.compressed
        col = []
        x = 0
        
        while True:
            col = decoding[x]
            yield col
            x += 1
            if x >= self.width:
                break

    def getNextColumn_HoriOfVertRle(self):
        decoding = self.compressed
        col = []
        x = 0
        
        while True:
            col = RLE.decode(decoding[x][0], decoding[x][1])
            yield col
            x += 1
            if x >= self.width:
                break

    def getNextColumn_HoriRleOfVert(self):
        decoding = self.compressed
        col = []
        index = 0
        remaining = None
        col = decoding[0][0]
        remaining = decoding[1][0]-1
        yield col
        
        j = 1
        
        while True:
            if remaining == 0:
                index += 1
                col = decoding[0][index]
                remaining = decoding[1][index]-1
            else:
                remaining -= 1
            yield col
            j += 1
            if j >= self.width:
                break



    def getNextColumn_VertOfHoriRle(self):
        decoding = self.compressed
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
    

    def getNextColumn_VertRleOfHori(self):
        decoding = RLE.decode(self.compressed[0], self.compressed[1])
        col = [0] * self.height         
        i = 0
        
        while True:
            for y in range(self.height): #values, counts
                col[y] = decoding[y][i]
            yield col
            i += 1
            if i >= self.width:
                break
    

    def getNextColumn_VertRleOfHoriRle(self):
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
    ## Check which is smallest for an image and use that
    def compress(self, compressionType = None):
        methods = [
            ["VertRleOfHoriRle" , self.compress_VertRleOfHoriRle()],
            ["VertRleOfHori" , self.compress_VertRleOfHori()],
            ["VertOfHoriRle" , self.compress_VertOfHoriRle()],
            ["HoriOfVert" , self.compress_HoriOfVert()],
            ["HoriRleOfVert" , self.compress_HoriRleOfVert()],
            ["HoriRleOfVertRle" , self.compress_HoriRleOfVertRle()],
            ["HoriOfVertRle" , self.compress_HoriOfVertRle()],
        ]

        if compressionType:
            methods = filter(lambda x:x[0]==compressionType, methods)
        
        sortedMethods = sorted(methods, key=lambda x:len(pickle.dumps(x[1])))

        self.compressionType = sortedMethods[0][0]
        self.compressed = sortedMethods[0][1]

        return self.compressed
       
        # TODO? : Max out the length to 255 and spread
        # TODO? : Make it a byte array
        # https://docs.python.org/3.5/library/struct.html#module-struct
        # https://docs.micropython.org/en/latest/library/struct.html


    def compress_HoriOfVertRle(self):
        cols = []
        for col in self.dat.T:
            cols.append(RLE.encode(col.tolist()))
        out = cols
        if self.debug:
            print(self.name, "HoriOfVertRle", len(pickle.dumps(out)))
        return out


    def compress_HoriRleOfVertRle(self):
        cols = []
        for col in self.dat.T:
            cols.append(RLE.encode(col.tolist()))
        out = RLE.encode(cols)
        if self.debug:
            print(self.name, "HoriRleOfVertRle", out, len(pickle.dumps(out)))
        return out

    def compress_HoriRleOfVert(self):
        cols = []
        for col in self.dat.T:
            cols.append(list(col))
        out = RLE.encode(cols)
        if self.debug:
            print(self.name, "HoriRleOfVert", len(pickle.dumps(out)))
        return out
    

    def compress_HoriOfVert(self):
        out = []
        for col in self.dat.T:
            out.append(col.tolist())

        if self.debug:
            print(self.name, "HoriOfVert", len(pickle.dumps(out)))
        return out
    
        
    def compress_VertRleOfHoriRle(self):
        lines = []
        for x in self.dat:
            rle = RLE.encode(x.tolist())
            lines.append(rle)
        out = RLE.encode(lines)
        if self.debug:
            print(self.name, "VertRleOfHoriRle", len(pickle.dumps(out)))
        return out
    
    def compress_VertOfHoriRle(self):
        lines = []
        for x in self.dat:
            rle = RLE.encode(x.tolist())
            lines.append(rle)
        if self.debug:
            print(self.name, "VertOfHoriRle", len(pickle.dumps(lines)))
        return lines


    def compress_VertRleOfHori(self):
        lines = []
        for x in self.dat:
            lines.append(x.tolist())
        out = RLE.encode(lines)
        if self.debug:
            print(self.name, "VertRleOfHori", len(pickle.dumps(out)))
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
