import csv
import json
import pickle
import os
import sys
import shutil
from os.path import exists as _exists
from os.path import split as _split
from os.path import join as _join
import numpy as np
from pprint import pprint

# https://github.com/rogerlew/all_your_base
from wepppy.all_your_base.geo import (
    raster_stacker, read_raster, RasterDatasetInterpolator
)
import subprocess
from glob import glob
from collections import Counter
from copy import deepcopy

products = [
            dict(src='/geodata/landfire/disturbance/*{year}*/Tif/*.tif',
                 dst='landfire_disturbance_{year}.tif',
                 start_year=1999, end_year=2020),
            dict(src='/geodata/islay.ceoas.oregonstate.edu/v1/canopy/mean/canopy_{year}_mean.tif',
                 dst='emapr_canopy_mean_{year}.tif',
                 start_year=1984, end_year=2017),
            dict(src='/geodata/islay.ceoas.oregonstate.edu/v1/landcover/vote/landcover_{year}_vote.tif',
                 dst='emapr_landcover_vote_{year}.tif',
                 start_year=1984, end_year=2017),
            dict(src='/geodata/landfire/disturbance/*{year}*/Tif/*.tif',
                 dst='landfire_disturbance_{year}.tif',
                 start_year=1999, end_year=2020),
            dict(src='/geodata/rap/v3/vegetation-cover-v3-{year}.tif',
                 dst='rap_vegetation_cover_v3_{year}.tif',
                 start_year=1986, end_year=2021),
            dict(src='/geodata/rap/biomass/v3/vegetation-biomass-v3-{year}.tif',
                 dst='rap_vegetation_biomass_v3_{year}.tif',
                 start_year=1986, end_year=2021),
            dict(src='/geodata/rap/npp/v3/vegetation-npp-v3-{year}.tif',
                 dst='rap_vegetation_npp_v3_{year}.tif',
                 start_year=1986, end_year=2021),
            dict(src='/geodata/ned1/2016/.vrt',
                 dst='dem.tif'),
            dict(src='/geodata/prism/ppt/.vrt',
                 dst='prism_monthlies_ppt.tif'),
            dict(src='/geodata/prism/tmin/.vrt',
                 dst='prism_monthlies_tmin.tif'),
            dict(src='/geodata/prism/tmax/.vrt',
                 dst='prism_monthlies_tmax.tif'),
            dict(src='/geodata/ned1/2016/topo/aspect/.vrt',
                 dst='topo_aspect.tif'),
            dict(src='/geodata/ned1/2016/topo/rough/.vrt',
                 dst='topo_rough.tif'),
            dict(src='/geodata/ned1/2016/topo/slope/.vrt',
                 dst='topo_slope.tif'),
            dict(src='/geodata/ned1/2016/topo/tpi/.vrt',
                 dst='topo_tpi.tif'),
            dict(src='/geodata/ned1/2016/topo/tri/.vrt',
                 dst='topo_tri.tif'),
            dict(src='/geodata/ssurgo/statsgo/raster/laea/90/BlkDns/.vrt',
                 dst='statsgo_BlkDns.tif'),
            dict(src='/geodata/ssurgo/statsgo/raster/laea/90/Cly/.vrt',
                 dst='statsgo_Cly.tif'),
            dict(src='/geodata/ssurgo/statsgo/raster/laea/90/DpthB/.vrt',
                 dst='statsgo_DpthB.tif'),
            dict(src='/geodata/ssurgo/statsgo/raster/laea/90/DrngCl/.vrt',
                 dst='statsgo_DrngCl.tif'),
            dict(src='/geodata/ssurgo/statsgo/raster/laea/90/FldFrq/.vrt',
                 dst='statsgo_FldFrq.tif'),
            dict(src='/geodata/ssurgo/statsgo/raster/laea/90/HydGr/.vrt',
                 dst='statsgo_HydGr.tif'),
            dict(src='/geodata/ssurgo/statsgo/raster/laea/90/Hydrc/.vrt',
                 dst='statsgo_Hydrc.tif'),
            dict(src='/geodata/ssurgo/statsgo/raster/laea/90/Ksat/.vrt',
                 dst='statsgo_Ksat.tif'),
            dict(src='/geodata/ssurgo/statsgo/raster/laea/90/OM/.vrt',
                 dst='statsgo_OM.tif'),
            dict(src='/geodata/ssurgo/statsgo/raster/laea/90/Snd/.vrt',
                 dst='statsgo_Snd.tif'),
            dict(src='/geodata/ssurgo/statsgo/raster/laea/90/SolThk/.vrt',
                 dst='statsgo_SolThk.tif'),
            dict(src='/geodata/ssurgo/statsgo/raster/laea/90/WS150/.vrt',
                 dst='statsgo_WS150.tif'),
            dict(src='/geodata/ssurgo/statsgo/raster/laea/90/WS25/.vrt',
                 dst='statsgo_WS25.tif'),
            dict(src='/geodata/ssurgo/statsgo/raster/laea/90/WTDp/.vrt',
                 dst='statsgo_WTDp.tif'),
            dict(src='/geodata/daymet/v4/prcp/daymet_v4_daily_na_prcp_{year}.nc',
                 dst='daymet_prcp_{year}.tif',
                 start_year=1980, end_year=2021),
            dict(src='/geodata/daymet/v4/dayl/daymet_v4_daily_na_dayl_{year}.nc',
                 dst='daymet_dayl_{year}.tif',
                 start_year=1980, end_year=2021),
            dict(src='/geodata/daymet/v4/srad/daymet_v4_daily_na_srad_{year}.nc',
                 dst='daymet_srad_{year}.tif',
                 start_year=1980, end_year=2021),
            dict(src='/geodata/daymet/v4/swe/daymet_v4_daily_na_swe_{year}.nc',
                 dst='daymet_swe_{year}.tif',
                 start_year=1980, end_year=2021),
            dict(src='/geodata/daymet/v4/tmax/daymet_v4_daily_na_tmax_{year}.nc',
                 dst='daymet_tmax_{year}.tif',
                 start_year=1980, end_year=2021),
            dict(src='/geodata/daymet/v4/tmin/daymet_v4_daily_na_tmin_{year}.nc',
                 dst='daymet_tmin_{year}.tif',
                 start_year=1980, end_year=2021),
            dict(src='/geodata/daymet/v4/vp/daymet_v4_daily_na_vp_{year}.nc',
                dst='daymet_vp_{year}.tif',
                 start_year=1980, end_year=2021)
          ]

def build_stack(fire_fn, outdir):
    for product in products:
        src = product['src']
        dst = product['dst']
        start_year = product.get('start_year')
        end_year = product.get('end_year')

        if not (start_year and end_year):
            start_year = end_year = 0

        for year in range(start_year, end_year+1):
            src_fn = glob(src.format(year=year))
            assert len(src_fn) == 1, (year, src, src_fn)
            src_fn = src_fn[0]

            dst_fn = _join(outdir, dst.format(year=year))
            print(src_fn, fire_fn, dst_fn)
            raster_stacker(src_fn, fire_fn, dst_fn)

if __name__ == "__main__":
    import sys
    from csv import DictReader

    target_year = None
    if not sys.argv[-1].endswith('.py'):
        target_year = sys.argv[-1]

    # use this to process specific fires
    process_targets = []

    with open('compiled_sbs.csv') as fp:
        rdr = DictReader(fp)

        for meta in rdr:

            mtbs_id = meta['fire_id'].lower()
            ignition_date = meta['ignition_date']

            if target_year:
                if target_year not in ignition_date:
                    continue

            if process_targets:
                if mtbs_id not in process_targets:
                    continue

            standardized_sbs = meta['standardized_sbs']
            outdir = standardized_sbs + "_reveg"
            if _exists(outdir):
                continue

            os.makedirs(outdir, exist_ok=True)
            print(standardized_sbs)

            build_stack(standardized_sbs, outdir)

