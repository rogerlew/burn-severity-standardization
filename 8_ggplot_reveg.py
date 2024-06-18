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

import pandas as pd
from plotnine import ggplot, aes, geom_point, geom_line, labs, geom_vline, facet_wrap, theme, element_text


def plot_evergreen_cover(canopy_fn, fire_name, fire_id, fire_year):
    
        df = pd.read_csv(canopy_fn)
        filtered_df = df[(df['burn_sev'].isin(['low_evergreen', 'moderate_evergreen', 'high_evergreen'])) & (df['stat'] == 'median')]
        
        # Creating the plot
        p = (ggplot(filtered_df, aes(x='fire_year', y='value', color='burn_sev')) +
            geom_vline(aes(xintercept=0), color="red") +
            geom_point() +
            labs(title=f'{fire_name} {fire_year} ({fire_id})',
                x='Fire Year',
                y='Cover (%)',
                color='Burn Severity') +
            theme(strip_text=element_text(size=15, face="bold"))
            )
        
        # Save the plot
        p.save(filename=canopy_fn[:-4] + '_evergreen.png', width=10, height=6, units='in', dpi=300)


if __name__ == "__main__":

    meta_fns = glob('*/meta.json')

    for meta_fn in meta_fns:
        stats = {}

        basedir, _ = _split(meta_fn)
        reveg = glob(f'{basedir}/*_reveg')
        if len(reveg) != 1:
            continue

        reveg = reveg[0]
        
        with open(meta_fn) as fp:
            meta = json.load(fp)

        print(reveg)

        ignition_date = meta['ignition_date']
        fire_name = meta['fire_name']
        fire_id = meta['fire_id']
        fire_year = int(ignition_date[-4:])

        canopy_stats_fn = _join(reveg, 'canopy_stats.csv')
        plot_evergreen_cover(canopy_stats_fn, fire_name, fire_id, fire_year)

        rap_stats_fn = _join(reveg, 'rap_tree_stats.csv')
        plot_evergreen_cover(rap_stats_fn, fire_name, fire_id, fire_year)

        