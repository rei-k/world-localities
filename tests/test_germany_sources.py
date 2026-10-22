import copy
import hashlib
import gzip
import io
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import germany_sources as de
import germany_inspire as inspire


def source(**extra):
    return dict(id='DE-fixture', country='DE', path='source.zip', bytes=1,
                sha256='0' * 64, states=['NW'], provenance='official_direct',
                format='hk_csv_zip', member='rows.txt', delimiter=';', header=True,
                licence='fixture', licence_url='https://example.org/terms', **extra)


def hk(**changes):
    row = dict(zip(de.HK_FIELDS[:20], ['N', 'DENW01HK10000a1o', 'A', '05', 'Nordrhein-Westfalen',
                   '9', 'Arnsberg', '11', 'Bochum', '000', 'Bochum', '0000', '',
                   '00001', 'Äußere Straße', '12', 'a', '32', '370000.125', '5700000.250']))
    row.update(changes)
    return row


def gv(typ, ags, association='    ', name='Name', text='  '):
    return typ + '20260930' + ags.ljust(8) + association + name.ljust(50) + ' ' * 50 + text + ' ' * 96


class Chunked(io.StringIO):
    def read(self, size=-1):
        return super().read(min(19, size) if size >= 0 else 19)


class GermanyContracts(unittest.TestCase):
    def test_house_suffix_and_zero_padded_codes_survive(self):
        row = de.hk_record(source(), 'rows.txt', 1, hk())
        self.assertEqual(row['municipality_code'], '05911000')
        self.assertEqual((row['number'], row['number_addition']), ('12', 'a'))
        self.assertEqual(row['coordinates']['crs'], 'EPSG:25832')
        self.assertEqual(row['raw']['str'], 'Äußere Straße')

    def test_range_is_one_observation(self):
        row = de.hk_record(source(), 'rows.txt', 1, hk(hnr='12-18'))
        self.assertEqual(row['number'], '12-18')

    def test_road_query_does_not_scan_unrelated_state_address_files(self):
        road = dict(source(), id='DE-roads', format='bkg_roads_geojson_zip')
        row = {'kind': 'road_segment', 'state': 'DE', 'name': 'Straße'}
        with patch.object(de.shared, 'verify_pin'), patch.object(de, 'records', return_value=iter([row])) as read:
            result = de.search({'sources': [source(), road]}, Path('.'), kind='road_segment')
        self.assertEqual(result['results'], [row])
        read.assert_called_once_with(road, Path('.'))

    def test_berlin_borough_code_is_not_replaced_in_source(self):
        s = source()
        s['states'] = ['BE']
        raw = hk(oid='DEBE00YY2GG000L4', landschl='11', land='Berlin', regbezschl='0', kreisschl='00', gmdschl='002', gmd='Friedrichshain-Kreuzberg', zone='33')
        row = de.hk_record(s, 'rows.txt', 1, raw)
        self.assertEqual(row['municipality_code'], '11000000')
        self.assertEqual(row['source_administrative_code'], '11000002')
        self.assertEqual(row['raw']['gmdschl'], '002')
        self.assertEqual(row['municipality_name'], 'Berlin')
        self.assertEqual(row['borough_name'], 'Friedrichshain-Kreuzberg')
        self.assertEqual(row['source_administrative_name'], row['raw']['gmd'])

    def test_hessian_alias_keeps_original_header(self):
        raw = hk()
        raw['kreissch'] = raw.pop('kreisschl')
        row = de.hk_record(source(), 'rows.txt', 1, raw)
        self.assertEqual(row['municipality_code'], '05911000')
        self.assertIn('kreissch', row['raw'])
        self.assertNotIn('kreisschl', row['raw'])

    def test_invalid_zone_code_and_coordinate_are_rejected(self):
        for changes in ({'zone': '31'}, {'gmdschl': '0'}, {'ostwert': 'nan'}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                de.hk_record(source(), 'rows.txt', 1, hk(**changes))

    def test_state_mismatch_is_rejected(self):
        with self.assertRaises(ValueError):
            de.hk_record(source(), 'rows.txt', 1, hk(landschl='08'))

    def test_gv_utf8_name_and_free_area_are_distinguished(self):
        s = source()
        row = de.gv_record(s, 'gv.txt', 1, gv('60', '05911000', '0000', 'Äußere Fläche', '66'))
        self.assertEqual(row['ars'], '059110000000')
        self.assertEqual(row['name'], 'Äußere Fläche')
        self.assertTrue(row['is_municipality_free_area'])
        self.assertEqual(len(row['raw']['line']), 220)

    def test_gv_rejects_truncated_and_unknown_record_types(self):
        for line in (gv('60', '05911000', '0000', text='64')[:-1], gv('70', '05')):
            with self.assertRaises(ValueError):
                de.gv_record(source(), 'gv.txt', 1, line)

    def test_special_gv_bucket_has_explicit_state_parent_rule(self):
        with tempfile.TemporaryDirectory() as root:
            with zipfile.ZipFile(Path(root) / 'source.zip', 'w') as z:
                z.writestr('gv.txt', gv('10', '07', name='Rheinland-Pfalz') + '\n' +
                           gv('50', '07000', '9999', 'Gemeinsames Hoheitsgebiet', '50') + '\n')
            s = source()
            s.update(format='gv100_zip', member='gv.txt')
            rows, reference = de.administrative_reference(s, root)
            self.assertEqual(rows[1]['parent_id'], '10:07')
            self.assertEqual(rows[1]['parent_link_rule'], 'GV100_special_state_bucket')
            self.assertEqual(reference['unresolved_parent_references'], [])

    def test_json_feature_collection_spans_small_chunks(self):
        doc = {'type': 'FeatureCollection', 'features': [{'type': 'Feature', 'id': 'ä',
               'properties': {'text': 'Straße { , ] "'}, 'geometry': None}],
               'numberMatched': 1, 'numberReturned': 1}
        metadata = {}
        rows = list(de.json_features(Chunked(json.dumps(doc, ensure_ascii=False)), metadata))
        self.assertEqual(rows, doc['features'])
        self.assertEqual(metadata['numberMatched'], 1)

    def test_json_truncation_duplicate_root_and_trailing_data_fail(self):
        for text in ('{"type":"FeatureCollection","features":[',
                     '{"type":"FeatureCollection","features":[],"features":[]}',
                     '{"type":"FeatureCollection","features":[]}garbage'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                list(de.json_features(io.StringIO(text), {}))

    def test_json_nested_duplicates_and_nonfinite_geometry_fail(self):
        for feature in ('{"type":"Feature","id":"one","id":"two"}',
                        '{"type":"Feature","geometry":{"coordinates":[NaN,1]}}'):
            with self.assertRaises(ValueError):
                list(de.json_features(io.StringIO('{"type":"FeatureCollection","features":[' + feature + ']}'), {}))

    def test_json_number_at_a_chunk_boundary_is_not_truncated(self):
        metadata = {}
        text = '{"type":"FeatureCollection","features":[],"numberMatched":123456789012345678901234567890}'
        self.assertEqual(list(de.json_features(Chunked(text), metadata)), [])
        self.assertEqual(metadata['numberMatched'], 123456789012345678901234567890)

    def test_thuringian_local_joins_keep_locator_types_and_namespace_values(self):
        ns = ('xmlns:wfs="http://www.opengis.net/wfs/2.0" '
              'xmlns:ad="http://inspire.ec.europa.eu/schemas/ad/4.0" '
              'xmlns:gml="http://www.opengis.net/gml/3.2" '
              'xmlns:gn="http://inspire.ec.europa.eu/schemas/gn/4.0" '
              'xmlns:xlink="http://www.w3.org/1999/xlink"')
        spelling = '<ad:name><gn:GeographicalName><gn:language>deu</gn:language><gn:spelling><gn:SpellingOfName><gn:text>{}</gn:text></gn:SpellingOfName></gn:spelling></gn:GeographicalName></ad:name>'
        bodies = {
            'AdminUnitName': '<ad:AdminUnitName gml:id="AdminUnitName_16074017">' + spelling.format('Beispielstadt') + '</ad:AdminUnitName>',
            'ThoroughfareName': '<ad:ThoroughfareName gml:id="ThoroughfareName_1607401710608">' + spelling.format('Äußere Straße') + '</ad:ThoroughfareName>',
            'Address': '<ad:Address gml:id="Address_DETH000000000001">'
                       '<ad:component xlink:href="https://example.org/?ID=x#AdminUnitName_16074017"/>'
                       '<ad:component xlink:href="https://example.org/?ID=y#ThoroughfareName_1607401710608"/>'
                       '<ad:component xlink:href="https://example.org/#Unresolved"/>'
                       '<ad:locator><ad:AddressLocator>'
                       '<ad:LocatorDesignator><ad:designator>12-18</ad:designator><ad:type xlink:href="http://inspire.ec.europa.eu/codelist/LocatorDesignatorTypeValue/addressNumber"/></ad:LocatorDesignator>'
                       '<ad:LocatorDesignator><ad:designator>a</ad:designator><ad:type xlink:href="http://inspire.ec.europa.eu/codelist/LocatorDesignatorTypeValue/addressNumberExtension"/></ad:LocatorDesignator>'
                       '</ad:AddressLocator></ad:locator>'
                       '<ad:position><ad:GeographicPosition><ad:geometry><gml:Point srsName="urn:ogc:def:crs:EPSG::25832"><gml:pos>700000.1 5630000.2</gml:pos></gml:Point></ad:geometry><ad:default>true</ad:default></ad:GeographicPosition></ad:position></ad:Address>'}
        with tempfile.TemporaryDirectory() as root:
            p = Path(root) / 'source.zip'
            pages, expected = [], {t: 1 for t in bodies}
            with zipfile.ZipFile(p, 'w') as z:
                for typ, body in bodies.items():
                    raw = ('<wfs:FeatureCollection ' + ns + ' numberReturned="1"><wfs:member>' + body + '</wfs:member></wfs:FeatureCollection>').encode()
                    member = typ + '/0.xml.gz'
                    z.writestr(member, gzip.compress(raw, mtime=0))
                    pages.append({'member': member, 'type': typ, 'original_bytes': len(raw),
                                  'original_sha256': hashlib.sha256(raw).hexdigest(), 'numberReturned': 1})
                z.writestr('index.json', json.dumps({'pages': pages, 'expected_rows': expected}))
            s = source()
            s.update(format='inspire_th_zip', states=['TH'], expected_rows=expected)
            receipt = {}
            rows = list(de.records(s, root, receipt))
            row = rows[-1]
            self.assertEqual(row['municipality_code'], '16074017')
            self.assertEqual(row['street'], 'Äußere Straße')
            self.assertEqual((row['number'], row['number_addition']), ('12-18', 'a'))
            self.assertEqual(row['missing_references'], ['Unresolved'])
            self.assertEqual(row['coordinates']['crs'], 'EPSG:25832')
            self.assertEqual(rows[1]['street_names'][0]['language'], 'deu')
            self.assertEqual(receipt['feature_counts'], expected)

    def test_replay_refuses_changed_imported_reader(self):
        manifest = de.load_manifest()
        accepted = {'implementation_sha256': de.IMPLEMENTATION_SHA256,
                    'manifest_sha256': hashlib.sha256(de.shared.canonical(manifest).encode()).hexdigest(),
                    'implementation_files': {}}
        with self.assertRaisesRegex(ValueError, 'imported reader'):
            de.replay(manifest, Path('.'), accepted)

    def test_xml_entity_declaration_across_chunks_fails(self):
        reader = de.XMLGuard(io.BytesIO(b'<root><!DOCTYPE x [<!ENTITY y "bad">]></root>'))
        with self.assertRaises(ValueError):
            while reader.read(5):
                pass

    def test_csv_wrong_width_fails(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / 'source.zip'
            with zipfile.ZipFile(path, 'w') as z:
                z.writestr('rows.txt', 'oid;hnr\nx\n')
            with self.assertRaises(ValueError):
                list(de.records(source(), root))

    def test_dbf_streaming_and_deleted_record_guard(self):
        descriptor = bytearray(32)
        descriptor[:3], descriptor[11], descriptor[16] = b'hnr', ord('C'), 4
        header = bytearray(32)
        struct.pack_into('<IHH', header, 4, 1, 65, 5)
        raw = bytes(header) + bytes(descriptor) + b'\r' + b' 12a ' + b'\x1a'
        self.assertEqual(list(de.dbf_rows(io.BytesIO(raw))), [(1, {'hnr': '12a'})])
        with self.assertRaises(ValueError):
            list(de.dbf_rows(io.BytesIO(raw[:65] + b'*12a ')))

    def test_pin_tamper_is_not_accepted(self):
        with tempfile.TemporaryDirectory() as root:
            p = Path(root) / 'source.zip'
            p.write_bytes(b'changed')
            with self.assertRaises(ValueError):
                de.shared.verify_pin(source(), root)

    def test_preexisting_partial_is_preserved(self):
        with tempfile.TemporaryDirectory() as root:
            p = Path(root) / 'source.zip.partial'
            p.write_bytes(b'other downloader')
            manifest = {'sources': [dict(source(), requested_url='https://example.org/source.zip')], 'evidence': []}
            with self.assertRaises(ValueError):
                de.acquire(manifest, root)
            self.assertEqual(p.read_bytes(), b'other downloader')

    def test_racing_partial_is_preserved(self):
        with tempfile.TemporaryDirectory() as root:
            partial = Path(root) / 'source.zip.partial'
            s = dict(source(), requested_url='https://example.org/source.zip', final_url='https://example.org/source.zip')

            class Response(io.BytesIO):
                def geturl(self):
                    return s['final_url']

            def race(*args, **kwargs):
                partial.write_bytes(b'other downloader')
                return Response(b'x')

            with patch.object(de, 'urlopen', side_effect=race), self.assertRaises(FileExistsError):
                de.acquire({'sources': [s]}, root)
            self.assertEqual(partial.read_bytes(), b'other downloader')

    def test_scope_and_all_sixteen_states_are_required(self):
        manifest = json.loads(de.DEFAULT_MANIFEST.read_text())
        for mutate in (lambda d: d.update(deliverability_in_scope=True),
                       lambda d: d['states'].pop(),
                       lambda d: d['sources'][0].update(path='../escape.zip')):
            d = copy.deepcopy(manifest)
            mutate(d)
            with tempfile.TemporaryDirectory() as root:
                p = Path(root) / 'manifest.json'
                p.write_text(json.dumps(d))
                with self.assertRaises(ValueError):
                    de.load_manifest(p)


if __name__ == '__main__':
    unittest.main()
