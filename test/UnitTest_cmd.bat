@ECHO OFF 

set OSGEO4W_ROOT=D:\Business-Programme\QGIS\

call "%OSGEO4W_ROOT%\bin\o4w_env.bat"

path %OSGEO4W_ROOT%\apps\qgis\bin;%PATH%
set QGIS_PREFIX_PATH=%OSGEO4W_ROOT%\apps\qgis

set GDAL_FILENAME_IS_UTF8=YES

set VSI_CACHE=TRUE
set VSI_CACHE_SIZE=1000000
set QT_PLUGIN_PATH=%OSGEO4W_ROOT%\apps\qgis\qtplugins;%OSGEO4W_ROOT%\apps\qt5\plugins

set PYTHONPATH=%OSGEO4W_ROOT%\apps\qgis\python
set PYTHONHOME=%OSGEO4W_ROOT%\apps\Python39
set PYTHONPATH=%OSGEO4W_ROOT%\apps\Python39\lib\site-packages;%PYTHONPATH%

set QT_QPA_PLATFORM_PLUGIN_PATH=%OSGEO4W_ROOT%\apps\Qt5\plugins\platforms
set QGIS_PREFIX_PATH=%OSGEO4W_ROOT%\apps\qgis


cd /d %~dp0

cd c:/Users/nickl/AppData/Roaming/QGIS/QGIS3/profiles/default/python/plugins/ifc_to_citygml/test
python test_init.py

python models/test_utilitiesGeom.py
python models/test_utilitiesIFC.py

pause