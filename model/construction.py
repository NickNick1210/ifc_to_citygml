# -*- coding: utf-8 -*-
"""
/***************************************************************************
@title: IFC-to-CityGML
@organization: Jade Hochschule Oldenburg
@author: Nicklas Meyer
@version: v1.0 (02.09.2022)
 ***************************************************************************/
"""


#####

class Construction:
    """ Objekt-Klasse zum Halten von Informationen zur Konstruktion in der Energy ADE """

    def __init__(self, gmlId, ifcMLS, optProp, ifcElems, type):
        """ Konstruktor der Objekt-Klasse zum Halten von Informationen zur Konstruktion in der Energy ADE

        Args:
            gmlId: Die GML-ID der Konstruktion
            ifcMLS: IFC-Element des MaterialLayerSets
            optProp: Optische Eigenschaften, als Liste
            ifcElems: IFC-Elemente, die die Konstruktion nutzen, als Liste
            type: Typ der Konstruktion (Layer oder optical)
        """
        self.gmlId = gmlId
        self.ifcMLS = ifcMLS
        self.optProp = optProp
        self.ifcElems = ifcElems
        self.type = type
