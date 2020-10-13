#!/usr/bin/env bash

## 1. GET INPUT cm FILE
cm_file=$1

## 2. GET REGION LIMITS OF CM FILE + 0.5 arc min
R=$(gmt gmtinfo -I0.1 -i1,2 -C ${cm_file} |\
    awk '{ print "-R"$1-0.5"/"$2+0.5"/"$3-0.5"/"$4+0.5}')

## 3. CUT THE PREDICTED BATHYMETRY FOR THE CM REGION
gmt grdcut SRTM15+V2.1-bs.nc ${R} -Gpredicted.nc=bs

## 4. DUMP TO XYZ FOR LOADING INTO PY-CMeditor
gmt grd2xyz --IO_COL_SEPARATOR=space predicted.nc > predicted.xyz

## 5. GET THE PREDICTED VALUES AT THE CM POINTS
gmt grdtrack -i1,2,3 ${cm_file} -Gpredicted.nc | awk '{
    if ($3 > $4) print $1, $2, $4-$3; else print $1, $2, $4-$3
        }' > difference.xyz

## EXIT
exit -1