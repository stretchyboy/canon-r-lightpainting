import numpy as np
import sys
import math
from copy import deepcopy
from PIL import Image, ImageDraw
#import rle as RLE
from rle import encode as rle_encode
from functools import reduce as _reduce
from pathlib import Path
import json
from stickframeplayer import StickFramePlayer

np.set_printoptions(threshold=sys.maxsize)
    

class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.bool_):
            return bool(obj)
        if isinstance(obj, (np.floating, np.complexfloating)):
            return float(obj)
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.string_):
            return str(obj)
        return super(NpEncoder, self).default(obj)
    

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
        self.bitDepth = int(math.ceil(math.log2(len(self.im.getcolors())),0))
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
        
        
        #self.size = self.im.size
        self.dat = np.asarray(self.im)
                        
        self.width = self.im.width
    
    @property
    def size(self):
        return (self.width, self.height)
    
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
        
        sortedMethods = sorted(methods, key=lambda x:len(json.dumps(x[1], cls=NpEncoder)))

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
            cols.append(rle_encode(col.tolist()))
        out = cols
        if self.debug:
            print(self.name, "HoriOfVertRle", len(json.dumps(out)))
        return out


    def compress_HoriRleOfVertRle(self):
        cols = []
        for col in self.dat.T:
            cols.append(rle_encode(col.tolist()))
        out = rle_encode(cols)
        if self.debug:
            print(self.name, "HoriRleOfVertRle", out, len(json.dumps(out)))
        return out

    def compress_HoriRleOfVert(self):
        cols = []
        for col in self.dat.T:
            cols.append(list(col))
        out = rle_encode(cols)
        if self.debug:
            print(self.name, "HoriRleOfVert", len(json.dumps(out)))
        return out
    

    def compress_HoriOfVert(self):
        out = []
        for col in self.dat.T:
            out.append(col.tolist())

        if self.debug:
            print(self.name, "HoriOfVert", len(json.dumps(out)))
        return out
    
        
    def compress_VertRleOfHoriRle(self):
        lines = []
        for x in self.dat:
            rle = rle_encode(x.tolist())
            lines.append(rle)
        out = rle_encode(lines)
        if self.debug:
            print(self.name, "VertRleOfHoriRle", len(json.dumps(out)))
        return out
    
    def compress_VertOfHoriRle(self):
        lines = []
        for x in self.dat:
            rle = rle_encode(x.tolist())
            lines.append(rle)
        if self.debug:
            print(self.name, "VertOfHoriRle", len(json.dumps(lines)))
        return lines


    def compress_VertRleOfHori(self):
        lines = []
        for x in self.dat:
            lines.append(x.tolist())
        out = rle_encode(lines)
        if self.debug:
            print(self.name, "VertRleOfHori", len(json.dumps(out)))
        return out

        
    def uncompress(self):
        x = 0
        self.dat = [[0]*self.width] * self.height
        self.im = Image.new("P", self.size, color=0)
        self.im.putpalette(self.ourPalette) 
        for col in self.getNextColumn():
            for y in range(len(col)):
                self.dat[y][x] = col[y]
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
        return json.dumps(data, cls=NpEncoder)
        
    def dump(self):
        
        file = open(self.filename, 'w')
        data = {
            "compressionType": self.compressionType,
            "compressed": self.compressed,
            "height": self.height,
            "width": self.width,
            "heightCM": self.heightCM,
            "widthCM": self.widthCM,
            "ourPalette": self.ourPalette
        }
        return json.dump(data, file, cls=NpEncoder)
