import struct
from typing import Tuple

class Packer:
    __packerList = []
    @classmethod
    def registerPackable(cls,type,code,packer,unpacker):
        cls.__packerList.append({'type': type, 'code': code, 'packer': packer, 'unpacker': unpacker})
    @classmethod
    def __packInfo(cls,value,forcedType=None):
        vtype = type(value).__name__ if forcedType == None else forcedType 
        # print("search for type ",vtype)
        infos = list(filter(lambda x: x['type']==vtype,cls.__packerList))
        if len(infos)!=1: return None
        info = infos[0]
        code = info['code']
        pack = [ info['packer'] ]
        return [code]+pack
    @classmethod
    def __unpackInfo(cls,code):
        infos = list(filter(lambda x: x['code']==code[:2],cls.__packerList))
        if len(infos)!=1: return None
        info = infos[0]
        ncode = info['code']
        unpack = [info['unpacker']]
        return[ncode] + unpack
    @classmethod
    def pack(cls,value,forcedType=None):
        packerInfo = cls.__packInfo(value,forcedType)
        code = packerInfo[0]
        fn = packerInfo[1]
        del packerInfo[1]
        del packerInfo[0]
        buf = fn(value)
        buf = code.encode() + buf
        return buf
    @classmethod
    def unpack(cls,buffer,index):
        unpackerInfo = cls.__unpackInfo(buffer[index:(index+2)].decode())
        code = unpackerInfo[0]
        fn = unpackerInfo[1]
        del unpackerInfo[1]
        del unpackerInfo[0]
        index = index + len(code)
        return fn(buffer,index)

class PackTraits:
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        name = cls.TYPE_NAME
        code = cls.CODE
        Packer.registerPackable(name,code,
                                lambda v: cls.pack(v),
                                lambda v,i: cls.unpack(v,i))
    @classmethod
    def pack(cls,value):
        return struct.pack(cls.CODE,value)
    @classmethod
    def unpack(cls,buffer,index):
        try:
            value = struct.unpack(cls.CODE,buffer[index:(index+cls.LENGTH)])[0]
            index += cls.LENGTH
            return index, value
        except Exception:
            raise
