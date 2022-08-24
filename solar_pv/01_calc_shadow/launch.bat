REM Change OSGEO4W_ROOT to point to the base install folder
SET OSGEO4W_ROOT=C:\Program Files\QGIS 3.24.3
SET QGISNAME=qgis
SET QGIS=%OSGEO4W_ROOT%\apps\%QGISNAME%
set QGIS_PREFIX_PATH=%QGIS%
REM Gdal Setup
set GDAL_DATA=%OSGEO4W_ROOT%\share\gdal\
REM Python Setup
set PATH=%OSGEO4W_ROOT%\bin;%QGIS%\bin;%PATH%;
SET PYTHONHOME=%OSGEO4W_ROOT%\apps\Python39
set PYTHONPATH=%QGIS%\python;%PYTHONPATH%


REM Launch python job
python C:\Users\lilia\Documents\GitHub\WMCA\DSSG_WMCA\solar_pv\01_calc_shadow\shading_without_DSM.py
pause
