@echo off
call o4w_env
call qt5_env
call py3_env

@echo on
pyrcc5 -o C:\Users\nickl\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\ifc_to_citygml\resources.py C:\Users\nickl\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\ifc_to_citygml\resources.qrc
pause