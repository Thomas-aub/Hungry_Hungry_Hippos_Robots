import struct
from typing import Tuple

from .Pack import Packer, PackTraits

class BytePacker(PackTraits):
    TYPE_NAME   =   'byte'
    CODE        =   '!c'
    LENGTH      =   1
    @classmethod
    def pack(cls,value:int)->str:
        return struct.pack(cls.CODE, bytes(chr(value),'utf-8'))

class CharPacker(PackTraits):
    TYPE_NAME   =   'char'
    CODE        =   '!b'
    LENGTH      =   1
    @classmethod
    def pack(cls,value:int)->str:
        return struct.pack(cls.CODE,ord(value[0]))

class UnsignedCharPacker(PackTraits):
    TYPE_NAME   =   'unsigned char'
    CODE        =   '!B'
    LENGTH      =   1
    @classmethod
    def pack(cls,value:int)->str:
        return struct.pack(cls.CODE,ord(value[0]))

class BoolPacker(PackTraits):
    TYPE_NAME   =   'bool'
    CODE        =   '!?'
    LENGTH      =   1

class ShortPacker(PackTraits):
    TYPE_NAME   =   'short'
    CODE        =   '!h'
    LENGTH      =   2

class UnsignedShortPacker(PackTraits):
    TYPE_NAME   =   'unsigned short'
    CODE        =   '!H'
    LENGTH      =   2

class IntPacker(PackTraits):
    TYPE_NAME   =   'int'
    CODE        =   '!i'
    LENGTH      =   4

class UnsignedIntPacker(PackTraits):
    TYPE_NAME   =   'unsigned int'
    CODE        =   '!I'
    LENGTH      =   4

class LongPacker(PackTraits):
    TYPE_NAME   =   'long'
    CODE        =   '!l'
    LENGTH      =   4

class UnsignedLongPacker(PackTraits):
    TYPE_NAME   =   'unsigned long'
    CODE        =   '!L'
    LENGTH      =   4

class LongLongPacker(PackTraits):
    TYPE_NAME   =   'long long'
    CODE        =   '!q'
    LENGTH      =   8

class UnsignedLongLongPacker(PackTraits):
    TYPE_NAME   =   'unsigned long long'
    CODE        =   '!Q'
    LENGTH      =   8

class FloatPacker(PackTraits):
    TYPE_NAME   =   'float'
    CODE        =   '!f'
    LENGTH      =   4

class DoublePacker(PackTraits):
    TYPE_NAME   =   'double'
    CODE        =   '!d'
    LENGTH      =   8

class StringPacker(PackTraits):
    TYPE_NAME   =   'str'
    CODE        =   '!s'
    LENGTH      =   -1
    @classmethod
    def pack(cls,value: str)->str:
        if value == '':
            return Packer.pack(0)
        s = bytes(value,'utf-8')
        return Packer.pack(len(s))+s
    @classmethod
    def unpack(cls,buffer:str,index:int)->Tuple[int,str]:
        try:
            index, l = Packer.unpack(buffer,index)
            if l==0: return index,''
            tmp = buffer[index:]
            s = tmp[:l]
            index += l
            return index, s.decode()
        except Exception:
            raise

class ListPacker(PackTraits):
    TYPE_NAME   =   'list'
    CODE        =   '!['
    LENGTH      =   -1
    @classmethod
    def pack(cls,value: list)->str:
        tmp = [ 
            Packer.pack(len(value))
            ] + [
                Packer.pack(x) for x in value
            ]
        return b''.join(tmp)
    @classmethod
    def unpack(cls,buffer:str,index:int)->Tuple[int,list]:
        try:
            values = []
            index,nb = Packer.unpack(buffer, index)
            for i in range(nb):
                tmp = Packer.unpack(buffer,index)
                index, v = tmp
                values.append(v)
            return index, values
        except Exception:
            raise

class DictPacker(PackTraits):
    TYPE_NAME   =   'dict'
    CODE        =   '!{'
    LENGTH      =   -1
    @classmethod
    def pack(cls,value: dict)->str:
        items = value.items ()
        print(items)
        tmp = [ 
            Packer.pack(len(value))
            ] + [
                b''.join([Packer.pack(x[0]),Packer.pack(x[1])]) for x in items
            ]
        return b''.join(tmp)
    @classmethod
    def unpack(cls,buffer:str,index:int)->Tuple[int,dict]:
        try:
            values = {}
            index,nb = Packer.unpack(buffer, index)
            for i in range(nb):
                tmp = Packer.unpack(buffer,index)
                index, key = tmp
                tmp = Packer.unpack(buffer,index)
                index, value = tmp
                values[key] = value
            return index, values
        except Exception:
            raise

