<?xml version='1.0' encoding='UTF-8'?>
<core:CityModel xmlns:core="http://www.opengis.net/citygml/2.0" xmlns="http://www.opengis.net/citygml/profiles/base/2.0" xmlns:bldg="http://www.opengis.net/citygml/building/2.0" xmlns:gen="http://www.opengis.net/citygml/generics/2.0" xmlns:grp="http://www.opengis.net/citygml/cityobjectgroup/2.0" xmlns:app="http://www.opengis.net/citygml/appearance/2.0" xmlns:gml="http://www.opengis.net/gml" xmlns:xAL="urn:oasis:names:tc:ciq:xsdschema:xAL:2.0" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:energy="http://www.sig3d.org/citygml/2.0/energy/1.0">
  <gml:name>CityGML_test3</gml:name>
  <gml:boundedBy>
    <gml:Envelope srsDimension="3" srsName="EPSG:32632">
      <gml:lowerCorner srsDimension="3">479337.60050634824 5444167.43024925 -3.0</gml:lowerCorner>
      <gml:upperCorner srsDimension="3">479381.60050634824 5444186.43024925 9.0</gml:upperCorner>
    </gml:Envelope>
  </gml:boundedBy>
  <core:cityObjectMember>
    <bldg:Building gml:id="UUID_6c764637-1045-40b0-92f8-3206eb81f0af">
      <gml:name>Buerogebaeude</gml:name>
      <gml:description>No real Building</gml:description>
      <core:creationDate>2022-09-26</core:creationDate>
      <bldg:class codeSpace="http://www.sig3d.org/codelists/citygml/2.0/building/2.0/_AbstractBuilding_class.xml">1030</bldg:class>
      <bldg:function codeSpace="http://www.sig3d.org/codelists/citygml/2.0/building/2.0/_AbstractBuilding_function.xml">1120</bldg:function>
      <bldg:usage codeSpace="http://www.sig3d.org/codelists/citygml/2.0/building/2.0/_AbstractBuilding_usage.xml">1120</bldg:usage>
      <core:relativeToTerrain>substaintiallyAboveTerrain</core:relativeToTerrain>
      <bldg:measuredHeight uom="m">15.34932</bldg:measuredHeight>
      <bldg:storeysAboveGround>4</bldg:storeysAboveGround>
      <bldg:storeysBelowGround>1</bldg:storeysBelowGround>
      <bldg:storeyHeightsAboveGround>3.0</bldg:storeyHeightsAboveGround>
      <bldg:storeyHeightsBelowGround>3.0</bldg:storeyHeightsBelowGround>
      <bldg:lod0FootPrint>
        <gml:MultiSurface>
          <gml:surfaceMember>
            <gml:Polygon>
              <gml:exterior>
                <gml:LinearRing>
                  <gml:pos>479356.600506348 5444183.43024925 -3</gml:pos>
                  <gml:pos>479356.600506348 5444185.43024925 -3</gml:pos>
                  <gml:pos>479362.600506348 5444185.43024925 -3</gml:pos>
                  <gml:pos>479362.600506348 5444183.43024925 -3</gml:pos>
                  <gml:pos>479380.600506348 5444183.43024925 -3</gml:pos>
                  <gml:pos>479380.600506348 5444171.43024925 -3</gml:pos>
                  <gml:pos>479363.100506348 5444171.43024925 -3</gml:pos>
                  <gml:pos>479363.100506348 5444167.43024925 -3</gml:pos>
                  <gml:pos>479356.100506348 5444167.43024925 -3</gml:pos>
                  <gml:pos>479356.100506348 5444171.43024925 -3</gml:pos>
                  <gml:pos>479338.600506348 5444171.43024925 -3</gml:pos>
                  <gml:pos>479338.600506348 5444183.43024925 -3</gml:pos>
                  <gml:pos>479356.600506348 5444183.43024925 -3</gml:pos>
                </gml:LinearRing>
              </gml:exterior>
            </gml:Polygon>
          </gml:surfaceMember>
        </gml:MultiSurface>
      </bldg:lod0FootPrint>
      <bldg:lod0RoofEdge>
        <gml:MultiSurface>
          <gml:surfaceMember>
            <gml:Polygon>
              <gml:exterior>
                <gml:LinearRing>
                  <gml:pos>479337.600506348 5444176.43024925 9</gml:pos>
                  <gml:pos>479337.600506348 5444184.43024925 9</gml:pos>
                  <gml:pos>479355.600506348 5444184.43024925 9</gml:pos>
                  <gml:pos>479355.600506348 5444186.43024925 9</gml:pos>
                  <gml:pos>479363.600506348 5444186.43024925 9</gml:pos>
                  <gml:pos>479363.600506348 5444184.43024925 9</gml:pos>
                  <gml:pos>479381.600506348 5444184.43024925 9</gml:pos>
                  <gml:pos>479381.600506348 5444170.43024925 9</gml:pos>
                  <gml:pos>479337.600506348 5444170.43024925 9</gml:pos>
                  <gml:pos>479337.600506348 5444176.43024925 9</gml:pos>
                </gml:LinearRing>
              </gml:exterior>
            </gml:Polygon>
          </gml:surfaceMember>
        </gml:MultiSurface>
      </bldg:lod0RoofEdge>
    </bldg:Building>
  </core:cityObjectMember>
</core:CityModel>
