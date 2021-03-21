#!/usr/bin/env python
import re
from realtek_reglist import db
from realtek_reglist import Family, Feature, Field, Register

soc_families = {
    0x8380 : 'maple',
    0x8390 : 'cypress',
    0x9300 : 'longan',
    0x9310 : 'mango'
}

db.drop_all()
db.create_all()

for fam_id,fam_name in soc_families.items():
    print(f'{fam_name}...')
    db.session.add(Family(id=fam_id, name=fam_name))
    db.session.commit()
    features = set()

    with open(f'reglist-{fam_name}.csv') as reglist_file:
        reg_name_prog = re.compile('^INT_{}_([A-Z0-9_]+)_RTL{:04x}$'.format(
                fam_name.upper(), fam_id
        ))
        for entry in reglist_file:
            entry_fields = entry.strip().split(',')
            feature, reg_name, offset = entry_fields[0:3]
            field_numbers, port_idx_lo, port_idx_hi = entry_fields[3:6]
            array_idx_lo, array_idx_hi, portlist_idx, bit_offset = entry_fields[6:10]
            feature = feature.strip('_')
            if feature not in features:
                db.session.add(Feature(family_id=fam_id, name=feature))
                features.add(feature)
                db.session.commit()
            reg_name_match = reg_name_prog.match(reg_name)
            db.session.add(Register(family_id=fam_id, name=reg_name_match.group(1),
                    feature_id=Feature.query.filter_by(name=feature).first().id,
                    offset=int(offset, 16), port_idx_min=port_idx_lo, port_idx_max=port_idx_hi,
                        array_idx_min=array_idx_lo, array_idx_max=array_idx_hi,
                        portlist_idx=portlist_idx, bit_offset=bit_offset))
        db.session.commit()

    with open(f'regfieldlist-{fam_name}.csv') as regfieldlist_file:
        reg_name_prog = re.compile('^([A-Z0-9_]+)_RTL{:04x}$'.format(
                fam_id
        ))
        field_name_prog = re.compile('^{}_([A-Z0-9_]+)$'.format(
                fam_name.upper(), fam_id
        ))
        for entry in regfieldlist_file:
            feature, reg_name, field_name, lsb, field_len = entry.strip().split(',')
            feature = feature.strip('_')
            lsb = int(lsb)
            field_len = int(field_len.strip())
            reg_name_match = reg_name_prog.match(reg_name)
            field_name_match = field_name_prog.match(field_name)
            db.session.add(Field(
                register=Register.query.filter_by(family_id=fam_id, name=reg_name_match.group(1)).first(),
                name=field_name_match.group(1), lsb=lsb, size=field_len))
        db.session.commit()
