# Burn Servity Standardization

This code attempts to standardize soil burn severity maps to a "standard" format from `burnserverity.cr.usgs.gov`


The `compiled_sbs.csv` is a table of all the standardized maps.


```
Filetype: Single Band Geotiff

Datatype: byte

Burn Classes:
 - unburned -> 0
 - low -> 1
 - moderate -> 2
 - high -> 3
 - nodata -> 255

Projection:
 +proj=lcc +lat_1=29.5 +lat_2=45.5 +lat_0=23 +lon_0=-96 +x_0=0 +y_0=0 +ellps=WGS84 +units=m +no_defs

Resolution:
 30m x 30m
```

## Scripts

### 0_download_fires.py

Downloads final burn severity zips from burnseverity.cr.usgs.gov to mtbs_id directories and creates mtbs_id/meta.json

### 1_extract_fires.py

Extracts the zips in the mtbs_id folders

### 2_1_rasterize_shps.py

Rasterizing the shape files to tifs.

Usings find_sbs_key to determine the sbs key. The find_sbs_key has blacklist functionality to skip files

### 2_2_standardize_rasters.py

Standardizes the tif SBS maps to "standard" burn codes and adds colortable to maps

### 3_compile_standardized_meta.py

builds the `compiled_sbs.csv` metadata file. This lists all the standardized sbs maps (maps ending with `.standardized.usgs_lcc.tif`)

## Github for Code

https://github.com/rogerlew/burn-severity-standardization/tree/main

## Hosted Data

https://wepp.cloud/geodata/mtbs/sbs/

