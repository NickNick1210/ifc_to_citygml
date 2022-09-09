# -*- coding: utf-8 -*-
"""
/***************************************************************************
@title: IFC-to-CityGML
@organization: Jade Hochschule Oldenburg
@author: Nicklas Meyer
@version: v1.0 (09.09.2022)
 ***************************************************************************/
"""

#####

# IFC-Bibliotheken
from ifcopenshell.util import element

# XML-Bibliotheken
# noinspection PyUnresolvedReferences
from lxml.etree import QName


#####


class UtilitiesIfc:
    """ Model-Klasse mit nützlichen IFC-Tools """

    @staticmethod
    def findPset(ifcElement, psetName, attrName=None):
        """ Finden eines Attributs bzw. eines PropertySets eines IFC-Elements

        Args:
            ifcElement: Das IFC-Element, für das das PropertySet gesucht werden soll
            psetName: Name des PropertySets, das gesucht werden soll
            attrName: Name des Attributs im PropertySet, das gesucht werden soll, falls es gesucht werden soll
                Default: None

        Returns:
            Das gesuchte PropertySet, falls gefunden. Ansonsten None
        """
        psets = element.get_psets(ifcElement)
        # Suche nach PropertySet
        if psetName in psets:
            if attrName is None:
                return psets[psetName]

            # Suche nach Attribut
            else:
                pset = element.get_psets(ifcElement)[psetName]
                return pset[attrName] if attrName in pset.keys() else None
        else:
            return None

    @staticmethod
    def findElement(ifc, inElement, outElement, result=None, type=None):
        """ Rekursives Finden von IFC-Subelementen eines IFC-Elements

        Args:
            ifc: Das IFC-Objekt
            inElement: Das IFC-Element, für das die Subelemente gesucht werden sollen
            outElement: Name der IFC-Subelemente, die gesucht werden soll
            result: Feld, in dem die gefundenden Elemente gespeichert werden
                Default: None
            type: PredifinedType des IFC-Subelements, falls Eingrenzung gewünscht
                Default: None

        Returns:
            Die gesuchten IFC-Elemente, falls gefunden, als Liste. Ansonsten None
        """
        if result is None:
            result = []
        rels = ifc.get_inverse(inElement)
        for rel in rels:

            if rel.is_a(outElement):
                if rel not in result:
                    result.append(rel)

            # Bei Aggregierungen
            if rel.is_a('IfcRelAggregates') and rel.RelatingObject == inElement:
                objs = rel.RelatedObjects
            # Bei räumlichen Begrenzungen
            elif rel.is_a("IfcRelSpaceBoundary") and rel.RelatingSpace == inElement:
                objs = [rel.RelatedBuildingElement] if rel.RelatedBuildingElement is not None else []
            # Bei räumlichen Enthaltungen
            elif rel.is_a("IfcRelContainedInSpatialStructure") and rel.RelatingStructure == inElement:
                objs = rel.RelatedElements
            else:
                continue

            for obj in objs:
                if obj.is_a(outElement):
                    if type is not None:
                        if obj.PredefinedType == type and obj not in result:
                            result.append(obj)
                    else:
                        if obj not in result:
                            result.append(obj)
                else:
                    UtilitiesIfc.findElement(ifc, obj, outElement, result, type)

        return result
