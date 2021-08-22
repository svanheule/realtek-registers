#!/bin/env python

import os
import sys
import re

# 3-tuples: (family_id, header_path, tag_start_offset)
sdk_headers = [
    # v4 SDK
    (0x8380, 'system/include/private/drv/nic/nic_rtl8380.h', 0),
    (0x8390, 'system/include/private/drv/nic/nic_rtl8390.h', 0),
    (0x9300, 'system/include/private/drv/nic/nic_rtl9300.h', 0),
    (0x9310, 'system/include/private/drv/nic/nic_rtl9310.h', 0),
    # v3 SDK: misses the leading u16 with frame size
    (0x8380, 'system/include/drv/nic/r8380.h', 16),
    (0x8390, 'system/include/drv/nic/r8390.h', 16),
]

pattern_bitfield = re.compile(r'uint(8|16|32)\s+(\w+)?:?(\d+)?')
pattern_cputag = re.compile(r'typedef struct (\w+)_s\s+{\s+union \{\s+' \
    r'struct \{(?P<rx>(?:\s*(?:uint.+;|/\*.+\*/))+)\s*\} .* rx;\s+' \
    r'struct \{(?P<tx>(?:\s*(?:uint.+;|/\*.+\*/))+)\s*\} .* tx;\s+\} un;\s+} (?:\1)_t;')

class Bitfield:
    def __init__(self, name, base_width, field_width):
        self.name = name or 'rsvd'
        if field_width is not None:
            self.width = int(field_width)
        else:
            self.width = int(base_width)
        self.type = f'uint{base_width}'

    def __repr__(self):
        return f'{self.type:6s} {self.name}:{self.width}'

def parse_fields(tag_fields, offset=0):
    fields = list()
    if offset > 0:
        fields.append(Bitfield(None, None, offset))
    for line in tag_fields.splitlines():
        line = line.strip()
        m = pattern_bitfield.match(line)
        if m is not None:
            bf = Bitfield(m.group(2), m.group(1), m.group(3))
            fields.append(bf)
    return fields

def total_length(fields):
    offset = 0
    for f in fields:
        offset += f.width
    return offset

class CpuTagFamily:
    def __init__(self, family, fields_rx, fields_tx):
        self.family = family
        self.rx = fields_rx
        self.tx = fields_tx

    def __repr__(self):
        return f'<CpuTagFamily({self.family:4x}, l_rx={total_length(self.rx)}, l_tx={total_length(self.tx)})>'

cputag_defs = list()

for family, header, offset in sdk_headers:
    try:
        with open(os.path.join(sys.argv[1], header), 'r') as cputag_header_file:
            cputag_header = cputag_header_file.read()
            m = pattern_cputag.search(cputag_header)
            if m is not None:
                rx = m['rx']
                tx = m['tx']
                cputag_defs.append(
                    CpuTagFamily(family, parse_fields(rx, offset), parse_fields(tx, offset))
                )
    except:
        continue

for f in cputag_defs:
    for direction,fields in {'rx' : f.rx, 'tx' : f.tx}.items():
        offset = 0
        for field in fields:
            print(f'{f.family:x},{direction},"{field.name}",{offset},{field.width}')
            offset += field.width
