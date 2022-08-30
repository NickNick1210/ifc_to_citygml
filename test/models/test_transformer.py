# coding=utf-8
"""
/***************************************************************************
@title: IFC-to-CityGML
@organization: Jade Hochschule Oldenburg
@author: Nicklas Meyer
@version: v0.2 (26.08.2022)

Unit-Test für die Modelklasse Transformer
 ***************************************************************************/
"""

# Standard-Bibliotheken
import unittest
import logging
import sys
import numpy as np

# IFC-Bibliotheken
import ifcopenshell

# Plugin
sys.path.insert(0, '..')
from models.transformer import Transformer

#####

LOGGER = logging.getLogger('QGIS')

# IFC-Elemente
dataPath = r"data/IFC_test.ifc"
ifc = ifcopenshell.open(dataPath)
dataPath2 = r"data/IFC_test2.ifc"
ifc2 = ifcopenshell.open(dataPath2)


class TestConstructor(unittest.TestCase):

    def test_1(self):
        result = Transformer(ifc)
        self.assertEqual(ifc, result.ifc)
        corr = 32632
        self.assertEqual(corr, result.epsg)
        corr = [458870.0632856814, 5438773.629049492, 110.0]
        self.assertEqual(corr, result.originShift)
        corr = [[0.64278761, 0.76604444, 0], [-0.76604444, 0.64278761, 0], [0, 0, 1]]
        np.testing.assert_array_almost_equal(corr, result.trans)

    def test_2(self):
        result = Transformer(ifc2)
        self.assertEqual(ifc2, result.ifc)
        corr = 32633
        self.assertEqual(corr, result.epsg)
        corr = [509733.27041584934, 6096718.499613839, 210.0]
        self.assertEqual(corr, result.originShift)
        corr = [[0.996923, 0.124615, 0], [-0.124615, 0.996923, 0], [0, 0, 1]]
        np.testing.assert_array_almost_equal(corr, result.trans)


class TestMergeDegrees(unittest.TestCase):

    def test_1(self):
        result = Transformer.mergeDegrees([53, 8, 34, 6])
        corr = 53.142934
        self.assertAlmostEqual(corr, result, 3)

    def test_2(self):
        result = Transformer.mergeDegrees([8, 12, 0, 8])
        corr = 8.200222
        self.assertAlmostEqual(corr, result, 3)


class TestGeoreferencePoint(unittest.TestCase):

    def test_1(self):
        trans = Transformer(ifc)
        result = trans.georeferencePoint([12, 34, 23])
        corr = [458851.7312259316, 5438804.6763615385, 133]
        np.testing.assert_array_almost_equal(corr, result)

    def test_2(self):
        trans = Transformer(ifc)
        result = trans.georeferencePoint([-34, 12.123456789, 17.00000001])
        corr = [458838.9214002475, 5438755.376346237, 127.00000001]
        np.testing.assert_array_almost_equal(corr, result)

    def test_3(self):
        trans = Transformer(ifc2)
        result = trans.georeferencePoint([12, 34, 23])
        corr = [509740.99656973616, 6096753.890383066, 233]
        np.testing.assert_array_almost_equal(corr, result)


if __name__ == '__main__':
    unittest.main()
