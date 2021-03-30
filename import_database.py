#!/usr/bin/env python3
import argparse
import datetime
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

def import_table(directory, tablename=None):
    if tablename is None:
        tablename = model_table_name(model)
    filename = f'{tablename}.csv'
    if directory is not None:
        filename = os.path.join(directory, filename)
    print(f'Dumping {filename}...')
    with open(filename, 'r') as csvfile:
        writer = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)
        for result in query.all():
            writer.writerow(result)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Import CSV files into Realtek switch SoC description database')
    parser.add_argument('-o', '--input-directory', default='', help='Input directory for the CSV files')
    args = parser.parse_args()

    users = dict()
    families = dict()
    features = dict()
    registers = dict()
    fields = dict()
    tables = dict()
    table_fields = dict()
    description_revisions = list()

    with app.app_context():
        in_dir = os.path.abspath(args.input_directory)

        db.create_all()

        # Import users
        with open(os.path.join(in_dir, 'user.csv')) as user_file:
            reader = csv.reader(user_file, quoting=csv.QUOTE_MINIMAL)
            for username, in reader:
                users[username] = User(username=username)

        for key,value in users.items():
            db.session.add(value)
        db.session.commit()

        # Import families
        with open(os.path.join(in_dir, 'family.csv')) as family_file:
            reader = csv.reader(family_file, quoting=csv.QUOTE_MINIMAL)
            for fam_id, fam_name in reader:
                families[fam_name] = Family(id=int(fam_id), name=fam_name)

        for key,value in families.items():
            db.session.add(value)
        db.session.commit()

        # Import features
        with open(os.path.join(in_dir, 'feature.csv')) as feature_file:
            reader = csv.reader(feature_file, quoting=csv.QUOTE_MINIMAL)
            for fam_name, feature_name in reader:
                fam = families[fam_name]
                features[(fam_name,feature_name)] = Feature(family=fam, name=feature_name)

        for key,value in features.items():
            db.session.add(value)
        db.session.commit()

        # Import registers
        with open(os.path.join(in_dir, 'register.csv')) as register_file:
            reader = csv.reader(register_file, quoting=csv.QUOTE_MINIMAL)
            for row in reader:
                fam_name, feature_name, reg_name = row[0:3]
                offset, port_min, port_max, idx_min, idx_max = row[3:8]
                portlist_idx, bit_offset = row[8:10]

                registers[(fam_name, reg_name)] = Register(
                    family=families[fam_name], feature=features[(fam_name, feature_name)],
                    name = reg_name, offset=int(offset),
                    port_idx_min=int(port_min), port_idx_max=int(port_max),
                    array_idx_min=int(idx_min), array_idx_max=int(idx_max),
                    portlist_idx=int(portlist_idx), bit_offset=int(bit_offset)
                )

        for key,value in registers.items():
            db.session.add(value)
        db.session.commit()

        with open(os.path.join(in_dir, 'field.csv')) as registerfield_file:
            reader = csv.reader(registerfield_file, quoting=csv.QUOTE_MINIMAL)
            for row in reader:
                fam_name, reg_name, field_name = row[0:3]
                lsb, size = row[3:5]
                lsb = int(lsb)
                size = int(size)

                fields[(fam_name, reg_name, lsb)] = Field(
                    register=registers[(fam_name, reg_name)],
                    name=field_name, lsb=lsb, size=size
                )

        for key,value in fields.items():
            db.session.add(value)
        db.session.commit()

        # Import tables
        with open(os.path.join(in_dir, 'table.csv')) as table_file:
            reader = csv.reader(table_file, quoting=csv.QUOTE_MINIMAL)
            for row in reader:
                fam_name, feature_name, table_name = row[0:3]
                access_type, size = row[3:5]
                ctrl_reg_name, data_reg_name = row[5:7]
                tables[(fam_name, table_name)] = Table(
                    family=families[fam_name], feature=features[(fam_name, feature_name)],
                    name=table_name, access_type=int(access_type), size=int(size),
                    ctrl_register=registers[(fam_name, ctrl_reg_name)],
                    data_register=registers[(fam_name, data_reg_name)]
                )

        for key,value in tables.items():
            db.session.add(value)
        db.session.commit()

        with open(os.path.join(in_dir, 'table_field.csv')) as tablefield_file:
            reader = csv.reader(tablefield_file, quoting=csv.QUOTE_MINIMAL)
            for fam_name, table_name, field_name, lsb, size,  in reader:
                lsb = int(lsb)
                size = int(size)
                table_fields[(fam_name, table_name, lsb)] = TableField(
                    table=tables[(fam_name, table_name)],
                    name=field_name, lsb=lsb, size=size
                )

        for key,value in table_fields.items():
            db.session.add(value)
        db.session.commit()

        # TODO description revisions
        with open(os.path.join(in_dir, 'description_register.csv')) as description_file:
            reader = csv.reader(description_file, quoting=csv.QUOTE_MINIMAL)
            for row in reader:
                fam_name, reg_name, username, timestamp, value = row
                timestamp = datetime.datetime.fromisoformat(timestamp)
                description_revisions.append(
                    DescriptionRevision(object=registers[(fam_name, reg_name)],
                        author=users[username], timestamp=timestamp, value=value)
                )
        with open(os.path.join(in_dir, 'description_registerfield.csv')) as description_file:
            reader = csv.reader(description_file, quoting=csv.QUOTE_MINIMAL)
            for row in reader:
                fam_name, reg_name, lsb, username, timestamp, value = row
                timestamp = datetime.datetime.fromisoformat(timestamp)
                description_revisions.append(
                    DescriptionRevision(object=fields[(fam_name, reg_name, int(lsb))],
                        author=users[username], timestamp=timestamp, value=value)
                )
        with open(os.path.join(in_dir, 'description_table.csv')) as description_file:
            reader = csv.reader(description_file, quoting=csv.QUOTE_MINIMAL)
            for row in reader:
                fam_name, table_name, username, timestamp, value = row
                timestamp = datetime.datetime.fromisoformat(timestamp)
                description_revisions.append(
                    DescriptionRevision(object=tables[(fam_name, table_name)],
                        author=users[username], timestamp=timestamp, value=value)
                )
        with open(os.path.join(in_dir, 'description_tablefield.csv')) as description_file:
            reader = csv.reader(description_file, quoting=csv.QUOTE_MINIMAL)
            for row in reader:
                fam_name, table_name, lsb, username, timestamp, value = row
                timestamp = datetime.datetime.fromisoformat(timestamp)
                description_revisions.append(
                    DescriptionRevision(object=tablefields[(fam_name, table_name, int(lsb))],
                        author=users[username], timestamp=timestamp, value=value)
                )


        for value in description_revisions:
            db.session.add(value)
        db.session.commit()
