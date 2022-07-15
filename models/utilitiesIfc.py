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
                if attrName in pset.keys():
                    return pset[attrName]
                else:
                    return None
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
                            UtilitiesIfc.findElement(ifc, obj, outElement, result, type)

            # Bei räumlichen Begrenzungen
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
                            UtilitiesIfc.findElement(ifc, obj, outElement, result, type)

            # Bei räumlichen Enthaltungen
            elif rel.is_a("IfcRelContainedInSpatialStructure"):
                if rel.RelatingStructure == inElement:
                    objs = rel.RelatedElements
                    for obj in objs:
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
                                UtilitiesIfc.findElement(ifc, obj, outElement, result, type)
        return result
