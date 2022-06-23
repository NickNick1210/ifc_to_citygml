# -*- coding: utf-8 -*-
"""
/***************************************************************************
@title: IFC-to-CityGML
@organization: Jade Hochschule Oldenburg
@author: Nicklas Meyer
@version: v0.1 (23.06.2022)
 ***************************************************************************/
"""

""" Dieses Skript initialisiert das Plugin und meldet es in QGIS an. """

# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Lädt Base-Klasse von der Datei base.

    Args:
        iface: Eine QGIS-Interface-Instanz.

    Returns:
        Die instanziierte Base-Klasse
    """

    from .base import Base
    return Base(iface)
