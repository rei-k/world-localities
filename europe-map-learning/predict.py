#!/usr/bin/env python3
"""Inspect a real sampled locality with saved learned policy and geometry guard."""
import argparse
import gzip
import json

import numpy as np

from prepare import ROOT, verdict
from train import LABELS, features, forward


def load_model():
    artifact = json.loads((ROOT / 'results/policy.json').read_text())
    return {k: np.array(v, dtype=float) for k, v in artifact['weights'].items()}


def decide(model, evidence):
    if not np.isfinite(evidence['assumed_radius_m']) or evidence['assumed_radius_m'] < 0:
        raise ValueError('Uncertainty radius must be finite and non-negative')
    probabilities = forward(model, features([evidence]))[1][0]
    learned = LABELS[int(probabilities.argmax())]
    rule = verdict(evidence)
    # Exact source/geometry checks have priority. Policy cannot resolve source conflicts.
    guarded = learned if rule != 'REVIEW' and learned == rule else 'REVIEW'
    return dict(learned_prediction=learned, geometry_verifier=rule, guarded_prediction=guarded,
                probabilities_uncalibrated={label: float(probabilities[i]) for i, label in enumerate(LABELS)})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--id', required=True, help='Sampled GeoNames ID, e.g. gn:3333508')
    parser.add_argument('--claimed', help='Proposed ADM1 ISO code; defaults to registry value')
    parser.add_argument('--radius', type=float, default=100, help='Assumed coordinate uncertainty in metres')
    args = parser.parse_args()
    with gzip.open(ROOT / 'data/audit.jsonl.gz', 'rt') as f:
        record = next((r for r in map(json.loads, f) if r['locality_id'] == args.id), None)
    if record is None:
        parser.error('ID is not in this pilot sample; prepare/map it before inference')
    record.update(claimed_region=args.claimed or record['registry_region'], assumed_radius_m=args.radius)
    print(json.dumps(dict(evidence=record, decision=decide(load_model(), record),
        map_url=f"https://www.openstreetmap.org/?mlat={record['latitude']}&mlon={record['longitude']}#map=15/{record['latitude']}/{record['longitude']}"), ensure_ascii=False, indent=2))
