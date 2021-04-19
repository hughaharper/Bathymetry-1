#!/usr/bin/env bash

## STEP 1.0 GET INPUT cm FILE
cm_file=$1

#------------------------------------------------------------------------------
## STEP 2.0 GET REGION LIMITS OF CM FILE + 0.5 arc min
R=$(gmt gmtinfo -I0.1 -i1,2 -C ${cm_file} |\
    awk '{ print "-R"$1-0.2"/"$2+0.2"/"$3-0.2"/"$4+0.2}')
echo ${R}
#------------------------------------------------------------------------------


#------------------------------------------------------------------------------
## STEP 3.0 CUT THE OUT GRIDS FOR THE GIVEN INPUT REGION
## 3.1 CUT PREDICTED BATHYMETRY
gmt grdcut SRTM15+V2_predicted_bathy_only-bs.nc=bs ${R} -GTMP_predictions_only.nc=bs
#gmt grdimage --PS_MEDIA=A2 SRTM15+V2_predicted_bathy_only-bs.nc=bs ${R} -JM30c -Bxf5a5 -Byf5a5 -P \
#  -I+a315+nt0.9 -Ctopo > 1_TMP_SRTM15+V2_predicted_bathy_only-bs.ps

## 3.2 CUT CURRENT SRTM15+V2.1_SHIP DATA
gmt grdcut SRTM15+V2.1_ship_data_only-bs.nc=bs ${R} -GTMP_SRTM_ship_data.nc=bs

## 3.3 CUT CURRENT SRTM15+V2.1_SHIP DATA
gmt grdcut SID_MASK_V2.1-bb_NaN.nc ${R} -GTMP_SID_MASK_V2.1-bb.nc=bb
#gmt grdimage --PS_MEDIA=A2 TMP_SID_MASK_V2.1-bb.nc=bb -JM30c -Bxf5a5 -Byf5a5 -P -Cmask.cpt > 2_TMP_SID_MASK_V2.1-bb.ps

##3.4 CREATE MASK OF PREDICTED DATA
gmt grdmath TMP_SID_MASK_V2.1-bb.nc=bb ISNAN = TMP_SID_NANs_MASK-bb.nc=bb
#gmt grdimage --PS_MEDIA=A2 TMP_SID_NANs_MASK-bb.nc=bb -JM30c -Bxf5a5 -Byf5a5 -P -Cmask.cpt > 3_TMP_SID_NANs_MASK-bb.ps
#------------------------------------------------------------------------------


#------------------------------------------------------------------------------
# STEP 4.0 CONVERT THE CM FILE TO GRID AN SET FLAGGED POINTS AS NaN
awk '{ if ($5 != 9999) print $2, $3, $4; else print $2, $3, "NaN"}' ${cm_file} |\
  gmt xyz2grd ${R} -I15s/15s -rp -GTMP_input_data.nc=bs
#------------------------------------------------------------------------------


#------------------------------------------------------------------------------
# STEP 5.0 PASTE THE EDITED CM GRID FILE OVER THE CURRENT SHIP DATA
##         N.B -Co="Clobber mode" SO THE 2nd GRID VALUES WILL OVERWRITE THE 1st
gmt grdblend TMP_SRTM_ship_data.nc=bs TMP_input_data.nc=bs -Co \
  -rp -GTMP_new_ship_input_data.nc=bs

#gmt grdimage --PS_MEDIA=A2 TMP_new_ship_input_data.nc -JM30c -Bxf5a5 \
#  -Byf5a5 -P -Ctopo -I+a315+nt0.9 > 4_TMP_new_ship_input_data.ps
#------------------------------------------------------------------------------


#------------------------------------------------------------------------------
# 7.0 DO THE REMOVE INTERPOLATE RESTORE PROCEDURE

#7.1.1 GET THE DIFFERENCES BETWEEN SHIP AND PREDICTED VALUES (REMOVE)
gmt grdmath TMP_new_ship_input_data.nc=bs TMP_predictions_only.nc=bs SUB = TMP_DIFF.nc=bs
#gmt grdimage --PS_MEDIA=A2 TMP_DIFF.nc=bs -JM30c -Bxf5a5 -Byf5a5 -P -Cdiff.cpt > 5_TMP_DIFF.ps

#7.1.2 CREATE MASK OF 1=NAN 0=SHIP DATA
gmt grdmath TMP_new_ship_input_data.nc=bs ISNAN 0 NAN = TMP_SHIP_MASK.nc=bb
#gmt grdimage --PS_MEDIA=A2 TMP_SHIP_MASK.nc=bb -JM30c -Bxf5a5 -Byf5a5 -P -Cmask.cpt > 6_TMP_SHIP_MASK.ps

# 7.2 (INTERPOLATE)
# 7.2.1 INTERPOLATE THE DIFFERENCES TO SMOOTH OUT THE TRANSITION FROM PREDICTED BATHY TO REAL SOUNDINGS
gmt grdfilter TMP_DIFF.nc=bs -D2 -Fg1k -GTMP_INTERP1.nc=bs
#gmt grdimage --PS_MEDIA=A2 TMP_INTERP1.nc=bs -JM30c -Bxf5a5 -Byf5a5 -P -Cdiff.cpt > 7_TMP_INTERP1.ps

#> tmp.points gmt grdmask tmp.points -S10k -N0/0/NaN
gmt grd2xyz -bi TMP_INTERP1.nc=bs | awk '{ if ($3 != 0) print $1, $2, $3}' |
  gmt blockmedian ${R} -I15s -rp | gmt surface ${R} -I15s -rp -T0.55 -GTMP_INTERP.nc=bs

# # 7.2.2 MASK OUT THE SHIP SOUNDINGS IN THE INTERPOLATED GRID
gmt grdmath TMP_SID_NANs_MASK-bb.nc=bb TMP_INTERP.nc=bs MUL = TMP_INTERP2.nc=bs
#gmt grdimage --PS_MEDIA=A2 TMP_INTERP2.nc=bs -JM30c -Bxf5a5 -Byf5a5 -P -Cdiff.cpt > 8_TMP_INTERP2.ps

# # 7.2.3 ADD ACTUAL SHIP SOUNDING VALUES BACK INTO INTERPOLATED GRID
gmt grdmath TMP_DIFF.nc=bs 0 DENAN = TMP_DIFF_NONAN.nc=bs
gmt grdmath TMP_INTERP2.nc=bs 0 DENAN = TMP_INTERP2_NONAN.nc=bs
#gmt grdimage --PS_MEDIA=A2 TMP_INTERP2_NONAN.nc=bs -JM30c -Bxf5a5 -Byf5a5 -P -Cdiff.cpt > 9_TMP_INTERP2_NONAN.ps

gmt grdblend TMP_INTERP2_NONAN.nc=bs TMP_DIFF_NONAN.nc=bs -nc ${R} -I15s -rp -GTMP_INTERP3.nc=bs
#gmt grdimage --PS_MEDIA=A2 TMP_INTERP3.nc=bs -JM30c -Bxf5a5 -Byf5a5 -P -Cdiff.cpt > 10_TMP_INTERP3.ps

# 7.3 (RESTORE)
gmt grdmath TMP_predictions_only.nc=bs TMP_INTERP3.nc=bs ADD = TMP_RESTORED.nc=bs
#gmt grdimage --PS_MEDIA=A2 TMP_RESTORED.nc=bs -JM30c -Bxf5a5 -Byf5a5 -P \
#  -CSRTM15+v2.1.cpt -I+a315+nt0.9 > 11_TMP_RESTORED.ps
#------------------------------------------------------------------------------

gmt grdimage --MAP_FRAME_TYPE=inside TMP_RESTORED.nc=bs ${R} -JX1 -CSRTM15+v2.1.cpt -I+a315+nt0.9 -E1440 > 12_TMP_RESTORED.ps
gmt psconvert 12_TMP_RESTORED.ps -E2000 -A+u -Tt -W+g
gdal2tiles.py --zoom=8-9 --s_srs=EPSG:4326 --webviewer=leaflet --xyz 12_TMP_RESTORED.tif TMP_RESTORED

echo "FINISHED REGRDDING"

mv TMP*nc  TMP_PS
mv *.ps TMP_PS

## EXIT
exit 1