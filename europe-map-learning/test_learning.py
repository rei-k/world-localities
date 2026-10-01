import unittest

from shapely import STRtree
from shapely.geometry import Point, box

from prepare import map_evidence, reward, spatial_split, verdict
from train import read_rows, validate_splits
from predict import decide, load_model


class MapTests(unittest.TestCase):
    def test_shared_boundary_and_outside_are_uncertain(self):
        polys = [box(0, 0, 10, 10), box(10, 0, 20, 10)]
        tree = STRtree(polys)
        self.assertEqual(map_evidence(Point(10, 5), polys, tree, ['A', 'B']), (['A', 'B'], None))
        self.assertEqual(map_evidence(Point(-1, 5), polys, tree, ['A', 'B']), ([], None))
        self.assertEqual(map_evidence(Point(5, 5), polys, tree, ['A', 'B']), (['A'], 5.0))

    def test_review_precedes_claim_decision(self):
        r = dict(map_regions=['AT-9'], registry_region='AT-9', claimed_region='AT-9',
                 boundary_distance_m=101, assumed_radius_m=100)
        self.assertEqual(verdict(r), 'MATCH')
        self.assertEqual(verdict(dict(r, claimed_region='AT-1')), 'CONFLICT')
        self.assertEqual(verdict(dict(r, registry_region='AT-1')), 'REVIEW')
        self.assertEqual(verdict(dict(r, boundary_distance_m=100, claimed_region='AT-1')), 'REVIEW')
        self.assertEqual(verdict(dict(r, boundary_distance_m=None)), 'REVIEW')
        self.assertEqual(verdict(dict(r, map_regions=[])), 'REVIEW')
        self.assertEqual(verdict(dict(r, map_regions=['AT-1', 'AT-9'])), 'REVIEW')

    def test_penalizes_false_certainty(self):
        self.assertGreater(reward('REVIEW', 'MATCH'), reward('MATCH', 'REVIEW'))
        self.assertEqual(reward('MATCH', 'MATCH'), 1)

    def test_guard_blocks_observed_confident_source_conflict(self):
        evidence = dict(map_regions=['AT-3'], registry_region='AT-9', claimed_region='AT-9',
                        boundary_distance_m=535.851, assumed_radius_m=100)
        self.assertEqual(decide(load_model(), evidence)['guarded_prediction'], 'REVIEW')

    def test_invalid_uncertainty_is_rejected(self):
        for radius in [-1, float('nan'), float('inf')]:
            with self.assertRaises(ValueError):
                decide(load_model(), {'assumed_radius_m': radius})

    def test_dataset_has_no_split_overlap_and_labels_replay(self):
        splits = {s: read_rows(s) for s in ['train', 'validation', 'test']}
        validate_splits(splits)
        for rows in splits.values():
            for r in rows:
                self.assertEqual(spatial_split(r['latitude'], r['longitude']), (r['tile'], r['split']))


if __name__ == '__main__':
    unittest.main()
