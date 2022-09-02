# IFC-to-CityGML QGIS-Plugin

## Deutsch

### Allgemeines

Dies ist ein python-basiertes Plugin für das freie und offene Geoinformationssystem
[QGIS](https://www.qgis.org/de/site/). Es konvertiert 3D-Gebäudemodelle aus dem BIM-Format
[IFC (Industry Foundation Classes)](https://technical.buildingsmart.org/standards/ifc/ifc-schema-specifications/)
in das GIS-Format [CityGML (City Geography Markup Language)](https://www.ogc.org/standards/citygml).
Dabei ist das Level of Detail (LoD) sowie die Nutzung der
[Energy ADE (Application Domain Extension)](https://www.citygmlwiki.org/index.php/CityGML_Energy_ADE)
wählbar. Zweiteres ermöglicht die Unterstützung von thermisch-energetischen Gebäudesimulationen (SIM).

Es ist Teil einer Masterarbeit im Studiengang Geoinformationswissenschaften am Fachbereich Bauwesen
Geoinformation Gesundheitstechnologie (BGG) der
[Jade Hochschule Wilhelmshaven/Oldenburg/Elsfleth](https://www.jade-hs.de/) am Standort Oldenburg.

- Autor: Nicklas Meyer
- Kontakt: nicklas.meyer@student.jade-hs.de
- Notwendige QGIS-Version: 3.X
- Notwendige Bibliotheken: [IfcOpenShell](https://pypi.org/project/python-ifcopenshell/)
  , [SymPy](https://pypi.org/project/sympy/)

### Bedienung

Nach Start des Plugins über eine Schaltfläche in QGIS kann eine lokale IFC-Datei gewählt werden.
Diese wird im Anschluss durch das Plugin überprüft. Sollte ein kritisches Problem erkannt werden,
so wird dies mitgeteilt und es muss eine andere Datei gewählt werden. Ansonsten kann dann das
gewünschte Level of Detail (LoD), ob die Energy ADE gewünscht ist, ob eine QGIS-Integration
gewünscht ist und das Zielverzeichnis der CityGML-Datei gewählt werden. Wird die Konvertierung
anschließend gestartet, so wird diese von IFC zu CityGML unter Rücksichtnahme der getätigten
Einstellungen durchgeführt. Tritt dabei ein kritischer Fehler auf, so kann die Eingabe von vorne
anfangen. Bei erfolgreicher Konvertierung ist die CityGML im gewünschten Verzeichnis abgespeichert
und gegebenenfalls in QGIS integriert. Ist dies geschehen wird eine Meldung abgegeben und das Plugin
kann geschlossen werden. Das Plugin kann jedoch auch jederzeit geschlossen und die bisherigen
Schritte damit abgebrochen werden.

---

## English

### General

This is a Python-based plugin for the free and open geographic information system
[QGIS](https://www.qgis.org/en/site/). It converts 3D building models from the BIM format
[IFC (Industry Foundation Classes)](https://technical.buildingsmart.org/standards/ifc/ifc-schema-specifications/)
to the GIS format [CityGML (City Geography Markup Language)](https://www.ogc.org/standards/citygml).
The level of detail (LoD) and the use of the
[Energy ADE (Application Domain Extension)](https://www.citygmlwiki.org/index.php/CityGML_Energy_ADE)
can be selected. Latter enables the support of building energy simulations (BES).

It's part of a master's thesis in the GIScience course in the Civil Engineering, Geoinformation and
Health Technology department of the [Jade University of Applied Sciences
Wilhelmshaven/Oldenburg/Elsfleth](https://www.jade-hs.de/en/) in Oldenburg, Germany.

- Author: Nicklas Meyer
- Contact: <nicklas.meyer@student.jade-hs.de>
- Needed QGIS version: 3.X
- Needed libaries: [IfcOpenShell](https://pypi.org/project/python-ifcopenshell/)
  , [SymPy](https://pypi.org/project/sympy/)

### Operation

After starting the plugin via a button in QGIS, a local IFC file can be selected. This is then
checked by the plugin. If a critical problem is detected, this will be reported and another file
must be selected. Otherwise,the desired level of detail (LoD), whether the Energy ADE is desired,
whether QGIS integration is desired and the target directory of the CityGML file can be selected.
If the conversion is then started, it is carried out taking into account the settings made. If a
critical error occurs, the input can start from the beginning. If the conversion is successfule,
the CityGML file ist saved in the desired directory and, if necessary, integrated into QGIS. If
this is done, a message is issued and the plugin can be closed. However, the plugin can also be
closed at any time and the previous steps thus aborted.
