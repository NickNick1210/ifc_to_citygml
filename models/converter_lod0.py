# -*- coding: utf-8 -*-
"""
/***************************************************************************
@title: IFC-to-CityGML
@organization: Jade Hochschule Oldenburg
@author: Nicklas Meyer
@version: v0.1 (23.06.2022)
 ***************************************************************************/
"""

#####

# XML-Bibliotheken
from lxml import etree
# noinspection PyUnresolvedReferences
from lxml.etree import QName

# QGIS-Bibliotheken
from qgis.PyQt.QtCore import QCoreApplication

# Geo-Bibliotheken
from osgeo import ogr

# Plugin
from .xmlns import XmlNs
from .utilitiesGeom import UtilitiesGeom
from .utilitiesIfc import UtilitiesIfc
from .converter_gen import GenConverter
from .converter_eade import EADEConverter


#####


class LoD0Converter:
    """ Model-Klasse zum Konvertieren von IFC-Dateien zu CityGML-Dateien """

    def __init__(self, parent, ifc, name, trans, eade):
        """ Konstruktor der Model-Klasse zum Konvertieren von IFC-Dateien zu CityGML-Dateien

        Args:
            parent: Die zugrunde liegende zentrale Converter-Klasse
            ifc: IFC-Datei
            name: Name des Modells
            trans: Transformer-Objekt
            eade: Ob die EnergyADE gewählt wurde als Boolean
        """

        # Initialisierung von Attributen
        self.parent = parent
        self.eade = eade
        self.ifc = ifc
        self.trans = trans
        self.geom = ogr.Geometry(ogr.wkbGeometryCollection)
        self.bldgGeom = ogr.Geometry(ogr.wkbGeometryCollection)
        self.name = name

    @staticmethod
    def tr(msg):
        """ Übersetzen

        Args:
            msg: zu übersetzender Text

        Returns:
            Übersetzter Text
        """
        return QCoreApplication.translate('LoD0Converter', msg)

    def convert(self, root):
        """ Konvertieren von IFC zu CityGML im Level of Detail (LoD) 0

        Args:
            root: Das vorbereitete XML-Schema
        """
        # IFC-Grundelemente
        ifcProject = self.ifc.by_type("IfcProject")[0]
        ifcSite = self.ifc.by_type("IfcSite")[0]
        ifcBuildings = self.ifc.by_type("IfcBuilding")

        # XML-Struktur
        chName = etree.SubElement(root, QName(XmlNs.gml, "name"))
        chName.text = self.name
        chBound = etree.SubElement(root, QName(XmlNs.gml, "boundedBy"))

        # Über alle enthaltenen Gebäude iterieren
        for ifcBuilding in ifcBuildings:
            chCOM = etree.SubElement(root, QName(XmlNs.core, "cityObjectMember"))
            chBldg = etree.SubElement(chCOM, QName(XmlNs.bldg, "Building"))

            # Konvertierung
            self.parent.dlg.log(self.tr(u'Building attributes are extracted'))
            GenConverter.convertBldgAttr(self.ifc, ifcBuilding, chBldg)
            self.parent.dlg.log(self.tr(u'Building footprint is calculated'))
            footPrint = self.convertFootPrint(ifcBuilding, chBldg)
            self.parent.dlg.log(self.tr(u'Building roofedge is calculated'))
            self.convertRoofEdge(ifcBuilding, chBldg)
            self.parent.dlg.log(self.tr(u'Building address is extracted'))
            addressSuccess = GenConverter.convertAddress(ifcBuilding, ifcSite, chBldg)
            if not addressSuccess:
                self.parent.dlg.log(self.tr(u'No address details existing'))
            self.parent.dlg.log(self.tr(u'Building bound is calculated'))
            bbox = GenConverter.convertBound(self.geom, chBound, self.trans)

            # EnergyADE
            if self.eade:
                self.parent.dlg.log(self.tr(u'Energy ADE: weather data is extracted'))
                EADEConverter.convertWeatherData(ifcProject, ifcSite, chBldg, bbox)
                self.parent.dlg.log(self.tr(u'Energy ADE: building attributes are extracted'))
                EADEConverter.convertEadeBldgAttr(self.ifc, ifcBuilding, chBldg, bbox, footPrint)

        return root

    def convertFootPrint(self, ifcBuilding, chBldg):
        """ Konvertieren der Grundfläche von IFC zu CityGML

        Args:
            ifcBuilding: Das Gebäude, aus dem die Grundfläche entnommen werden soll
            chBldg: XML-Element an dem die Grundfläche angefügt werden soll
        """
        # IFC-Elemente
        ifcSlabs = UtilitiesIfc.findElement(self.ifc, ifcBuilding, "IfcSlab", result=[], type="BASESLAB")
        if len(ifcSlabs) == 0:
            ifcSlabs = UtilitiesIfc.findElement(self.ifc, ifcBuilding, "IfcSlab", result=[], type="FLOOR")
            # Wenn keine Grundfläche vorhanden
            if len(ifcSlabs) == 0:
                self.parent.dlg.log(self.tr(u"Due to the missing baseslab, no FootPrint geometry can be calculated"))
                return

        # Geometrie
        geometry = GenConverter.calcPlane(ifcSlabs, self.trans)[1]
        if geometry is not None:
            self.geom.AddGeometry(geometry)
            self.bldgGeom.AddGeometry(geometry)
            geomXML = UtilitiesGeom.geomToGml(geometry)
            if geomXML is not None:
                # XML-Struktur
                chBldgFootPrint = etree.SubElement(chBldg, QName(XmlNs.bldg, "lod0FootPrint"))
                chBldgFootPrintMS = etree.SubElement(chBldgFootPrint, QName(XmlNs.gml, "MultiSurface"))
                chBldgFootPrintSM = etree.SubElement(chBldgFootPrintMS, QName(XmlNs.gml, "surfaceMember"))
                chBldgFootPrintSM.append(geomXML)
        return geometry

    def convertRoofEdge(self, ifcBuilding, chBldg):
        """ Konvertieren der Dachkantenfläche von IFC zu CityGML

        Args:
            ifcBuilding: Das Gebäude, aus dem die Dachkantenfläche entnommen werden soll
            chBldg: XML-Element an dem die Dachkantenfläche angefügt werden soll
        """

        # IFC-Elemente
        ifcRoofs = UtilitiesIfc.findElement(self.ifc, ifcBuilding, "IfcSlab", result=[], type="ROOF")
        if len(ifcRoofs) == 0:
            ifcRoofs = UtilitiesIfc.findElement(self.ifc, ifcBuilding, "IfcRoof", result=[])
            # Wenn kein Dach vorhanden
            if len(ifcRoofs) == 0:
                self.parent.dlg.log(self.tr(u"Due to the missing roof, no RoofEdge geometry can be calculated"))
                return

        # Geometrie
        geometry = GenConverter.calcPlane(ifcRoofs, self.trans)[1]
        self.geom.AddGeometry(geometry)
        self.bldgGeom.AddGeometry(geometry)
        geomXML = UtilitiesGeom.geomToGml(geometry)
        if geomXML is not None:
            # XML-Struktur
            chBldgRoofEdge = etree.SubElement(chBldg, QName(XmlNs.bldg, "lod0RoofEdge"))
            chBldgRoofEdgeMS = etree.SubElement(chBldgRoofEdge, QName(XmlNs.gml, "MultiSurface"))
            chBldgRoofEdgeSM = etree.SubElement(chBldgRoofEdgeMS, QName(XmlNs.gml, "surfaceMember"))
            chBldgRoofEdgeSM.append(geomXML)
