#!/usr/bin/env bash

cm_file=$1
#echo ${cm_file}

##%GET REGION LIMITS OF CM FILE
R=$(gmt gmtinfo -I+1 -i1,2 ${cm_file})
#echo ${R}

##% CUT THE PREDICTED BATHYMETRY FOR THE CM REGION
gmt grdcut SRTM15+V2.nc ${R} -Gpredicted.nc

##% DUMP TO XYZ FOR LOADING INTO PY-CMeditor
gmt grd2xyz predicted.nc | awk '{ print $1, $2, $3 }' > predicted.xyz

##% GET THE PREDICTED VALUES AT THE CM POINTS
gmt grdtrack -i1,2,3 ${cm_file} -Gpredicted.nc | awk '{ print $1, $2, $3, $4}' > cm_predicted.xyz

##% CALCULATE DEPTH DIFFERENCE
awk '{ if ($3 > $4) print $1, $2, $4-$3; else print $1, $2, $4-$3 }' cm_predicted.xyz |\
    awk '{ print $1, $2, $3}' > difference.xyz

exit