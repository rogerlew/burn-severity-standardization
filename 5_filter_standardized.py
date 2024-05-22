import csv

with open('compiled_sbs.csv') as fp:
    rdr = csv.DictReader(fp)

    for row in rdr:
        if int(row['low_px']) == 1:
            print(row['fire_id'])
