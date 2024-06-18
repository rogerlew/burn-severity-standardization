import json
import csv
from glob import glob
from os.path import split as _split
from os.path import join as _join

from collections import Counter

import na_l3_ecoregions

import numpy as np

from wepppy.all_your_base.geo import RasterDatasetInterpolator
from wepppy.all_your_base.geo import read_raster
from wepppy.nodb.mods.baer.sbs_map import SoilBurnSeverityMap


import requests
import re

def get_baer_db_search_url(ignition_date):
    month, day, year = ignition_date.split('/')
    formatted_date = f"{year}-{month}-{day}"
    baer_db_search_url = f"https://forest.moscowfsl.wsu.edu/cgi-bin/BAERTOOLS/baer-db/index.pl?start_date={formatted_date}&end_date={formatted_date}&exp=0&"
    return baer_db_search_url

def do_baer_query(ignition_date):
    url = get_baer_db_search_url(ignition_date)
    response = requests.get(url)
    response_text = response.text

    match = re.search(r"Found (\d+) BAER reports with this search:", response_text)
    if match:
        return int(match.group(1))
    else:
        return -1


with open('us_abbreviations.csv') as fp:
    rdr = csv.DictReader(fp)
    us_abbreviations = {row['postal'].lower(): row['full'] for row in rdr}

if __name__ == "__main__":

    pf = open('compiled_sbs2.csv', 'w')

    sbs_fns = glob('*/*usgs_lcc.tif')
    sbs_fns = [fn for fn in sbs_fns if 'dnbr' not in fn]

    for i, sbs_fn in enumerate(sbs_fns):
        print(sbs_fn)
        mtbs_id = _split(sbs_fn)[0]
        meta_fn = _join(mtbs_id, 'meta.json')

        with open(meta_fn) as fp:
            meta = json.load(fp)

        meta['fire_id'] = meta['fire_id'].lower()

        if 'field_state' in meta:
            if meta['field_state'].strip().lower() in us_abbreviations:
                meta['field_state'] = us_abbreviations[meta['field_state'].strip().lower()]

        if i == 0:
            fieldnames = list(meta.keys())
            fieldnames.append('standardized_sbs')
            fieldnames.append('unburned_px')
            fieldnames.append('low_px')
            fieldnames.append('moderate_px')
            fieldnames.append('high_px')
            fieldnames.append('nodata_px')
            fieldnames.append('centroid_lng')
            fieldnames.append('centroid_lat')
            fieldnames.append('l3_ecoregion')
            fieldnames.append('baer_db_url')

            wtr = csv.DictWriter(pf, fieldnames=fieldnames)
            wtr.writeheader()

        ignition_date = meta['ignition_date']
        baer_db_url = ''
        if do_baer_query(ignition_date) > 0:
            baer_db_url = get_baer_db_search_url(ignition_date)
        meta['baer_db_url'] = baer_db_url

        meta['standardized_sbs'] = sbs_fn

        data, _, _ = read_raster(sbs_fn, dtype=np.int32)
        px = dict(Counter(list(data.flatten())).most_common())
        meta['unburned_px'] = px.get(0, 0)
        meta['low_px'] = px.get(1, 1)
        meta['moderate_px'] = px.get(2, 2)
        meta['high_px'] = px.get(3, 3)
        meta['nodata_px'] = px.get(255, 255)

        rdi = RasterDatasetInterpolator(sbs_fn)
        wgs_lng, wgs_lat = rdi.gt0_centroid
        l3code = na_l3_ecoregions.l3code(wgs_lng, wgs_lat)

        meta['centroid_lng'] = wgs_lng
        meta['centroid_lat'] = wgs_lat
        meta['l3_ecoregion'] = l3code

        wtr.writerow(meta)
    pf.close()
