#!/usr/bin/env python3
import argparse
import csv
import os

from realtek_reglist import app
from realtek_reglist.models import db
from realtek_reglist.models.auth import User
from realtek_reglist.models.description import DescriptionRevision
from realtek_reglist.models.soc import Family, Feature, Register, Field, Table, TableField

def model_table_name(model):
    if hasattr(model, '__tablename__'):
        return model.__tablename__
    else:
        raise ValueError('Unsupported object')

def dump_table(directory, model, query, tablename=None):
    if tablename is None:
        tablename = model_table_name(model)
    filename = f'{tablename}.csv'
    if directory is not None:
        filename = os.path.join(directory, filename)
    print(f'Dumping {filename}...')
    with open(filename, 'w') as csvfile:
        writer = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)
        for result in query.all():
            writer.writerow(result)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Dump Realtek switch SoC description database to CSV files')
    parser.add_argument('-o', '--output-directory', default='', help='Output directory for the CSV files')
    args = parser.parse_args()

    with app.app_context():
        out_dir = os.path.abspath(args.output_directory)

        if not os.path.exists(out_dir):
            os.mkdir(out_dir, 0o775)
        elif not os.path.isdir(out_dir):
            raise ValueError(f'{out_dir} is not a directory')

        dump_table(out_dir,
                User,
                db.session.query(User.username)
        )
        dump_table(out_dir,
                Family,
                db.session.query(Family.id, Family.name)
        )
        dump_table(out_dir,
                Feature,
                db.session.query(Family.name, Feature.name).join(Feature.family)
        )
        dump_table(out_dir,
                Register,
                db.session.query(Family.name, Feature.name, Register.name,
                    Register.offset, Register.port_idx_min, Register.port_idx_max,
                    Register.array_idx_min, Register.array_idx_max,
                    Register.portlist_idx, Register.bit_offset)\
                        .join(Register.family)\
                        .join(Register.feature)
        )
        dump_table(out_dir,
                Field,
                db.session.query(Family.name, Register.name, Field.name,
                        Field.lsb, Field.size)\
                        .join(Field.register)\
                        .join(Register.family)

        )
        CtrlReg = db.aliased(Register)
        DataReg = db.aliased(Register)
        dump_table(out_dir,
                Table,
                db.session.query(Family.name, Feature.name, Table.name,
                    Table.access_type, Table.size,
                    CtrlReg.name, DataReg.name)\
                        .join(Table.family)\
                        .join(Table.feature)\
                        .join(CtrlReg, Table.ctrl_register)\
                        .join(DataReg, Table.data_register)
        )
        dump_table(out_dir,
                TableField,
                db.session.query(Family.name, Table.name, TableField.name, TableField.lsb, TableField.size)\
                        .join(TableField.table)\
                        .join(Table.family)
        )
        dump_table(out_dir,
                Register,
                db.session.query(
                    Family.name, Register.name, User.username,
                    DescriptionRevision.timestamp, DescriptionRevision.value)\
                        .join(Register.family)\
                        .join(Register.description_revisions)\
                        .join(DescriptionRevision.author),
                tablename='description_register'
        )
        dump_table(out_dir,
                Field,
                db.session.query(
                    Family.name, Register.name, Field.lsb, User.username,
                    DescriptionRevision.timestamp, DescriptionRevision.value)\
                        .join(Field.register)\
                        .join(Register.family)\
                        .join(Field.description_revisions)\
                        .join(DescriptionRevision.author),
                tablename='description_registerfield'
        )
        dump_table(out_dir,
                Table,
                db.session.query(
                    Family.name, Table.name, User.username,
                    DescriptionRevision.timestamp, DescriptionRevision.value)\
                        .join(Table.family)\
                        .join(Table.description_revisions)\
                        .join(DescriptionRevision.author),
                tablename='description_table'
        )
        dump_table(out_dir,
                TableField,
                db.session.query(
                    Family.name, Table.name, TableField.lsb, User.username,
                    DescriptionRevision.timestamp, DescriptionRevision.value)\
                        .join(TableField.table)\
                        .join(Table.family)\
                        .join(TableField.description_revisions)\
                        .join(DescriptionRevision.author),
                tablename='description_tablefield'
        )
