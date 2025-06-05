
def slice_per(source, step):
    l = len(source)
    nb = int(l/step)
    if nb*step < l: nb += 1
    return [source[(i*step):min(l,((i+1)*step))] for i in range(nb)]

class Buffer:
    def __init__(self,data = []):
        self.buffer = data
    def displayString(self)->None:
        tmp = slice_per(['{:02x}'.format(x) for x in self.buffer],16)
        tmp2 = slice_per(self.buffer,16)
        strs = []
        for x,y in zip(tmp,tmp2):
            decal = ''
            if len(x) < 16:
                decal = '   '*(16-len(x))
            v = [int(c) for c in y]
            vv = ''.join([(chr(c) if c>= 32 and c<=128 else '.') for c in v])
            strs.append(''.join([' '.join(x),decal,' : ',vv]))
        return '\n'.join(strs)
    @property
    def length(self):
        return len(self.buffer)
