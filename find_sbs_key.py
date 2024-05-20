import geopandas as gpd
from glob import glob
import fiona
fiona.Env(SHAPE_RESTORE_SHX='YES')


sbs_fields = """\
SBS
Soil_BS
Soil_Burn
SoilBurnSe
Burn_Sev
soil_burn
Severity
SEVERITY
SoilBrnSev
Fire_Int
BS
BurnSev
BURNSEV
BARC
SBS_29Sept""".split()


def try_lower(x):
    try:
        return x.lower()
    except:
        return x

def isint(x):
    try:
        return float(int(x)) == float(x)
    except:
        return False

def isfloat(x):
    try:
        float(x)
        return True
    except:
        return False

def find_sbs_key(shp_fn):
    if shp_fn in blacklist:
        return None

    c = gpd.read_file(shp_fn)
    key = None
    for field in c.keys():
        if 'sbs' in field.lower():
            return field
        if 'burn' in field.lower():
            return field
        if 'severity' in field.lower():
            return field
        if 'intensity' in field.lower():
            return field
        if 'barc' in field.lower():
            return field
        if 'firecode' in field.lower():
            return field

    for field in sbs_fields:
        if field in c:
            return field

    for field in c.keys():
        if 'gridcode' in field.lower():
            return field
        if 'grid_code' in field.lower():
            return field

    for field in c.keys():
        try:
            vals = set(c[field])

        except TypeError:
            continue

        vals = set(try_lower(x) for x in vals if x is not None)
        if all(isint(x) for x in vals):
            pass
        if all(isfloat(x) for x in vals):
            pass
        else:
            if any('low' in x for x in vals) and any('high' in x for x in vals):
                return field

        if all(isint(x) for x in vals) and len(vals) > 0:
            vals = [int(x) for x in vals]
            if min(vals) >= 0 and max(vals) >= 4:
                return field

        print(field, vals)

blacklist = [
'ca4195612355120180715/NatchezFireBoundary.shp',  # fiona shx error
'ca4072012156220140731/Eiler_SBS_final/Eiler_SBS_30M_Final.shp',  #  missing projection, has img of burn severity
'ca3454311980320130527/GIS/Pourpoint_BurnSeverity/Aliso/High.shp',  # NaN bounds value
'or4408412223820180819/SoilBurnSeverity.shp', # missing projection, has tif
]

if __name__ == "__main__":
    field_map = open('shape_sbs_field_map.txt').read()

    shps = glob('*/*.shp')
    for shp in shps:
        if shp in field_map:
            continue
        if shp in blacklist:
            continue

        print(shp)
        key = find_sbs_key(shp)
        if key is not None:
            with open('shape_sbs_field_map.txt', 'a') as fp:
                fp.write(f'{shp}|{key}\n')




