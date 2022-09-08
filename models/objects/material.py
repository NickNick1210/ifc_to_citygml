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

class Material:
    """ Objekt-Klasse zum Halten von Informationen zum Material in der Energy ADE """

    def __init__(self, gmlId, ifcMat):
        """ Konstruktor der Objekt-Klasse zum Halten von Informationen zum Material in der Energy ADE

        Args:
            gmlId: Die GML-ID der Konstruktion
            ifcMat: IFC-Element des Materials
        """
        self.gmlId = gmlId
        self.ifcMat = ifcMat
