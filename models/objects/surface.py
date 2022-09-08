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

class Surface:
    """ Objekt-Klasse zum Halten von Informationen zur Konstruktion in der Energy ADE """

    def __init__(self, geom, name, ifcElem, type):
        """ Konstruktor der Objekt-Klasse zum Halten von Informationen zur Konstruktion in der Energy ADE

        Args:
            geom: Die Geometrien der Oberfläche, als Liste
            name: Der Name der Oberfläche, als string
            ifcElem: Das IFC-Element der Oberfläche
            type: Typ der Oberfläche
        """
        self.geom = geom
        self.name = name
        self.ifcElem = ifcElem
        self.type = type
        self.openings = []
        self.gmlId = None
