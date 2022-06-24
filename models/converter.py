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

# Standard-Bibliotheken
import os

# IFC-Bibliotheken
import ifcopenshell


class Converter():
    def __init__(self, parent, inPath, outPath):
        """Constructor."""
        self.parent = parent
        self.ifc = self.readIfc(inPath)
        self.cgml = outPath


    def readIfc(self, path):
        ifc = ifcopenshell.open(path)
        return ifc


    def run(self, lod, eade, integr):
        # TODO
        pass







