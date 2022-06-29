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

# IFC-Bibliotheken
import ifcopenshell
from ifcopenshell import util
import ifcopenshell.util.pset

# XML-Bibliotheken
from lxml import etree
# noinspection PyUnresolvedReferences
from lxml.etree import QName


#####


class Utilities:
    """ Model-Klasse mit nützlichen Tools """

    @staticmethod
    def geomToGml(geom):
        """ Umwandeln von Geometrien in ein XML-Objekt

        Args:
            geom: Die umzuwandelnde Geometrie

        Returns:
            Das daraus erzeugte XML-Objekt
        """
        gmlGeom = geom.ExportToGML()
        gmlGeom = gmlGeom[0:gmlGeom.find(">")] + " xmlns:gml='http://www.opengis.net/gml'" + gmlGeom[gmlGeom.find(">"):]
        xml = etree.XML(gmlGeom)
        return xml

    @staticmethod
    def findPset(ifc, ifcElement, psetName):
        """ Finden eines PropertySets eines IFC-Elements

        Args:
            ifc: Das IFC-Objekt
            ifcElement: Das IFC-Element, für das das PropertySet gesucht werden soll
            psetName: Name des PropertySets, das gesucht werden soll

        Returns:
            Das gesuchte PropertySet, falls gefunden. Ansonsten None
        """
        psets = ifcopenshell.util.element.get_psets(ifcElement)
        if psetName in psets:
            return psets[psetName]
        else:
            return None

    @staticmethod
    def findElement(ifc, inElement, outElement, result=[], type=None):
        """ Rekursives Finden von IFC-Subelementen eines IFC-Elements

        Args:
            ifc: Das IFC-Objekt
            inElement: Das IFC-Element, für das die Subelemente gesucht werden sollen
            outElement: Name der IFC-Subelemente, die gesucht werden soll
            result: Feld, in dem die gefundenden Elemente gespeichert werden
                Default: []
            type: PredifinedType des IFC-Subelements, falls Eingrenzung gewünscht
                Default: None

        Returns:
            Das gesuchte PropertySet, falls gefunden. Ansonsten None
        """
        rels = ifc.get_inverse(inElement)
        for rel in rels:
            # Bei Aggregierungen
            if rel.is_a('IfcRelAggregates'):
                if rel.RelatingObject == inElement:
                    for obj in rel.RelatedObjects:
                        if obj.is_a(outElement):
                            if type is not None:
                                if obj.PredefinedType == type:
                                    if obj not in result:
                                        result.append(obj)
                            else:
                                if obj not in result:
                                    result.append(obj)
                        else:
                            Utilities.findElement(ifc, obj, outElement, result, type)

            # Bei räumlichen Zusammenhängen
            elif rel.is_a("IfcRelSpaceBoundary"):
                if rel.RelatingSpace == inElement:
                    obj = rel.RelatedBuildingElement
                    if obj is not None:
                        if obj.is_a(outElement):
                            if type is not None:
                                if obj.PredefinedType == type:
                                    if obj not in result:
                                        result.append(obj)
                            else:
                                if obj not in result:
                                    result.append(obj)
                        else:
                            Utilities.findElement(ifc, obj, outElement, result, type)
        return result
