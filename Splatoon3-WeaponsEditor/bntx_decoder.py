import struct
import os

# =============================================
# BNTX Extractor (Adapted from AboodXD) thx :)
# =============================================

formats = {
    0x0b01: 'R8_G8_B8_A8_UNORM',
    0x0b06: 'R8_G8_B8_A8_SRGB',
    0x0701: 'R5_G6_B5_UNORM',
    0x0201: 'R8_UNORM',
    0x0901: 'R8_G8_UNORM',
    0x1a01: 'BC1_UNORM',
    0x1a06: 'BC1_SRGB',
    0x1b01: 'BC2_UNORM',
    0x1b06: 'BC2_SRGB',
    0x1c01: 'BC3_UNORM',
    0x1c06: 'BC3_SRGB',
    0x1d01: 'BC4_UNORM',
    0x1d02: 'BC4_SNORM',
    0x1e01: 'BC5_UNORM',
    0x1e02: 'BC5_SNORM',
    0x1f01: 'BC6H_UF16',
    0x1f02: 'BC6H_SF16',
    0x2001: 'BC7_UNORM',
    0x2006: 'BC7_SRGB',
    0x2d01: 'ASTC4x4',
    0x2d06: 'ASTC4x4 SRGB',
    0x2e01: 'ASTC5x4',
    0x2e06: 'ASTC5x4 SRGB',
    0x2f01: 'ASTC5x5',
    0x2f06: 'ASTC5x5 SRGB',
    0x3001: 'ASTC6x5',
    0x3006: 'ASTC6x5 SRGB',
    0x3101: 'ASTC6x6',
    0x3106: 'ASTC6x6 SRGB',
    0x3201: 'ASTC8x5',
    0x3206: 'ASTC8x5 SRGB',
    0x3301: 'ASTC8x6',
    0x3306: 'ASTC8x6 SRGB',
    0x3401: 'ASTC8x8',
    0x3406: 'ASTC8x8 SRGB',
    0x3501: 'ASTC10x5',
    0x3506: 'ASTC10x5 SRGB',
    0x3601: 'ASTC10x6',
    0x3606: 'ASTC10x6 SRGB',
    0x3701: 'ASTC10x8',
    0x3706: 'ASTC10x8 SRGB',
    0x3801: 'ASTC10x10',
    0x3806: 'ASTC10x10 SRGB',
    0x3901: 'ASTC12x10',
    0x3906: 'ASTC12x10 SRGB',
    0x3a01: 'ASTC12x12',
    0x3a06: 'ASTC12x12 SRGB'
}

BCn_formats = [0x1a, 0x1b, 0x1c, 0x1d, 0x1e, 0x1f, 0x20]

ASTC_formats = [
    0x2d, 0x2e, 0x2f, 0x30, 0x31, 0x32, 0x33, 0x34,
    0x35, 0x36, 0x37, 0x38, 0x39, 0x3a,
]

blk_dims = {  
    0x1a: (4, 4), 0x1b: (4, 4), 0x1c: (4, 4),
    0x1d: (4, 4), 0x1e: (4, 4), 0x1f: (4, 4),
    0x20: (4, 4), 0x2d: (4, 4), 0x2e: (5, 4),
    0x2f: (5, 5), 0x30: (6, 5), 0x31: (6, 6), 
    0x32: (8, 5), 0x33: (8, 6), 0x34: (8, 8),
    0x35: (10, 5), 0x36: (10, 6), 0x37: (10, 8), 
    0x38: (10, 10), 0x39: (12, 10), 0x3a: (12, 12),
}

bpps = {  
    0x0b: 0x04, 0x07: 0x02, 0x02: 0x01, 0x09: 0x02, 0x1a: 0x08,
    0x1b: 0x10, 0x1c: 0x10, 0x1d: 0x08, 0x1e: 0x10, 0x1f: 0x10,
    0x20: 0x10, 0x2d: 0x10, 0x2e: 0x10, 0x2f: 0x10, 0x30: 0x10,
    0x31: 0x10, 0x32: 0x10, 0x33: 0x10, 0x34: 0x10, 0x35: 0x10,
    0x36: 0x10, 0x37: 0x10, 0x38: 0x10, 0x39: 0x10, 0x3a: 0x10,
}

dx10_formats = ["BC4U", "BC4S", "BC5U", "BC5S", "BC6H_UF16", "BC6H_SF16", "BC7"]

def DIV_ROUND_UP(n, d):
    return (n + d - 1) // d

def round_up(x, y):
    return ((x - 1) | (y - 1)) + 1

def getAddrBlockLinear(x, y, image_width, bytes_per_pixel, base_address, block_height):
    image_width_in_gobs = DIV_ROUND_UP(image_width * bytes_per_pixel, 64)
    GOB_address = (base_address
                   + (y // (8 * block_height)) * 512 * block_height * image_width_in_gobs
                   + (x * bytes_per_pixel // 64) * 512 * block_height
                   + (y % (8 * block_height) // 8) * 512)
    x *= bytes_per_pixel
    Address = (GOB_address + ((x % 64) // 32) * 256 + ((y % 8) // 2) * 64
               + ((x % 32) // 16) * 32 + (y % 2) * 16 + (x % 16))
    return Address

def deswizzle(width, height, blkWidth, blkHeight, bpp, tileMode, alignment, size_range, data):
    assert 0 <= size_range <= 5
    block_height = 1 << size_range

    width = DIV_ROUND_UP(width, blkWidth)
    height = DIV_ROUND_UP(height, blkHeight)

    if tileMode == 0:
        pitch = round_up(width * bpp, 32)
        surfSize = round_up(pitch * height, alignment)
    else:
        pitch = round_up(width * bpp, 64)
        surfSize = round_up(pitch * round_up(height, block_height * 8), alignment)

    result = bytearray(surfSize)

    for y in range(height):
        for x in range(width):
            if tileMode == 0: pos = y * pitch + x * bpp
            else: pos = getAddrBlockLinear(x, y, width, bpp, 0, block_height)

            pos_ = (y * width + x) * bpp

            if pos + bpp <= surfSize:
                result[pos_:pos_ + bpp] = data[pos:pos + bpp]

    return result

def bytes_to_string(data, end=0):
    if not end:
        end = data.find(b'\0')
        if end == -1: return data.decode('utf-8', 'ignore')
    return data[:end].decode('utf-8', 'ignore')

class BNTXHeader(struct.Struct):
    def __init__(self, bom):
        super().__init__(bom + '8si2Hi2xh2i')
    def data(self, data, pos):
        (self.magic, self.version, self.bom, self.revision,
         self.fileNameAddr, self.strAddr, self.relocAddr, self.fileSize) = self.unpack_from(data, pos)

class NXHeader(struct.Struct):
    def __init__(self, bom):
        super().__init__(bom + '4sI3qI')
    def data(self, data, pos):
        (self.magic, self.count, self.infoPtrAddr,
         self.dataBlkAddr, self.dictAddr, self.strDictSize) = self.unpack_from(data, pos)

class BRTIInfo(struct.Struct):
    def __init__(self, bom):
        super().__init__(bom + '4siq2b3H3I5i6I4i3q')
    def data(self, data, pos):
        (self.magic, self.size_, self.size_2, self.tileMode, self.dim,
         self.flags, self.swizzle, self.numMips, self.unk18, self.format_,
         self.unk20, self.width, self.height, self.unk2C, self.numFaces,
         self.sizeRange, self.unk38, self.unk3C, self.unk40, self.unk44,
         self.unk48, self.unk4C, self.imageSize, self.alignment, self.compSel,
         self.type_, self.nameAddr, self.parentAddr, self.ptrsAddr) = self.unpack_from(data, pos)

class TexInfo:
    pass

def generateHeader(num_mipmaps, w, h, format_, compSel, size, compressed):
    hdr = bytearray(128)
    luminance = False
    RGB = False
    has_alpha = True

    if format_ == 28:
        RGB = True
        compSels = {2: 0x000000ff, 3: 0x0000ff00, 4: 0x00ff0000, 5: 0xff000000, 1: 0}
        fmtbpp = 4
    elif format_ == 24:
        RGB = True
        compSels = {2: 0x3ff00000, 3: 0x000ffc00, 4: 0x000003ff, 5: 0xc0000000, 1: 0}
        fmtbpp = 4
    elif format_ == 85:
        RGB = True
        compSels = {2: 0x0000f800, 3: 0x000007e0, 4: 0x0000001f, 5: 0, 1: 0}
        fmtbpp = 2
        has_alpha = False
    elif format_ == 86:
        RGB = True
        compSels = {2: 0x00007c00, 3: 0x000003e0, 4: 0x0000001f, 5: 0x00008000, 1: 0}
        fmtbpp = 2
    elif format_ == 115:
        RGB = True
        compSels = {2: 0x00000f00, 3: 0x000000f0, 4: 0x0000000f, 5: 0x0000f000, 1: 0}
        fmtbpp = 2
    elif format_ == 61:
        luminance = True
        compSels = {2: 0x000000ff, 3: 0, 4: 0, 5: 0, 1: 0}
        fmtbpp = 1
        if compSel[3] != 2: has_alpha = False
    elif format_ == 49:
        luminance = True
        compSels = {2: 0x000000ff, 3: 0x0000ff00, 4: 0, 5: 0, 1: 0}
        fmtbpp = 2
    elif format_ == 112:
        luminance = True
        compSels = {2: 0x0000000f, 3: 0x000000f0, 4: 0, 5: 0, 1: 0}
        fmtbpp = 1
    else:
        return b''

    flags = 0x00000001 | 0x00001000 | 0x00000004 | 0x00000002
    caps = 0x00001000

    if num_mipmaps == 0: num_mipmaps = 1
    elif num_mipmaps != 1:
        flags |= 0x00020000
        caps |= 0x00000008 | 0x00400000

    if not compressed:
        flags |= 0x00000008
        a = False
        if compSel[0] != 2 and compSel[1] != 2 and compSel[2] != 2 and compSel[3] == 2:
            a = True
            pflags = 0x00000002
        elif luminance: pflags = 0x00020000
        elif RGB: pflags = 0x00000040
        else: return b''

        if has_alpha and not a: pflags |= 0x00000001
        size = w * fmtbpp
    else:
        flags |= 0x00080000
        pflags = 0x00000004

        if format_ == "ETC1": fourcc = b'ETC1'
        elif format_ == "BC1": fourcc = b'DXT1'
        elif format_ == "BC2": fourcc = b'DXT3'
        elif format_ == "BC3": fourcc = b'DXT5'
        elif format_ in dx10_formats: fourcc = b'DX10'
        else: fourcc = b'DXT1'

    hdr[:4] = b'DDS '
    hdr[4:8] = (124).to_bytes(4, 'little')
    hdr[8:12] = flags.to_bytes(4, 'little')
    hdr[12:16] = h.to_bytes(4, 'little')
    hdr[16:20] = w.to_bytes(4, 'little')
    hdr[20:24] = size.to_bytes(4, 'little')
    hdr[28:32] = num_mipmaps.to_bytes(4, 'little')
    hdr[76:80] = (32).to_bytes(4, 'little')
    hdr[80:84] = pflags.to_bytes(4, 'little')

    if compressed:
        hdr[84:88] = fourcc
    else:
        hdr[88:92] = (fmtbpp << 3).to_bytes(4, 'little')
        hdr[92:96] = compSels[compSel[0]].to_bytes(4, 'little')
        hdr[96:100] = compSels[compSel[1]].to_bytes(4, 'little')
        hdr[100:104] = compSels[compSel[2]].to_bytes(4, 'little')
        hdr[104:108] = compSels[compSel[3]].to_bytes(4, 'little')

    hdr[108:112] = caps.to_bytes(4, 'little')

    if format_ == "BC4U":
        hdr += bytearray(b"\x50\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00")
    elif format_ == "BC4S":
        hdr += bytearray(b"\x51\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00")
    elif format_ == "BC5U":
        hdr += bytearray(b"\x53\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00")
    elif format_ == "BC5S":
        hdr += bytearray(b"\x54\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00")
    elif format_ == "BC6H_UF16":
        hdr += bytearray(b"\x5F\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00")
    elif format_ == "BC6H_SF16":
        hdr += bytearray(b"\x60\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00")
    elif format_ == "BC7":
        hdr += bytearray(b"\x62\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00")

    return hdr

def process_bntx(bntx_data, target_name):
    pos = 0
    if bntx_data[0xc:0xe] == b'\xFF\xFE': bom = '<'
    elif bntx_data[0xc:0xe] == b'\xFE\xFF': bom = '>'
    else: return None

    header = BNTXHeader(bom)
    header.data(bntx_data, pos)
    pos += header.size

    nx = NXHeader(bom)
    nx.data(bntx_data, pos)
    pos += nx.size

    for i in range(nx.count):
        pos = nx.infoPtrAddr + i * 8
        pos = struct.unpack(bom + 'q', bntx_data[pos:pos+8])[0]

        info = BRTIInfo(bom)
        info.data(bntx_data, pos)

        nameLen = struct.unpack(bom + 'H', bntx_data[info.nameAddr:info.nameAddr + 2])[0]
        name = bytes_to_string(bntx_data[info.nameAddr + 2:info.nameAddr + 2 + nameLen], nameLen)

        if name != target_name and target_name != "*":
            continue

        compSel = []
        for i in range(4):
            value = (info.compSel >> (8 * (3 - i))) & 0xff
            if value == 0: value = len(compSel) + 2
            compSel.append(value)

        dataAddr = struct.unpack(bom + 'q', bntx_data[info.ptrsAddr:info.ptrsAddr + 8])[0]

        tex = TexInfo()
        tex.name = name
        tex.tileMode = info.tileMode
        tex.numMips = info.numMips
        tex.width = info.width
        tex.height = info.height
        tex.format = info.format_
        tex.numFaces = info.numFaces
        tex.sizeRange = info.sizeRange
        tex.compSel = compSel
        tex.alignment = info.alignment
        tex.type = info.type_
        tex.data = bntx_data[dataAddr:dataAddr+info.imageSize]

        if tex.format in formats and tex.numFaces < 2:
            if (tex.format >> 8) == 0xb: format_ = 28
            elif tex.format == 0x701: format_ = 85
            elif tex.format == 0x201: format_ = 61
            elif tex.format == 0x901: format_ = 49
            elif (tex.format >> 8) == 0x1a: format_ = "BC1"
            elif (tex.format >> 8) == 0x1b: format_ = "BC2"
            elif (tex.format >> 8) == 0x1c: format_ = "BC3"
            elif tex.format == 0x1d01: format_ = "BC4U"
            elif tex.format == 0x1d02: format_ = "BC4S"
            elif tex.format == 0x1e01: format_ = "BC5U"
            elif tex.format == 0x1e02: format_ = "BC5S"
            elif tex.format == 0x1f01: format_ = "BC6H_UF16"
            elif tex.format == 0x1f02: format_ = "BC6H_SF16"
            elif (tex.format >> 8) == 0x20: format_ = "BC7"
            else: format_ = "BC1" 

            if (tex.format >> 8) in blk_dims:
                blkWidth, blkHeight = blk_dims[tex.format >> 8]
            else:
                blkWidth, blkHeight = 1, 1

            bpp = bpps.get(tex.format >> 8, 4)
            size = DIV_ROUND_UP(tex.width, blkWidth) * DIV_ROUND_UP(tex.height, blkHeight) * bpp

            result = deswizzle(tex.width, tex.height, blkWidth, blkHeight, bpp, tex.tileMode, tex.alignment, tex.sizeRange, tex.data)
            result = result[:size]

            if (tex.format >> 8) in ASTC_formats:
                outBuffer = b''.join([
                    b'\x13\xAB\xA1\x5C', blkWidth.to_bytes(1, "little"),
                    blkHeight.to_bytes(1, "little"), b'\1',
                    tex.width.to_bytes(3, "little"),
                    tex.height.to_bytes(3, "little"), b'\1\0\0',
                    result,
                ])
                return (outBuffer, "astc")
            else:
                hdr = generateHeader(1, tex.width, tex.height, format_, list(reversed(tex.compSel)), size, (tex.format >> 8) in BCn_formats)
                return (b''.join([hdr, result]), "dds")
            
    return None