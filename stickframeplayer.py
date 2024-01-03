from functools import reduce as _reduce
import pickle

DATASTORE = "store/"

def rle_decode(values, counts):
    """
    Decodes run-length encoding of given iterable.
    
    Parameters
    ----------
    values, counts: List of contiguous unique values, and list of counts
    
    Returns
    -------
    seq: Decoded sequence
    """
    assert len(values) == len(counts), 'len(values) != len(counts)'
    
    try:
        counts = [int(i) for i in counts]
    except:
        raise ValueError('Counts contain non-integer values')
    
    seq = [[i] * j for i, j in zip(values, counts)]
    seq = _reduce(lambda x, y: x + y, seq)
    return seq

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
        col = rle_decode(decoding[0][0][0], decoding[0][0][1])
        
        remaining = decoding[1][0]-1
        yield col
        
        j = 1
        
        while True:
            if remaining == 0:
                index += 1
                col = rle_decode(decoding[0][index][0], decoding[0][index][1])
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
            col = rle_decode(decoding[x][0], decoding[x][1])
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
        decoding = rle_decode(self.compressed[0], self.compressed[1])
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
        decoding = rle_decode(self.compressed[0], self.compressed[1])
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