#!/usr/bin/env python
import re
from realtek_reglist import db
from realtek_reglist import Family, Feature, Register, Table, TableField

soc_families = {
    0x8380 : 'maple',
    0x8390 : 'cypress',
    0x9300 : 'longan',
    0x9310 : 'mango',
}

table_access_regs = {
    0x8380 : [
        ('TBL_ACCESS_L2_CTRL','TBL_ACCESS_L2_DATA'),
        ('TBL_ACCESS_CTRL_0','TBL_ACCESS_DATA_0'),
        ('TBL_ACCESS_CTRL_1','TBL_ACCESS_DATA_1'),
    ],
    0x8390 : [
        ('TBL_ACCESS_L2_CTRL','TBL_ACCESS_L2_DATA'),
        ('TBL_ACCESS_CTRL_0','TBL_ACCESS_DATA_0'),
        ('TBL_ACCESS_CTRL_1','TBL_ACCESS_DATA_1'),
        ('TBL_ACCESS_CTRL_2','TBL_ACCESS_DATA_2'),
    ],
    0x9300 : [
        ('TBL_ACCESS_L2_CTRL','TBL_ACCESS_L2_DATA'),
        ('TBL_ACCESS_CTRL_0','TBL_ACCESS_DATA_0'),
        ('TBL_ACCESS_CTRL_1','TBL_ACCESS_DATA_1'),
        ('TBL_ACCESS_CTRL_2','TBL_ACCESS_DATA_2'),
        ('TBL_ACCESS_HSB_CTRL','TBL_ACCESS_HSB_DATA'),
        ('TBL_ACCESS_HSA_CTRL','TBL_ACCESS_HSA_DATA'),
    ],
    0x9310 : [
        ('TBL_ACCESS_CTRL_0','TBL_ACCESS_DATA_0'),
        ('TBL_ACCESS_CTRL_1','TBL_ACCESS_DATA_1'),
        ('TBL_ACCESS_CTRL_2','TBL_ACCESS_DATA_2'),
        ('TBL_ACCESS_CTRL_3','TBL_ACCESS_DATA_3'),
        ('TBL_ACCESS_CTRL_4','TBL_ACCESS_DATA_4'),
        ('TBL_ACCESS_CTRL_5','TBL_ACCESS_DATA_5'),
    ],
}

table_access_set = {
    0x8380 : {
        'L2_UC' : 0,
        'L2_MC' : 0,
        'L2_IP_MC_SIP' : 0,
        'L2_IP_MC' : 0,
        'L2_NEXT_HOP' : 0,
        'L2_NEXT_HOP_LEGACY' : 0,
        'L2_CAM_UC' : 0,
        'L2_CAM_MC' : 0,
        'L2_CAM_IP_MC_SIP' : 0,
        'L2_CAM_IP_MC' : 0,
        'MC_PMSK' : 0,
        'VLAN' : 1,
        'IACL' : 1,
        'LOG' : 1,
        'MSTI' : 1,
        'UNTAG' : 2,
        'VLAN_EGR_CNVT' : 2,
        'ROUTING' : 2,
    },
    0x8390 : {
        'L2_UC' : 0,
        'L2_MC' : 0,
        'L2_IP_MC_SIP' : 0,
        'L2_IP_MC' : 0,
        'L2_CAM_UC' : 0,
        'L2_CAM_MC' : 0,
        'L2_CAM_IP_MC_SIP' : 0,
        'L2_CAM_IP_MC' : 0,
        'MC_PMSK' : 0,
        'L2_NEXT_HOP' : 0,
        'L2_NH_LEGACY' : 0,
        'VLAN' : 1,
        'VLAN_IGR_CNVT' : 1,
        'VLAN_IP_SUBNET_BASED' : 1,
        'VLAN_MAC_BASED' : 1,
        'IACL' : 1,
        'EACL' : 1,
        'METER' : 1,
        'LOG' : 1,
        'MSTI' : 1,
        'UNTAG' : 2,
        'VLAN_EGR_CNVT' : 2,
        'ROUTING' : 2,
        'MPLS_LIB' : 2,
        'SCHED' : 3,
        'SPG_PORT' : 3,
        'OUT_Q' : 3,
    },
    0x9300 : {
        'L2_UC' : 0,
        'L2_MC' : 0,
        'L2_CAM_UC' : 0,
        'L2_CAM_MC' : 0,
        'MC_PORTMASK' : 0,
        'VLAN' : 1,
        'VLAN_IGR_CNVT' : 1,
        'VLAN_MAC_BASED' : 1,
        'VLAN_IP_BASED' : 1,
        'METER' : 1,
        'MSTI' : 1,
        'LOG' : 1,
        'VACL' : 1,
        'IACL' : 1,
        'PORT_ISO_CTRL' : 1,
        'LAG' : 1,
        'SRC_TRK_MAP' : 1,
        'L3_ROUTER_MAC' : 2,
        'L3_HOST_ROUTE_IPUC' : 2,
        'L3_HOST_ROUTE_IPMC' : 2,
        'L3_HOST_ROUTE_IP6UC' : 2,
        'L3_HOST_ROUTE_IP6MC' : 2,
        'L3_PREFIX_ROUTE_IPUC' : 2,
        'L3_PREFIX_ROUTE_IPMC' : 2,
        'L3_PREFIX_ROUTE_IP6UC' : 2,
        'L3_PREFIX_ROUTE_IP6MC' : 2,
        'L3_NEXTHOP' : 2,
        'L3_EGR_INTF_LIST' : 2,
        'L3_EGR_INTF' : 2,
        'UNTAG' : 3,
        'VLAN_EGR_CNVT' : 3,
        'L3_EGR_INTF_MAC' : 3,
        'REMARK' : 3,
        'HSB' : 4,
        'HSA' : 5,
    },
}


for fam_id,fam_name in soc_families.items():
    family = db.session.query(Family).where(Family.id == fam_id, Family.name == fam_name).one()

    print(f'{fam_name}...')
    features = dict()
    access_regs = dict()
    tables = dict()

    with open(f'tablelist-{fam_name}.csv') as reglist_file:
        table_name_prog = re.compile('^INT_{}_RTL{:04x}_([A-Z0-9_]+)$'.format(
                fam_name.upper(), fam_id
        ))
        for entry in reglist_file:
            entry_fields = entry.strip().split(',')
            feature_name, table_name = entry_fields[0:2]
            access_set, access_type = entry_fields[2:4]
            table_size, data_registers = entry_fields[4:6]
            feature_name = feature_name.strip('_')
            # Clean up table name
            m = table_name_prog.match(table_name)
            table_name  = m[1]

            # If access_set is '99', this means we need manual mapping
            access_set = int(access_set)
            access_type = int(access_type)
            if access_set == 99:
                access_set = table_access_set[fam_id][table_name]
            
            # Ensure feature exists and is cached
            if feature_name not in features:
                feature_name = feature_name
                feature_query = db.session.query(Feature).where(Feature.family_id==fam_id, Feature.name==feature_name)

                if feature_query.count() == 0:
                    feature = Feature(family_id=fam_id, name=feature_name)
                    db.session.add(feature)
                    db.session.commit()
                    feature = feature_query.one()
                    print(f'missing feature {feature_name}')
                else:
                    feature = feature_query.one()

                features[feature_name] = feature

            feature = features[feature_name]

            # Ensure access registers are cached
            for reg_name in table_access_regs[fam_id][access_set]:
                if reg_name not in access_regs:
                    reg = db.session.query(Register).where(Register.family_id==fam_id, Register.name==reg_name).one()
                    access_regs[reg_name] = reg

            reg_name_ctrl, reg_name_data = table_access_regs[fam_id][access_set]
            reg_ctrl = access_regs[reg_name_ctrl]
            reg_data = access_regs[reg_name_data]

            table = Table(family=family, feature=feature, name=table_name,
                access_type=access_type, size=int(table_size),
                ctrl_register=reg_ctrl, data_register=reg_data)
            db.session.add(table)
        db.session.commit()

    for t in db.session.query(Table).where(Table.family_id == fam_id).all():
        tables[t.name] = t

    with open(f'tablefieldlist-{fam_name}.csv') as tablefieldlist_file:
        table_name_prog = re.compile(f'^RTL{fam_id:04x}_([A-Z0-9_]+)$')
        for entry in tablefieldlist_file:
            feature, table_name, field_name, lsb, field_len = entry.strip().split(',')
            feature = feature.strip('_')
            lsb = int(lsb)
            field_len = int(field_len.strip())
            table_name_match = table_name_prog.match(table_name)
            table_name = table_name_match[1]
            field_name_match = re.match(f'^{fam_name.upper()}_{table_name}_([A-Z0-9_]+)$', field_name)
            tf = TableField(table=tables[table_name], name=field_name_match.group(1), lsb=lsb, size=field_len)
            db.session.add(tf)
        db.session.commit()
