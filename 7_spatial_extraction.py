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

from wepppy.all_your_base.geo import read_tif, RasterDatasetInterpolator
import subprocess
from glob import glob
from collections import Counter
from copy import deepcopy

sys.path.append('/geodata/')

from landfire.disturbance import get_landfire_disturbance_meta


lf_dist_meta = get_landfire_disturbance_meta()


def process_canopy(outdir, indices, wc='emapr_canopy_mean_{yr}.tif', 
                   start_year=1984, end_year=2017, band=1):
    res = {}
    for yr in range(start_year, end_year+1):
        res[yr] = {}
        fn = _join(outdir, wc.format(yr=yr))
        canopy, transform, proj = read_tif(fn, dtype=np.uint8, band=band)
        for k, i in indices.items():
            res[yr][k] = canopy[i]

    return res


def process_canopy_stats(canopy, fire_year, aggregators):
    res = []
    for yr in canopy:
        for k in canopy[yr]:
            series = canopy[yr][k]
            for stat, agg_func in aggregators.items():
                try:
                    value = agg_func(series)
                except:
                    value = None

                res.append(dict(year=yr, fire_year=yr-fire_year, 
                                burn_sev=k, stat=stat, value=value))
    return res

def process_disturbance(outdir, indices, start_year=1999, end_year=2020):
    global lf_dist_meta

    res = {}
    for yr in range(start_year, end_year+1):
        res[yr] = {}
        fn = _join(outdir, f'landfire_disturbance_{yr}.tif')
        disturbance, transform, proj = read_tif(fn, dtype=np.int16)
        for k, i in indices.items():
            res[yr][k] = {}
            for _k, v in Counter(disturbance[i]).most_common():
                try:
                    dist_type = lf_dist_meta[yr][int(_k)]['dist_type']
                except KeyError:
                    dist_type = 'N/A'
                res[yr][k][dist_type] = v
    return res

rap_bands = dict(annual=1, bare=2, litter=3, perennial=4, shrub=5, tree=6)
rap_npp_bands = dict(annual=1, perennial=2, shrub=3, tree=4)
rap_biomass_bands = dict(annual=1, perennial=2)

if __name__ == "__main__":
    from glob import glob

    meta_fns = glob('*/meta.json')


    skip_processed = False
    run_canopy = True
    run_rap = True
    run_rap_npp = True
    run_rap_biomass = True
    run_disturbance = True

    wd = os.getcwd()

    skip_processed = False

    for meta_fn in meta_fns:
        basedir, _ = _split(meta_fn)

        reveg = glob(f'{basedir}/*_reveg')
        if len(reveg) != 1:
            continue

        reveg = reveg[0]
        outdir = reveg

        if _exists(_join(outdir, 'disturbance.json')):
            continue


        with open(meta_fn) as fp:
            meta = json.load(fp)

        ignition_date = meta['ignition_date']
        fire_year = int(ignition_date[-4:])
        fire_fn = reveg.replace('_reveg', '')

        print(fire_fn)

        lc_year = fire_year - 1

        if fire_year > 2017:
            lc_year = 2017

        lc_fn = _join(outdir, f'emapr_landcover_vote_{lc_year}.tif') 
        if _exists(lc_fn):
            lc, _, __ = read_tif(lc_fn)
        else:
            lc = None

        dnbr, _, __ = read_tif(fire_fn)


        if run_canopy:
            indices = dict(low=np.where(dnbr==2),
                           moderate=np.where(dnbr==3),
                           high=np.where(dnbr==4))
            if lc is not None:
                indices.update(dict(low_deciduous=np.where((dnbr==2) & (lc==41)),
                           low_evergreen=np.where((dnbr==2) & (lc==42)),
                           low_mixed=np.where((dnbr==2) & (lc==43)),
                           moderate_deciduous=np.where((dnbr==3) & (lc==41)),
                           moderate_evergreen=np.where((dnbr==3) & (lc==42)),
                           moderate_mixed=np.where((dnbr==3) & (lc==43)),
                           high_deciduous=np.where((dnbr==4) & (lc==41)),
                           high_evergreen=np.where((dnbr==4) & (lc==42)),
                           high_mixed=np.where((dnbr==4) & (lc==43)),
                           low_forest=np.where((dnbr==2) & (lc>=41) & (lc<=43)),
                           mod_forest=np.where((dnbr==3) & (lc>=41) & (lc<=43)),
                           high_forest=np.where((dnbr==4) & (lc>=41) & (lc<=43)),
                           ))

            canopy = process_canopy(outdir, indices)

            with open(_join(outdir, 'canopy.pkl'), 'wb') as pf:
                pickle.dump(canopy, pf) 

            canopy_stats = process_canopy_stats(canopy, fire_year=fire_year, aggregators=dict(\
                count=len, 
                mean=np.mean, 
                median=np.median, 
                min=np.min, 
                max=np.max, 
                std=np.std))

            with open(_join(outdir, 'canopy_stats.csv'), 'w') as pf:
                wtr = csv.DictWriter(pf, fieldnames=list(canopy_stats[0].keys()))
                wtr.writeheader()
                wtr.writerows(canopy_stats)


        if run_rap:
            for k, band in rap_bands.items():
                rap = process_canopy(outdir, indices, 
                                     wc='rap_vegetation_cover_v3_{yr}.tif', 
                                     start_year=1986, end_year=2021, band=band)

                pkl = _join(outdir, f'rap_{k}.pkl')
                if _exists(pkl):
                    os.remove(pkl)
 
                with open(pkl, 'wb') as pf:
                    pickle.dump(rap, pf) 

                rap_stats = process_canopy_stats(rap, fire_year=fire_year, aggregators=dict(\
                    count=len, 
                    mean=np.mean, 
                    median=np.median, 
                    min=np.min, 
                    max=np.max, 
                    std=np.std))

                with open(_join(outdir, f'rap_{k}_stats.csv'), 'w') as pf:
                    wtr = csv.DictWriter(pf, fieldnames=list(rap_stats[0].keys()))
                    wtr.writeheader()
                    wtr.writerows(rap_stats)

        if run_rap_npp:
            for k, band in rap_npp_bands.items():
                rap = process_canopy(outdir, indices, 
                                     wc='rap_vegetation_npp_v3_{yr}.tif', 
                                     start_year=1986, end_year=2021, band=band)

                pkl = _join(outdir, f'rap_npp_{k}.pkl')
                if _exists(pkl):
                    os.remove(pkl)
 
                with open(pkl, 'wb') as pf:
                    pickle.dump(rap, pf) 

                rap_stats = process_canopy_stats(rap, fire_year=fire_year, aggregators=dict(\
                    count=len, 
                    mean=np.mean, 
                    median=np.median, 
                    min=np.min, 
                    max=np.max, 
                    std=np.std))

                with open(_join(outdir, f'rap_npp_{k}_stats.csv'), 'w') as pf:
                    wtr = csv.DictWriter(pf, fieldnames=list(rap_stats[0].keys()))
                    wtr.writeheader()
                    wtr.writerows(rap_stats)

        if run_rap_biomass:
            for k, band in rap_biomass_bands.items():
                rap = process_canopy(outdir, indices, 
                                     wc='rap_vegetation_biomass_v3_{yr}.tif', 
                                     start_year=1986, end_year=2021, band=band)

                pkl = _join(outdir, f'rap_biomass_{k}.pkl')
                if _exists(pkl):
                    os.remove(pkl)
 
                with open(pkl, 'wb') as pf:
                    pickle.dump(rap, pf) 

                rap_stats = process_canopy_stats(rap, fire_year=fire_year, aggregators=dict(\
                    count=len, 
                    mean=np.mean, 
                    median=np.median, 
                    min=np.min, 
                    max=np.max, 
                    std=np.std))

                with open(_join(outdir, f'rap_biomass_{k}_stats.csv'), 'w') as pf:
                    wtr = csv.DictWriter(pf, fieldnames=list(rap_stats[0].keys()))
                    wtr.writeheader()
                    wtr.writerows(rap_stats)

        if run_disturbance:
            dist_indices = dict(burned=np.where((dnbr >= 2) & (dnbr <= 4)))

            if lc is not None:
                dist_indices.update(dict(
                           burned_deciduous=np.where((dnbr >= 2) & (dnbr <= 4) & (lc==41)),
                           burned_evergreen=np.where((dnbr >= 2) & (dnbr <= 4) & (lc==42)),
                           burned_mixed=np.where((dnbr >= 2) & (dnbr <= 4) & (lc==43)),
                           burned_forest=np.where((dnbr>=2) & (dnbr<=4) & (lc>=41) & (lc<=43))
                           ))

            #print([ (k, len(v[0])) for k, v in dist_indices.items()])

            disturbance = process_disturbance(outdir, dist_indices)

            with open(_join(outdir, 'disturbance.json'), 'w') as pf:
                json.dump(disturbance, pf)

#            with open(_join(outdir, 'disturbance_stats.csv'), 'w') as pf:
#                pf.write('year,fire_year,disturbed\n')
#                for yr, d in disturbance.items():
#                    disturbed = (1.0 - d['burned'].get(1, 0.0)) * 100.0
#                    fy = yr - year
#                    pf.write(f'{yr},{fy},{disturbed}\n')

