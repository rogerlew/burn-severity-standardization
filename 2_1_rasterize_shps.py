import os
import sys

from os.path import join as _join
from os.path import split as _split
from os.path import exists as _exists
from glob import glob

from collections import Counter
from pprint import pprint
import shutil

import math
import numpy as np

import rasterio
from rasterio import features

from affine import Affine
import geopandas as gpd

from wepppy.all_your_base.geo import raster_stacker, GeoTransformer, read_raster

from wepppy.nodb.mods.baer.sbs_map import SoilBurnSeverityMap

from find_sbs_key import find_sbs_key

usgs_proj4 = '+proj=lcc +lat_1=29.5 +lat_2=45.5 +lat_0=23 +lon_0=-96 +x_0=0 +y_0=0 +ellps=WGS84 +units=m +no_defs'


class Logger(object):
    def __init__(self, log_fn):
        self._log_fn = log_fn
        self.terminal = sys.stdout
        self.log = open(self._log_fn, "a")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        # this flush method is needed for python 3 compatibility.
        # this handles the flush command by doing nothing.
        # you might want to specify some extra behavior here.
        pass

def isint(x):
    try:
        float(int(x)) == float(x)
        return 1
    except:
        return 0


def find_sbs_shps(top):
    shps = []
    for (root, dirs, files) in os.walk(top, topdown=True):
        for name in files:
            if name.lower().endswith('.shp') and \
                'boundary' not in name.lower() and \
                'perimeter' not in name.lower():
                shps.append(_join(root, name))
    return shps



def rasterize_sbs(shp_fn):
    global usgs_proj4

    log_fn = shp_fn + '.rasterization.log'
    sys.stdout = Logger(log_fn)

    print(f'Rasterizing {shp_fn}')

    key = find_sbs_key(shp_fn)
    if key is None:
        print('  Abort, No key found')
        return log_fn

    print(f'  key: {key}')

    geom_value = []

    c = gpd.read_file(shp_fn)
    c = c.to_crs(usgs_proj4)
    minx, miny, maxx, maxy = bounds = c.total_bounds

    cellsize = 30 # m
    width = int(math.ceil((maxx - minx) / cellsize))
    height = int(math.ceil((maxy - miny) / cellsize))
    out_shape = (height, width)
    transform = Affine.translation(minx, maxy) * Affine.scale(cellsize, -cellsize)

    print(f' out_shape: {out_shape}')
    print(f' transform: {transform}')

    print('  identifying geometeries', end='')
    for sev_desc, geom in zip(c[key], c.geometry):
        if sev_desc is None:
           continue

        elif isint(sev_desc):
            burn_severity = int(sev_desc)
        else:
            sev_desc = sev_desc.lower()

            burn_severity = 0
            if 'low' in sev_desc:
                burn_severity = 1
            elif 'mod' in sev_desc:
                burn_severity = 2
            elif 'high' in sev_desc:
                burn_severity = 3

        geom_value.append((geom, burn_severity))
        print('.', end='')
    print('done\n')

    if len(geom_value) == 0:
        print(f'  Abort, no features found in {shp_fn}')
        return log_fn

    print('  rasterizing geometeries')
    rasterized = features.rasterize(
        geom_value,
        out_shape = out_shape,
        transform = transform,
        fill = 255,
        all_touched = True,
        dtype = np.int16)
    print('done\n')

    fn = shp_fn + '.tif'
    print(f'  saving as {shp_fn}')
    with rasterio.open(
        fn, "w",
        driver = "GTiff",
        crs = c.crs,
        transform = transform,
        dtype = rasterio.uint8,
        count = 1,
        width = width,
        height = height) as dst:
        dst.write(rasterized, indexes = 1)
        dst.write_colormap(
            1, {
              0: (0, 100, 0, 255),  # unburned
              1: (127, 255, 212, 255),  # low
              2: (255, 255, 0, 255),  # moderate
              3: (255, 0, 0, 255),  # high
              255: (255, 255, 255, 0)})  # n/a
    print('done\n')

    print(f'  standardizing tif using wepppy.SoilBurnSeverityMap')
    sbs_map = SoilBurnSeverityMap(fn)
    sbs_map_fn = fn.replace('.tif', '.standardized.usgs_lcc.tif')
    sbs_map.export_4class_map(sbs_map_fn)
    print('done\n')

    data, _, _ = read_raster(sbs_map_fn)
    print('Standized Pixel Counts:', Counter(list(data.flatten())).most_common())


if __name__ == "__main__":
    sbs_dirs = glob('*/')
    sbs_dirs = [d.replace('/', '') for d in sbs_dirs]

    reprocess = 0

    for mtbs_id in sbs_dirs:

        print(f'{mtbs_id}')
        contents = os.listdir(mtbs_id)

        pprint(contents)

        sbs_shps = find_sbs_shps(mtbs_id)
        for sbs_shp in sbs_shps:
            if _exists(sbs_shp + '.standardized.tif') and not reprocess:
                print('{sbs_shp} has been rasterized. continuing.')
                continue

            print(f'rasterizing {sbs_shp}')
            rasterize_sbs(sbs_shp)

# python3 standardization2.py 2>&1 | tee standardization.log
