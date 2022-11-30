#
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0.txt
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#

import xml.etree.ElementTree as ET


class XMLInfo:
    """
    The image metadata dictionary contains the following keys-values:
        'unit' - string denoting the physical units of the image origin,
                 and spacing.
        'times' - string denoting the time associated with the image in
                            ('%Y-%m-%d %H:%M:%S.%f' -
                            Year-month-day hour:minute:second.microsecond) format.
        'imaris_channels_information' - XML string denoting channel information.
        XML structure:

    <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
      <xs:element name="imaris_channels_information">
        <xs:complexType>
          <xs:sequence>
            <xs:element name="channel">
              <xs:complexType>
                  <xs:element type="xs:string" name="name"/>
                  <xs:element type="xs:string" name="description"/>
                  <xs:element type="xs:string" name="color"/>
                  <xs:element type="xs:string" name="range"/>
                  <xs:element type="xs:string" name="gamma" minOccurs="0" maxOccurs="1"/>
              </xs:complexType>
            </xs:element>
          </xs:sequence>
        </xs:complexType>
      </xs:element>
    </xs:schema>
    """

    def __init__(self, xml_string):
        self.root_element = ET.fromstring(xml_string)

    @staticmethod
    def _parse_tuple(s):
        if s is None:
            return None
        return s.replace(",", " ").split()

    @property
    def channel_names(self):
        return [e.text for e in self.root_element.findall("channel/name")]

    def descriptions(self):
        return [e.text for e in self.root_element.findall("channel/description")]

    def colors(self):
        colors = []
        for ch_element in self.root_element.iter("channel"):
            e = ch_element.find("color")
            if e is None:
                c = None
            else:
                c = [float(c) / 255 for c in self._parse_tuple(e.text)]
            colors.append(c)
        return colors

    def color_tables(self):
        color_tables = []
        for ch_element in self.root_element.iter("channel"):
            e = ch_element.find("color")
            if e is None:
                t = None
            else:
                t = [float(c) / 255 for c in self._parse_tuple(e.text)]
            color_tables.append(t)
        return color_tables

    def ranges(self):
        return [self._parse_tuple(e.text) for e in self.root_element.findall("channel/range")]

    def gamas(self):
        gamas = []
        for ch_element in self.root_element.iter("channel"):
            e = ch_element.find("gama")
            if e is None:
                g = None
            else:
                g = [float(self._parse_tuple(e.text))]
            gamas.append(g)
        return gamas

    def alpha(self):
        return [float(e.text) for e in self.root_element.findall("channel/alpha")]


class OMEInfo:

    _ome_ns = {"OME": "http://www.openmicroscopy.org/Schemas/OME/2015-01"}

    def __init__(self, ome_xml_string):
        self._root_element = ET.fromstring(ome_xml_string)

    def _image_element(self):
        return self._root_element.findall("OME:Image/OME:Pixels", self._ome_ns)[0]

    @property
    def channel_names(self):
        el = self._root_element.findall("OME:Image/OME:Pixels/OME:Channel", self._ome_ns)
        return [e.attrib["Name"] for e in el]

    @property
    def dimension_order(self):
        return self._image_element().attrib["DimensionOrder"]

    @property
    def size(self):
        img_element = self._image_element()
        size = []
        for d in self.dimension_order:
            attr = "Size{}".format(d)
            size.append(int(img_element.get(attr, 1)))
        return size

    @property
    def spacing(self):
        img_element = self._image_element()
        spacing = []
        for d in self.dimension_order:
            attr = "PhysicalSize{}".format(d)
            spacing.append(float(img_element.get(attr, 1.0)))
        return spacing

    @property
    def units(self):
        img_element = self._image_element()
        default = "µm"
        units = []
        for d in self.dimension_order:
            attr = "PhysicalSize{}Unit".format(d)
            units.append(img_element.get(attr, default))
        return units
