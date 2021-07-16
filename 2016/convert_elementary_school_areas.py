import os
import json
import xml.etree.ElementTree as ET
import numpy as np

prefectures = json.load(open('prefectures.json', 'r'))

if not os.path.exists('outputs'):
    os.mkdir('outputs')

for i, prefecture in enumerate(prefectures):
    if not os.path.exists('outputs/%02d_%s' % (i + 1, prefecture)):
        os.mkdir('outputs/%02d_%s' % (i + 1, prefecture))

    root = ET.parse('original_data/A27-16_%02d.xml' % (i + 1)).getroot()

    curves = {}
    for curve in root.findall('gml:Curve',
                              {'gml': 'http://www.opengis.net/gml/3.2'}):
        id = curve.attrib['{http://www.opengis.net/gml/3.2}id']
        pos_list = curve.find('.//gml:posList',
                              {'gml': 'http://www.opengis.net/gml/3.2'})
        positions = pos_list.text.split()
        curves[id] = np.array(positions).reshape(-1, 2).tolist()

    cities = {}
    for area in root.findall(
            'ksj:ElementarySchoolArea',
        {'ksj': 'http://nlftp.mlit.go.jp/ksj/schemas/ksj-app'}):
        school_id = area.attrib['{http://www.opengis.net/gml/3.2}id']

        administrative_area_code = area.find('ksj:administrativeAreaCode', {
            'ksj': 'http://nlftp.mlit.go.jp/ksj/schemas/ksj-app'
        }).text
        establishment_body = area.find('ksj:establishmentBody', {
            'ksj': 'http://nlftp.mlit.go.jp/ksj/schemas/ksj-app'
        }).text.rstrip('立')
        name = area.find('ksj:name', {
            'ksj': 'http://nlftp.mlit.go.jp/ksj/schemas/ksj-app'
        }).text

        positions = []
        curve_index = 1
        while ('cv%s_%d' % (school_id.split('-')[1], curve_index) in curves):
            positions.append(curves['cv%s_%d' %
                                    (school_id.split('-')[1], curve_index)])
            curve_index += 1

        if not administrative_area_code in cities:
            cities[administrative_area_code] = {
                'establishment_body': establishment_body,
                'schools': []
            }

        cities[administrative_area_code]['schools'].append({
            'id': school_id,
            'name': name,
            'positions': positions
        })

    for administrative_area_code, city in cities.items():
        kml = ET.Element('kml', {'xmlns': 'http://www.opengis.net/kml/2.2'})
        document = ET.SubElement(kml, 'Document')

        for school in city['schools']:
            for positions in school['positions']:
                placemark = ET.SubElement(document, 'Placemark')
                name = ET.SubElement(placemark, 'name')
                name.text = school['name']

                polygon = ET.SubElement(placemark, 'Polygon')
                outer_boundary_is = ET.SubElement(polygon, 'outerBoundaryIs')
                linear_ring = ET.SubElement(outer_boundary_is, 'LinearRing')

                coordinates = ET.SubElement(linear_ring, 'coordinates')
                coordinates.text = ' '.join(
                    [','.join(reversed(x)) for x in positions])

        ET.ElementTree(kml).write('outputs/%02d_%s/%s_%s_小学校区.kml' %
                                  (i + 1, prefecture, administrative_area_code,
                                   city['establishment_body']),
                                  encoding='utf-8',
                                  xml_declaration=True)
