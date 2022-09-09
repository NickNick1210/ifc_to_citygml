# -*- coding: utf-8 -*-
"""
/***************************************************************************
@title: IFC-to-CityGML
@organization: Jade Hochschule Oldenburg
@author: Nicklas Meyer
@version: v1.0 (09.09.2022)
 ***************************************************************************/
"""


class XmlNs:
    """ Klasse zum Speichern von XML-Namespaces """
    schemaLocation = "http://www.opengis.net/citygml/2.0 http://schemas.opengis.net/citygml/2.0/cityGMLBase.xsd  " + \
                     "http://www.opengis.net/citygml/appearance/2.0 http://schemas.opengis.net/citygml/appearance/" + \
                     "2.0/appearance.xsd http://www.opengis.net/citygml/building/2.0 http://schemas.opengis.net/" + \
                     "citygml/building/2.0/building.xsd http://www.opengis.net/citygml/generics/2.0 " + \
                     "http://schemas.opengis.net/citygml/generics/2.0/generics.xsd"
    xmlns = "http://www.opengis.net/citygml/profiles/base/2.0"
    core = "http://www.opengis.net/citygml/2.0"
    bldg = "http://www.opengis.net/citygml/building/2.0"
    gen = "http://www.opengis.net/citygml/generics/2.0"
    grp = "http://www.opengis.net/citygml/cityobjectgroup/2.0"
    app = "http://www.opengis.net/citygml/appearance/2.0"
    gml = "http://www.opengis.net/gml"
    xAL = "urn:oasis:names:tc:ciq:xsdschema:xAL:2.0"
    xlink = "http://www.w3.org/1999/xlink"
    xsi = "http://www.w3.org/2001/XMLSchema-instance"
    energy = "http://www.sig3d.org/citygml/2.0/energy/1.0"
