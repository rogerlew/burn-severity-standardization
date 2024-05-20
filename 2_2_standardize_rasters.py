import os
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
from rasterio.warp import calculate_default_transform, reproject, Resampling

from affine import Affine
import geopandas as gpd

from wepppy.all_your_base.geo import raster_stacker, GeoTransformer, read_raster

from wepppy.nodb.mods.baer.sbs_map import SoilBurnSeverityMap

from find_sbs_key import find_sbs_key

usgs_proj4 = '+proj=lcc +lat_1=29.5 +lat_2=45.5 +lat_0=23 +lon_0=-96 +x_0=0 +y_0=0 +ellps=WGS84 +units=m +no_defs'


def transform_to_usgs_lcc(raster_fn, resolution=30):
    global usgs_proj4
    dst_fn = raster_fn.replace('.tif', '.usgs_lcc.tif')

    with rasterio.open(raster_fn) as src:

        src_crs = src.crs
        if src_crs is None:
            print(f'Abort, {raster_fn} does not have projection.')
            return None

        transform, width, height = calculate_default_transform(
            src_crs, usgs_proj4, src.width, src.height, *src.bounds)

        if not src_crs.is_geographic:
            transform = Affine.translation(transform.c, transform.f) * Affine.scale(resolution, -resolution)
            width = int((src.bounds.right - src.bounds.left) / resolution)
            height = int((src.bounds.top - src.bounds.bottom) / resolution)

        dst_meta = src.meta.copy()
        dst_meta.update({
            'crs': usgs_proj4,
            'transform': transform,
            'width': width,
            'height': height
        })

        with rasterio.open(dst_fn, 'w', **dst_meta) as dst:
            for i in range(1, src.count + 1):
                reproject(
                    source=rasterio.band(src, i),
                    destination=rasterio.band(dst, i),
                    src_transform=src.transform,
                    src_crs=src_crs,
                    dst_transform=transform,
                    dst_crs=usgs_proj4,
                    resampling=Resampling.nearest
                )


            # Copy color table if it exists
            if 'colormap' in src.meta:
                for i in range(1, src.count + 1):
                    dst.write_colormap(i, src.colormap(i))


    return dst_fn


def isint(x):
    try:
        float(int(x)) == float(x)
        return 1
    except:
        return 0


if __name__ == "__main__":
    sbs_dirs = glob('*/')
    sbs_dirs = [d.replace('/', '') for d in sbs_dirs]

    reprocess = 0

    for mtbs_id in ['or4251612403720230716',]: #sbs_dirs:

        print(f'{mtbs_id}')
        contents = os.listdir(mtbs_id)

        if len(glob(f'{mtbs_id}/*.standardized.usgs_lcc.tif')) > 0 and not reprocess:
            print('  has already been processed. continuing.')
            continue

        pprint(contents)

        nbr_fns = glob(f'/geodata/mtbs/dnbr6/*/*{mtbs_id}*nbr*.tif')
        if len(nbr_fns) > 0:
            print(f'found nbr files: {nbr_fns}')
            for fn in nbr_fns:
                shutil.copy(fn, mtbs_id)
                transform_to_usgs_lcc(_join(mtbs_id, _split(fn)[1]))

        if len(contents) == 1:
            print('no sbs download link available for {mtbs_id}')
            continue

        tif_files = glob(_join(mtbs_id, '**', '*.tif'), recursive=True)
        img_files = glob(_join(mtbs_id, '**', '*.img'), recursive=True)

        for sbs_fn in tif_files + img_files:
            name = _split(sbs_fn)[1]
            if '.standardized.' in name:
                continue

            if '.shp.' in name:
                continue

            if not (
                'final' in name.lower() or
                'burn' in name.lower() or
                'sbs' in name.lower() or
                'severity' in name.lower()
            ):
                continue

            sbs_map = SoilBurnSeverityMap(sbs_fn)
            sbs_map_fn = sbs_fn.replace('.tif', '.standardized.tif').replace('.img', '.img.standardized.tif')

            print(f'  standardizing to {sbs_map_fn}')
            sbs_map.export_4class_map(sbs_map_fn)

            print(f'  reprojecting {sbs_map_fn}')
            sbs_reproj_fn = transform_to_usgs_lcc(sbs_map_fn)
            if sbs_reproj_fn is not None:
                data, _, _ = read_raster(sbs_reproj_fn)
                print('    exported counts', Counter(list(data.flatten())).most_common())


# python3 standardization2.py 2>&1 | tee standardization.log
