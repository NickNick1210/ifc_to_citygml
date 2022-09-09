# -*- coding: utf-8 -*-
"""
/***************************************************************************
@title: IFC-to-CityGML
@organization: Jade Hochschule Oldenburg
@author: Nicklas Meyer
@version: v1.0 (09.09.2022)
 ***************************************************************************/
"""


def classFactory(iface):
    """ Lädt Base-Klasse von der Datei base.

    Args:
        iface: Die QGIS-Interface-Instanz.

    Returns:
        Die instanziierte Base-Klasse
    """
    from .base import Base
    return Base(iface)
