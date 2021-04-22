#!/usr/bin/env bash

## 1. GET INPUT cm FILE
cm_file=$1
utm_epsg_code=$2

## 2. GET REGION LIMITS OF CM FILE + 0.5 arc min
R=$(gmt gmtinfo -I0.1 -i1,2 -C ${cm_file} |\
    awk '{ print "-R"$1-0"/"$2+0"/"$3-0"/"$4+0}')

## 3. CUT THE PREDICTED BATHYMETRY FOR THE CM REGION
gmt grdcut SRTM15+V2.1-bs.nc=bs ${R} -Gpredicted.nc=bs

## 4. DUMP TO XYZ FOR LOADING INTO PY-CMeditor
gmt grd2xyz --IO_COL_SEPARATOR=space predicted.nc > predicted.tmp

## 5. GET THE PREDICTED VALUES AT THE CM POINTS
gmt grdtrack -i1,2,3 ${cm_file} -Gpredicted.nc | awk '{
    if ($3 > $4) print $1, $2, $4-$3; else print $1, $2, $4-$3
        }' > difference.tmp

## 6. CONVERT LAT/LONG TO UTM X/Y
awk '{ print $2, $1}' predicted.tmp |\
  cs2cs EPSG:4326 EPSG:${utm_epsg_code} -f "%.2f" |\
    awk '{ print $1, $2 }' > tmp

awk '{ print $2, $1}' difference.tmp |\
  cs2cs EPSG:4326 EPSG:${utm_epsg_code} -f "%.2f" |\
    awk '{ print $1, $2 }' > tmp2

## REPLACE LONG/LAT WITH X/Y
paste tmp predicted.tmp | awk '{ print $1, $2, $5}' > predicted.xyz
paste tmp2 difference.tmp | awk '{ print $1, $2, $5}' > difference.xyz

## EXIT
exit 0