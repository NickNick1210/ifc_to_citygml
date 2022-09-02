# -*- coding: utf-8 -*-
"""
/***************************************************************************
@title: IFC-to-CityGML
@organization: Jade Hochschule Oldenburg
@author: Nicklas Meyer
@version: v1.0 (02.09.2022)
 ***************************************************************************/
"""


class Mapper:
    """ Klasse zum Speichern Zuordnungen über Dictionaries """

    # Dachtyp
    roofTypeDict = {
        "BARREL_ROOF": 1100, "BUTTERFLY_ROOF": 1010, "DOME_ROOF": 1090, "FLAT_ROOF": 1000, "FREEFORM": 1130,
        "GABLE_ROOF": 1030, "GAMBREL_ROOF": 1030, "HIPPED_GABLE_ROOF": 1050, "HIP_ROOF": 1040, "MASARD_ROOF": 1060,
        "PAVILION_ROOF": 1070, "RAINBOW_ROOF": 1100, "SHED_ROOF": 1010, "USERDEFINED": 1130}

    # Gebäudeklasse
    classDict = {
        "habitation": 1000, "sanitation": 1010, "administration": 1020, "business": 1030, "trade": 1030,
        "catering": 1040, "recreation": 1050, "sport": 1060, "culture": 1070, "church": 1080, "agriculture": 1090,
        "forestry": 1090, "school": 1100, "education": 1100, "research": 1100, "maintenance": 1110, "waste": 1110,
        "healthcare": 1120, "communicating": 1130, "security": 1140, "storage": 1150, "industry": 1160, "traffic": 1170,
        "function": 1180,
        "Wohnen": 1000, "Sanitär": 1010, "Verwaltung": 1020, "Geschäft": 1030, "Gewerbe": 1030, "Gastronomie": 1040,
        "Erholung": 1050, "Sport": 1060, "Kultur": 1070, "Kirche": 1080, "Landwirtschaft": 1090,
        "Forstwirtschaft": 1090, "Schule": 1100, "Bildung": 1100, "Forschung": 1100, "Instandhaltung": 1110,
        "Abfall": 1110, "Gesundheit": 1120, "Gesundheitswesen": 1120, "Kommunikation": 1130, "Sicherheit": 1140,
        "Lagerung": 1150, "Industrie": 1160, "Verkehr": 1170, "Funktion": 1180, "Sanitaer": 1010, "Geschaeft": 1030
    }

    # Gebäudenutzung aus Gebäudeklasse
    classFunctionUsage = {
        1000: 1000, 1010: 1000, 1020: 1030, 1030: 1020, 1040: 1030, 1050: 1030, 1060: 1090, 1070: 1090, 1080: 1060,
        1090: 1070, 1100: 1050, 1110: 1050, 1120: 1030, 1130: 1030, 1140: 1030, 1150: 1030, 1160: 1030, 1170: 1030,
        1180: 1030, 1190: 1120, 1200: 1050, 1210: 1020, 1220: 1020, 1230: 1050, 1240: 1040, 1250: 1040, 1260: 1050,
        1270: 1180, 1280: 1050, 1290: 1050, 1300: 1050, 1310: 1160, 1320: 1160, 1330: 1160, 1340: 1170, 1350: 1170,
        1360: 1180, 1370: 1150, 1380: 1100, 1390: 1160, 1400: 1160, 1410: 1160, 1420: 1160, 1430: 1160, 1440: 1160,
        1450: 1160, 1460: 1100, 1470: 1170, 1480: 1170, 1490: 1170, 1500: 1170, 1510: 1770, 1520: 1770, 1530: 1770,
        1540: 1770, 1550: 1770, 1560: 1770, 1570: 1770, 1580: 1770, 1590: 1770, 1600: 1770, 1610: 1770, 1620: 1770,
        1630: 1770, 1640: 1770, 1650: 1770, 1660: 1110, 1670: 1110, 1680: 1110, 1690: 1110, 1700: 1110, 1710: 1110,
        1720: 1110, 1730: 1110, 1740: 1110, 1750: 1110, 1760: 1130, 1770: 1110, 1780: 1110, 1790: 1110, 1800: 1110,
        1810: 1110, 1820: 1110, 1830: 1010, 1840: 1110, 1850: 1110, 1860: 1090, 1870: 1090, 1880: 1090, 1890: 1090,
        1900: 1090, 1910: 1090, 1920: 1090, 1930: 1090, 1940: 1090, 1950: 1090, 1960: 1020, 1970: 1020, 1980: 1020,
        1990: 1020, 2000: 1020, 2010: 1020, 2020: 1020, 2030: 1020, 2040: 1020, 2050: 1020, 2060: 1020, 2070: 1100,
        2080: 1100, 2090: 1100, 2100: 1100, 2110: 1100, 2120: 1070, 2130: 1070, 2140: 1070, 2150: 1070, 2160: 1070,
        2170: 1070, 2180: 1070, 2190: 1070, 2200: 1070, 2210: 1070, 2220: 1080, 2230: 1070, 2240: 1070, 2250: 1070,
        2260: 1070, 2270: 1070, 2280: 1070, 2290: 1070, 2300: 1120, 2310: 1120, 2320: 1120, 2330: 1120, 2340: 1050,
        2350: 1050, 2360: 1050, 2370: 1000, 2380: 1100, 2390: 1000, 2400: 1140, 2410: 1140, 2420: 1140, 2430: 1140,
        2440: 1140, 2450: 1180, 2460: 1180, 2470: 1180, 2480: 1170, 2490: 1170, 2500: 1170, 2510: 1170, 2520: 1170,
        2530: 1170, 2540: 1170, 2550: 1060, 2560: 1060, 2570: 1060, 2580: 1060, 2590: 1050, 2600: 1050, 2610: 1050,
        2620: 1050, 2630: 1050, 2640: 1050, 2650: 1050
    }

    # Gebäudenutzung aus Gebäudefunktion
    functionUsageDict = {
        "res": 1000, "family": 1000, "townhome": 1000, "residential": 1000, "tenement": 1010, "hostel": 1020,
        "residential and administration": 1030, "residential and office": 1040, "residential and business": 1050,
        "residential and plant": 1060, "agrarian": 1070, "forestry": 1070, "residential and commercial": 1080,
        "forester's lodge": 1090, "holiday house": 1100, "summer house": 1110, "office": 1120,
        "credit institution": 1130, "bank": 1130, "insurance": 1140, "business": 1150, "store": 1160, "retail": 1170,
        "shopping": 1170, "kiosk": 1180, "pharmacy": 1190, "pavilion": 1200, "hotel": 1210, "youth hostel": 1220,
        "campsite": 1230, "restaurant": 1240, "cantine": 1250, "recreational": 1260, "recreation": 1260,
        "function": 1270, "cinema": 1280, "bowling": 1290, "casino": 1300, "industrial": 1310, "factory": 1320,
        "workshop": 1330, "petrol": 1340, "gas station": 1340, "washing": 1350, "cold store": 1360, "depot": 1370,
        "research": 1380, "quarry": 1390, "salt": 1400, "miscellaneous industrial": 1410, "mill": 1420,
        "windwill": 1430, "water mill": 1440, "bucket elevator": 1450, "weather station": 1460, "traffic assets": 1470,
        "street maintenance": 1480, "waiting": 1490, "signal control": 1500, "engine shed": 1510, "signal box": 1520,
        "air traffic": 1530, "hangar": 1540, "shipping": 1550, "shipyard": 1560, "dock": 1570, "canal": 1580,
        "boathouse": 1590, "cablecar": 1600, "car park": 1610, "parking level": 1620, "parking": 1620, "garage": 1630,
        "vehicle hall": 1640, "underground garage": 1650, "supply": 1660, "waterworks": 1670, "pump": 1680,
        "water": 1690, "power": 1700, "transformer": 1710, "converter": 1720, "reactor": 1730, "turbine": 1740,
        "boiler": 1750, "telecommunication": 1760, "gas": 1770, "heat": 1780, "pumping": 1790, "disposal": 1800,
        "effluent disposal": 1810, "filter": 1820, "toilet": 1830, "rubbish bunker": 1840, "rubbish incineration": 1850,
        "rubbish disposal": 1860, "barn": 1880, "equestrian": 1900, "alpine cabin": 1910, "hunting": 1920,
        "arboretum": 1930, "glass": 1940, "moveable glass house": 1950, "public": 1950, "administration": 1960,
        "parliament": 1970, "guildhall": 1990, "post": 2000, "customs": 2010, "court": 2020, "embassy": 2030,
        "consulate": 2030, "district administration": 2040, "district government": 2050, "tax": 2060, "education": 2070,
        "school": 2080, "vocational school": 2090, "college": 2100, "university": 2100, "research establishment": 2110,
        "cultural": 2120, "culture": 2120, "castle": 2130, "theatre": 2140, "opera": 2140, "concert": 2150,
        "museum": 2160, "broadcasting": 2170, "activity": 2180, "library": 2190, "fort": 2200, "religious": 2210,
        "church": 2220, "synagogue": 2230, "chapel": 2240, "community": 2250, "worship": 2260, "mosque": 2270,
        "temple": 2280, "convent": 2290, "health care": 2300, "hospital": 2310, "healing": 2320, "care home": 2320,
        "health": 2330, "clinic": 2330, "medical": 2330, "social": 2340, "youth": 2350, "seniors": 2360,
        "homeless": 2370, "kindergarten": 2380, "nursery": 2380, "asylum": 2390, "police": 2400, "fire": 2410,
        "barracks": 2420, "bunker": 2430, "penitentiary": 2440, "prison": 2440, "cemetery": 2450,
        "funeral parlor": 2460, "crematorium": 2470, "train station": 2480, "airport": 2490,
        "underground station": 2500, "tramway": 2510, "bus station": 2520, "shipping terminal": 2530,
        "recuperation": 2540, "sports": 2550, "sports hall": 2560, "sports field": 2570, "swimming": 2580,
        "swimming pool": 2590, "sanatorium": 2600, "zoo": 2610, "green house": 2620, "botanical": 2630, "bothy": 2640,
        "tourist": 2650, "wohnen": 1000, "wohnung": 1010, "herberge": 1020, "wohnen und verwaltung": 1030,
        "wohnen und büro": 1040, "wohnen und gewerbe": 1050, "wohnen und betrieb": 1060, "agrarwirtschaft": 1070,
        "forstwirtschaft": 1070, "wohnen und Einzelhandel": 1080, "forsthütte": 1090, "ferienhaus": 1100,
        "gartenhaus": 1110, "büro": 1120, "buero": 1120, "kreditinstitut": 1130, "versicherung": 1140, "geschäft": 1150,
        "kaufhaus": 1160, "einkaufen": 1170, "einzelhandel": 1170, "apotheke": 1190, "pavillon": 1200,
        "jugendherberge": 1220, "campingplatz": 1230, "kantine": 1250, "freizeit": 1260, "funktion": 1270, "kino": 1280,
        "kasino": 1300, "industrie": 1310, "fabrik": 1320, "werkstatt": 1330, "benzin": 1340, "tankstelle": 1340,
        "waschen": 1350, "waschanlage": 1350, "kühlhaus": 1360, "lager": 1370, "forschung": 1380, "steinbruch": 1390,
        "salz": 1400, "verschiedene industrie": 1410, "mühle": 1420, "windmühle": 1430, "wassermühle": 1440,
        "becherwerk": 1450, "wetterstation": 1460, "verkehrsanlage": 1470, "straßenmeisterei": 1480, "warten": 1490,
        "signalsteuerung": 1500, "lokschuppen": 1510, "stellwerk": 1520, "flugverkehr": 1530, "schifffahrt": 1550,
        "werft": 1560, "kanal": 1580, "bootshaus": 1590, "seilbahn": 1600, "parkhaus": 1610, "parkdeck": 1620,
        "fahrzeughalle": 1640, "tiefgarage": 1650, "versorgung": 1660, "wasserwerk": 1670, "pumpe": 1680,
        "wasser": 1690, "strom": 1700, "trafo": 1710, "transformator": 1710, "konverter": 1720, "reaktor": 1730,
        "kessel": 1750, "telekommunikation": 1760, "wärme": 1780, "pumpen": 1790, "entsorgung": 1800,
        "abwasserentsorgung": 1810, "toilette": 1830, "müllbunker": 1840, "müllverbrennung": 1850, "müllabfuhr": 1860,
        "scheune": 1880, "stall": 1890, "reitsport": 1900, "almhütte": 1910, "jagd": 1920, "glas": 1940,
        "bewegliches glashaus": 1950, "öffentlichkeit": 1950, "verwaltung": 1960, "parlament": 1970, "zunfthaus": 1990,
        "zoll": 2010, "gericht": 2020, "botschaft": 2030, "konsulat": 2030, "bezirksverwaltung": 2040,
        "bezirksregierung": 2050, "steuer": 2060, "bildung": 2070, "schule": 2080, "berufsschule": 2090,
        "hochschule": 2100, "universität": 2100, "forschungseinrichtung": 2110, "kultur": 2120, "schloss": 2130,
        "theater": 2140, "oper": 2140, "konzert": 2150, "rundfunk": 2170, "aktivität": 2180, "bibliothek": 2190,
        "festung": 2200, "religiös": 2210, "kirche": 2220, "synagoge": 2230, "kapelle": 2240, "gemeinde": 2250,
        "gottesdienst": 2260, "moschee": 2270, "tempel": 2280, "kloster": 2290, "gesundheitsvorsorge": 2300,
        "krankenhaus": 2310, "heilung": 2320, "pflegeheim": 2320, "gesundheit": 2330, "klinik": 2330, "soziales": 2340,
        "jugend": 2350, "senioren": 2360, "obdachlos": 2370, "kindertagesstätte": 2380, "asyl": 2390, "polizei": 2400,
        "feuerwehr": 2410, "kaserne": 2420, "gefängnis": 2440, "justizvollzugsanastalt": 2440, "friedhof": 2450,
        "bestattungsinstitut": 2460, "krematorium": 2470, "bahnhof": 2480, "s-bahnhof": 2480, "flughafen": 2490,
        "u-bahnhof": 2500, "straßenbahn": 2510, "busbahnhof": 2520, "schiffsterminal": 2530, "erholung": 2540,
        "sport": 2550, "sporthalle": 2560, "sportplatz": 2570, "schwimmen": 2580, "schwimmbad": 2590,
        "gewächshaus": 2620, "botanisch": 2630, "hütte": 2640, "wohnen und buero": 1040, "forsthuette": 1090,
        "kuehlhaus": 1360, "muehle": 1420, "windmuehle": 1430, "wassermuehle": 1440, "muellbunker": 1840,
        "muellverbrennung": 1850, "muellabfuhr": 1860, "almhuette": 1910, "huette": 2640, "oeffentlichkeit": 1950,
        "religioes": 2210, "geschaeft": 1150, "waerme": 1780, "universitaet": 2100, "aktivitaet": 2180,
        "kindertagesstaette": 2380, "gefaengnis": 2440, "gewaechshaus": 2620, "wohngebäude": 1000, "wohngebaeude": 1000,
        "bürogebäude": 1120, "buerogebaeude": 1120
    }

    # Gebäudetyp aus Freitext
    bldgTypeDict = {
        "Apartment": "Apartment Block", "Block": "Apartment Block", "Multi": "Multi Family House",
        "Single": "Single Family House", "Terraced": "Terraced House", "Wohnung": "Apartment Block",
        "Wohnblock": "Apartment Block", "Mehrfamilienhaus": "Multi Family House",
        "Einfamilienhaus": "Single Family House", "Wohnhaus": "Single Family House", "Reihenhaus": "Terraced House",
        "Doppelhaus": "Terraced House"
    }

    # Konstruktionswichtung aus Material
    layerCatDict = {
        "concrete": 1, "steel": 3.27, "aluminium": 1.13, "block": 1, "brick": 0.71, "stone": 1.17, "glass": 1.04,
        "gypsum": 0.96, "plastic": 0.96, "earth": 2.3
    }

    # Konstruktionsgewicht aus Materialdicke
    thicknessCatDict = {
        0.0: "veryLight", 0.1: "light", 0.25: "medium", 0.4: "heavy"
    }

    # Nutzungstyp aus Gebäudeklasse
    usageZoneTypeDict = {
        1000: "residential", 1010: "ancillary", 1020: "commerceAndServices", 1030: "commerceAndServices",
        1040: "commerceAndServices", 1050: "commerceAndServices", 1060: "commerceAndServices",
        1070: "commerceAndServices", 1080: "commerceAndServices", 1090: "agriculture", 1100: "commerceAndServices",
        1110: "commerceAndServices", 1120: "commerceAndServices", 1130: "commerceAndServices",
        1140: "commerceAndServices", 1150: "commerceAndServices", 1160: "industry", 1170: "ancillary", 1180: "ancillary"
    }
