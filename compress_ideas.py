import numpy as np
import filecmp
import sys
import math
from copy import deepcopy
from PIL import Image, ImageDraw


np.set_printoptions(threshold=sys.maxsize)


class StickFrame() : 
    im = None
    dat = None
    compressed = None
    PILmode = None
    height = 144
    width = None
    debug = True
    '''
    +String stickImageFilename
    StickFrame : +Int frameNumber
    StickFrame : -[PIL] data 
    StickFrame : +String type 
    StickFrame : +analyse()
    '''

    def __init__(self, im = None, height = 144):
        self.height = height
        if im:
            self.setImage(im)
            
    def setImage(self, im):
        self.im = im.quantize(dither = Image.NONE)
        self.bitdepth = int(round(math.log2(len(self.im.getcolors())),0))
        self.ourPalette = self.im.getpalette()[:3*pow(2,self.bitdepth)]
        self.resizeImage()
        if(self.debug):
            print("Total", self.width * self.height)
            print(self.__class__.__name__, "Palette", self.ourPalette)#self.im.getpalette())
            #print(self.__class__.__name__, "Palette2", self.im.palette.tostring())
            #print(self.__class__.__name__, "bitdepth",self.bitdepth, "getcolors", self.im.getcolors())
        
    def resizeImage(self):
        ratio = self.height / self.im.height    
        self.width = int(self.im.width * ratio)
        if(self.debug):
            print(self.__class__.__name__, "im.width", self.im.width, "im.height", self.im.height, "ratio", ratio, "width", self.width, "height", self.height)
        self.im = self.im.resize((self.width, self.height))
        # TODO : resize before saving
        self.PILmode = deepcopy(self.im.mode)
        
        self.size = self.im.size
        self.dat = np.asarray(self.im)
        self.width = self.im.width

    def compress_cell(self, cell):
        return cell 
    
    def upcompress_cell(self, item):
        cell = item
        return cell 
    
    #Priority
    # 1 / 2 colour images
    # 256 pallette vertical and horizontal 

    ## ideas and maybe we check which is smallest for an image and use that
    # rle up the column
    
    # rle left to right counting of each item as we go
    # rle left to right building each group as we read it and poping off the top of the mini lists
    # rle left to right (either of the above) but with start column first then length and change arrays played seperately
    # First column then changes so fourth col has [(0, 255),(1,0)] changing row 0 to 255 and row 1 to 0 and changing nothing else 
    # changes up form initial row( very unlikely to be good but accaisonnly my work)
    # just rotated and palletized
    # just rotated but in small enough bits that it doesn't kill everything 
    # some algorythms actualy proabably not because the chouse of hori or vert rle / changes would do it 
    def compress(self):
        out = []
        for x in self.dat:
            pos, = np.where(np.diff(x) != 0)
            pos = np.concatenate(([0],pos+1,[len(x)]))
            rle = [(b-a,x[a]) for (a,b) in zip(pos[:-1],pos[1:])]

            # TODO : max out the length to 255 and spread
            # TODO : Make it a byte array
            # https://docs.python.org/3.5/library/struct.html#module-struct
            # https://docs.micropython.org/en/latest/library/struct.html

            out.append(rle)
        print("compress out", out)
        self.compressed = out
        return out
    
    def getNextColumn(self):
        return []
        pass

    def uncompress(self):
        x = 0
        self.im = Image.new(self.PILmode, self.size, color=0)
        for col in self.getNextColumn():
            #print("returned col", x, col)
            for y in range(len(col)):
                self.dat[y][x] = deepcopy(col[y])
                #print("self.dat[",y,"][",x,"]", self.dat[y][x])
                self.im.putpixel((x,y), int(self.dat[y][x]) )
            x += 1 
        

    def save(self):
        #print("self.dat", self.dat)
        #print("self.PILmode", self.PILmode)
        #self.im = Image.fromarray(self.dat, mode=self.PILmode)
        pass
        
        
    def load(self):
        pass
    


class StickFramePalleted(StickFrame):

    '''
    StickFramePalleted : +List~int~ pallete
    StickFramePalleted : +colourDepth
    StickFramePalleted : +compress()
    StickFramePalleted : +getNextColumn()
    '''


class StickFrame1bit(StickFramePalleted):
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

    
    '''
    def getNextColumn(self):
        i = 0
        compressedlinepos = []
        eleremaining = []
        col = []
        ended = 0
        for y in range(len(self.compressed)):
            if self.compressed[y][i] == 0 :
                compressedlinepos.append(1)
                if(len(self.compressed[y]) >= i):
                   eleremaining.append(self.compressed[y][i+1])
                else:
                    eleremaining.append(0)
                col.append(False)
            else:
                compressedlinepos.append(0)
                eleremaining.append(self.compressed[y][i]-1)
                col.append(True)
        #print("First col", col)
        yield col
        i += 1
        # An Infinite loop to generate squares
        while True:
            for y in range(len(self.compressed)):
                if eleremaining[y] == 0:
                    compressedlinepos[y] += 1
                    col[y] = not col[y]
                    #print("len(self.compressed[",y,"]) > i", len(self.compressed[y]),  i)
                    if(i +1 < len(self.compressed[y])):
                        eleremaining[y] = self.compressed[y][i+1]
                    else:
                        eleremaining[y] = 0
                        
                else:
                    eleremaining[y] -= 1
            #if ended < 1:
            #print("col", i, col)
            yield col
            i += 1  # Next execution resumes
            if i >= self.width:
                break

    '''
    
    '''
    StickFrame1bit : 
    StickFrame1bit : +compress()
    StickFrame1bit : +getNextColumn()

    '''

    '''
    note for StickFrame1bit "Run Length Encoding\nhttps://tinyurl.com/2h54atwk"
    note for StickFrame "https://www.geeksforgeeks.org/use-yield-keyword-instead-return-keyword-python/"
    '''

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

im.save("test.png")

stick = StickFrame1bit(im)

data = deepcopy(stick.dat)
assert list_list_eq(data, stick.dat), "Testing Deep Copy"

stick.compress() 
stick.uncompress()

assert list_list_eq(data, stick.dat), "Compress Uncompress"


stick.save()
stick.im.save("test2.png")

assert filecmp.cmp("test.png", "test2.png", shallow=True), "File comparision" 

with Image.open("../country-flags/png1000px/lv.png") as im2:
    #"../country-flags/png1000px/de.png"
    #"../country-flags/png1000px/ca.png"
    #"../country-flags/png1000px/ch.png"
    #"../country-flags/png1000px/eu.png"
    stick2 = StickFrame(im2)
    stick2.im.save("test3.png")

    data2 = deepcopy(stick2.dat)
    assert list_list_eq(data2, stick2.dat), "2 Testing Deep copy"

    stick2.compress() 
    stick2.uncompress()

    assert list_list_eq(data2, stick2.dat), "2 Compress Uncompress"
    stick2.im.save("test4.png")
