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

class IfcAnalyzer():
    def __init__(self, parent, path):
        """Constructor."""
        self.parent = parent
        ifc = self.readIFC(path)
        self.analyzeIFC(ifc)

    def readIFC(self, path):
        ifc = ifcopenshell.open(path)
        return ifc

    def analyzeIFC(self, ifc):
        self.parent.dlg.log("Schema: " + ifc.schema)
        self.parent.dlg.log("Schema: " + ifc.schema)
        self.parent.dlg.log("Schema: " + ifc.schema)
        self.parent.dlg.log("Schema: " + ifc.schema)





