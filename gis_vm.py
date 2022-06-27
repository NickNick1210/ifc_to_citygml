# -*- coding: utf-8 -*-
"""
/***************************************************************************
@title: IFC-to-CityGML
@organization: Jade Hochschule Oldenburg
@author: Nicklas Meyer
@version: v0.1 (23.06.2022)
 ***************************************************************************/
"""


class GisVM:
    """ ViewModel der GIS-View """

    def __init__(self, parent, model):
        """Constructor."""
        self.parent = parent
        self.model = model

        # TODO: QGIS-Integration
