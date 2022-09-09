@ECHO OFF 

:: title: IFC-to-CityGML
:: organization: Jade Hochschule Oldenburg
:: author: Nicklas Meyer
:: version: v1.0 (02.09.2022)
:: Batch-Datei zum Ausführen von UnitTests

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

set CPL_LOG=NUL

cd /d %~dp0
cd c:/Users/nickl/AppData/Roaming/QGIS/QGIS3/profiles/default/python/plugins/ifc_to_citygml/test

python test_init.py

python objects/test_surface.py
python objects/test_construction.py
python objects/test_material.py

python models/test_transformer.py
python models/test_ifc_analyzer.py
python models/test_utilitiesIFC.py
python models/test_utilitiesGeom.py

python models/test_convert_starter.py
python models/test_converter_lod0.py
python models/test_converter_lod1.py
python models/test_converter_lod2.py
python models/test_converter_lod3.py
::python models/test_converter_lod4.py
python models/test_converter_eade.py

:: Die Klassen Base, Model, DialogVM und GisVM können nicht getestet werden, da sie eine laufende QGIS-Instanz benötigen

pause