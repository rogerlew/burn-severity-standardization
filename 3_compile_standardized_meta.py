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

if __name__ == "__main__":

    pf = open('compiled_sbs.csv', 'w')

    sbs_fns = glob('*/*usgs_lcc.tif')
    sbs_fns = [fn for fn in sbs_fns if 'dnbr' not in fn]

    for i, sbs_fn in enumerate(sbs_fns):
        print(sbs_fn)
        mtbs_id = _split(sbs_fn)[0]
        meta_fn = _join(mtbs_id, 'meta.json')

        with open(meta_fn) as fp:
            meta = json.load(fp)

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

            wtr = csv.DictWriter(pf, fieldnames=fieldnames)
            wtr.writeheader()

        meta['standardized_sbs'] = sbs_fn

        data, _, _ = read_raster(sbs_fn, dtype=np.int)
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
