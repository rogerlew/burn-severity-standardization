from glob import glob
from os.path import exists
from os.path import join as _join
from os.path import split as _split
import json
from collections import Counter
import numpy as np

from wepppy.wepp.soils.utils import simple_texture
import oyaml

from wepppy.all_your_base.geo import read_raster
from subprocess import Popen, check_output


def simple_texture_vectorized(clay, sand):
    cs = clay + sand
    sand = np.where(cs > 100, 100 - clay, sand)
    cs = clay + sand

    textures = np.full(clay.shape, None, dtype=object)

    # Apply conditions for 'silt loam'
    mask_silt_loam = ((clay <= 27) & (cs <= 50)) | ((clay > 27) & (sand <= 20) & (cs <= 50))
    textures[mask_silt_loam] = 'silt loam'

    # Apply conditions for 'loam'
    mask_loam = ((6 <= clay) & (clay <= 27) & (50 < cs) & (cs <= 72) & (sand <= 52))
    textures[mask_loam] = 'loam'

    # Apply conditions for 'sand loam'
    mask_sand_loam = ((sand > 52) | ((cs > 50) & (clay < 6)) & (sand >= 50))
    textures[mask_sand_loam] = 'sand loam'

    # Apply conditions for 'clay loam'
    mask_clay_loam = ((cs > 72) & (sand < 50)) | ((clay > 27) & (20 < sand) & (sand <= 45)) | ((sand <= 20) & (cs > 50))
    textures[mask_clay_loam] = 'clay loam'

    return textures


if __name__ == "__main__":


    meta_fns = glob('*/meta.json')

    for meta_fn in meta_fns:
        stats = {}

        basedir, _ = _split(meta_fn)
        reveg = glob(f'{basedir}/*_reveg')
        if len(reveg) != 1:
            continue

        reveg = reveg[0]
        if exists(_join(reveg, 'stats.yaml')):
            continue

        with open(meta_fn) as fp:
            meta = json.load(fp)

        ignition_date = meta['ignition_date']
        fire_year = int(ignition_date[-4:])
        prior_year = fire_year - 1
        if prior_year > 2017:
            prior_year = 2017

        print(meta_fn, reveg, fire_year)

        sbs_fn = reveg.replace('_reveg', '')
        data, transform, proj = read_raster(sbs_fn, dtype=np.uint8)
        counts = Counter(int(x) for x in data.flatten())
        print(counts.most_common())
        stats['burn_classes'] = {}
        stats['burn_classes']['unburned'] = counts.get(0)
        stats['burn_classes']['low'] = counts.get(1)
        stats['burn_classes']['moderate'] = counts.get(2)
        stats['burn_classes']['high'] = counts.get(3)

        landuse_fn = _join(reveg, f'emapr_landcover_vote_{prior_year}.tif')
        data, transform, proj = read_raster(landuse_fn, dtype=np.uint8)
        counts = Counter(int(x) for x in data.flatten())
        stats[f'emampr_landcover_vote_{prior_year}'] = dict(counts.most_common())

        clay_fn = _join(reveg, 'statsgo_Cly.tif')
        clay, transform, proj = read_raster(landuse_fn, dtype=np.uint8)

        sand_fn = _join(reveg, 'statsgo_Snd.tif')
        sand, transform, proj = read_raster(landuse_fn, dtype=np.uint8)

        textures = simple_texture_vectorized(clay, sand)
        counts = Counter(textures.flatten())
        stats[f'soil_textures'] = dict(counts.most_common())

        print(stats)
        with open(_join(reveg, 'stats.yaml'), 'w') as fp:
            oyaml.dump(stats, fp)

#        js = check_output(f'gdalinfo -json {sbs_fn}', shell=True)
#        info = json.loads(js.decode())
#        print(info)
