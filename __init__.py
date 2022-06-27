# -*- coding: utf-8 -*-
"""
/***************************************************************************
@title: IFC-to-CityGML
@organization: Jade Hochschule Oldenburg
@author: Nicklas Meyer
@version: v0.1 (23.06.2022)
 ***************************************************************************/
"""


def classFactory(iface):
    """Lädt Base-Klasse von der Datei base.

    Args:
        iface: Eine QGIS-Interface-Instanz.

    Returns:
        Die instanziierte Base-Klasse
    """

    from .base import Base
    return Base(iface)
