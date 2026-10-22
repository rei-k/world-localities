import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import germany_wfs as wfs


class WFSContracts(unittest.TestCase):
    def test_page_count_and_identity_order_are_required(self):
        value = {'type': 'FeatureCollection', 'numberMatched': 2, 'numberReturned': 2,
                 'features': [{'properties': {'objid': 'a'}}, {'properties': {'objid': 'b'}}]}
        self.assertEqual(wfs.page_receipt(json.dumps(value).encode(), 0, 2, 5000, 'url')['last_id'], 'b')
        value['features'].reverse()
        with self.assertRaises(ValueError):
            wfs.page_receipt(json.dumps(value).encode(), 0, 2, 5000, 'url')
        value['features'].reverse()
        value['numberMatched'] = 3
        with self.assertRaises(ValueError):
            wfs.page_receipt(json.dumps(value).encode(), 0, 2, 5000, 'url')

    def test_forbidden_responses_are_never_retried(self):
        error = HTTPError('https://example.org/', 403, 'Forbidden', {}, io.BytesIO(b'forbidden'))
        with patch.object(wfs, 'urlopen', side_effect=error) as get, patch.object(wfs.time, 'sleep') as sleep:
            with self.assertRaises(HTTPError):
                wfs.read_http('https://example.org/', 100)
            self.assertEqual(get.call_count, 1)
            sleep.assert_not_called()

    def test_provider_count_drift_prevents_candidate_creation(self):
        receipt = {'member': 'pages/0.json', 'offset': 0, 'numberReturned': 1, 'first_id': 'a', 'last_id': 'a'}
        with tempfile.TemporaryDirectory() as root:
            output = Path(root) / 'candidate.zip'
            with patch.object(wfs, 'matched_count', side_effect=[(1, {}), (2, {})]), patch.object(wfs, 'download_page', return_value=receipt):
                with self.assertRaisesRegex(ValueError, 'count changed'):
                    wfs.acquire_candidate(output, Path(root) / 'work', workers=1)
            self.assertFalse(output.exists())

    def test_thuringian_hits_total_is_separate_from_feature_matched_count(self):
        data = b'<wfs:FeatureCollection xmlns:wfs="http://www.opengis.net/wfs/2.0" xmlns:ad="http://inspire.ec.europa.eu/schemas/ad/4.0" xmlns:gml="http://www.opengis.net/gml/3.2" numberMatched="1" numberReturned="1"><wfs:member><ad:Address gml:id="address-11"/></wfs:member></wfs:FeatureCollection>'
        receipt = wfs.th_page_receipt(data, 'Address', 10, 11, 5, 'url')
        self.assertEqual(receipt['numberReturned'], 1)
        self.assertEqual(receipt['provider_numberMatched'], '1')
        with self.assertRaises(ValueError):
            wfs.th_page_receipt(data, 'Address', 10, 12, 5, 'url')

    def test_uncached_page_ceiling_prevents_large_downloads(self):
        with tempfile.TemporaryDirectory() as root:
            for acquire in (wfs.acquire_candidate, wfs.acquire_th_candidate):
                with self.subTest(acquire=acquire.__name__), patch.object(wfs, 'matched_count', return_value=(6000, {})), patch.object(wfs, 'read_http') as read:
                    with self.assertRaisesRegex(ValueError, 'ceiling'):
                        acquire(Path(root) / 'new.zip', Path(root) / 'work', max_new_pages=0)
                    read.assert_not_called()

    def test_disk_reserve_prevents_download_before_pages_are_queued(self):
        usage = type('Usage', (), {'free': 1024})()
        with tempfile.TemporaryDirectory() as root:
            for acquire in (wfs.acquire_candidate, wfs.acquire_th_candidate):
                with self.subTest(acquire=acquire.__name__), patch.object(wfs, 'matched_count', return_value=(1, {})), patch.object(wfs.shutil, 'disk_usage', return_value=usage), patch.object(wfs, 'read_http') as read:
                    with self.assertRaisesRegex(ValueError, 'Insufficient space'):
                        acquire(Path(root) / 'new.zip', Path(root) / 'work', max_new_pages=3)
                    read.assert_not_called()


if __name__ == '__main__':
    unittest.main()
