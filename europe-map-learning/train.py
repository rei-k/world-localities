#!/usr/bin/env python3
"""Actual one-step reinforcement learning: NumPy MLP policy, sampled-action REINFORCE."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np

from prepare import ROOT, reward, verdict, write_json, write_jsonl

LABELS = ['MATCH', 'CONFLICT', 'REVIEW']
FEATURES = ['single_map_region', 'registry_matches_map', 'claim_matches_map',
            'distance_available', 'signed_log_clearance', 'log_boundary_distance',
            'log_assumed_radius']


def read_rows(split):
    with gzip.open(ROOT / 'data' / f'{split}.jsonl.gz', 'rt') as f:
        return [json.loads(line) for line in f]


def features(rows):
    result = []
    for r in rows:
        maps, d, radius = r['map_regions'], r['boundary_distance_m'], r['assumed_radius_m']
        one = len(maps) == 1
        clearance = (d - radius) if d is not None else 0.0
        result.append([float(one), float(one and r['registry_region'] == maps[0]),
                       float(one and r['claimed_region'] == maps[0]), float(d is not None),
                       np.sign(clearance) * np.log1p(abs(clearance)) / 10,
                       np.log1p(d or 0) / 12, np.log1p(radius) / 12])
    # Names, IDs, gold labels, country and split identity are not model features.
    return np.array(result, dtype=np.float64)


def init_model(seed):
    rng = np.random.default_rng(seed)
    return dict(w1=rng.normal(0, .15, (len(FEATURES), 24)), b1=np.zeros(24),
                w2=rng.normal(0, .15, (24, 3)), b2=np.zeros(3))


def forward(model, x):
    hidden = np.tanh(x @ model['w1'] + model['b1'])
    logits = hidden @ model['w2'] + model['b2']
    exp = np.exp(logits - logits.max(axis=1, keepdims=True))
    return hidden, exp / exp.sum(axis=1, keepdims=True)


def measurements(rows, pred):
    matrix = np.zeros((3, 3), dtype=int)
    for row, action in zip(rows, pred):
        matrix[LABELS.index(row['gold']), int(action)] += 1
    f1 = []
    recall = {}
    for i, label in enumerate(LABELS):
        denom = matrix[i].sum() + matrix[:, i].sum()
        f1.append(float(2 * matrix[i, i] / denom) if denom else 0)
        recall[label] = float(matrix[i, i] / matrix[i].sum()) if matrix[i].sum() else None
    confident = np.asarray(pred) != 2
    incorrect = np.asarray(pred) != np.array([LABELS.index(r['gold']) for r in rows])
    return dict(n=len(rows), accuracy=float(np.trace(matrix) / len(rows)), macro_f1=float(np.mean(f1)),
                recall=recall, confusion_matrix=matrix.tolist(), label_order=LABELS,
                unsafe_confident_errors=int((confident & incorrect).sum()),
                mean_reward=float(np.mean([reward(LABELS[int(a)], r['gold']) for r, a in zip(rows, pred)])))


def evaluate(model, rows):
    return measurements(rows, forward(model, features(rows))[1].argmax(1))


def validate_splits(splits):
    for name, rows in splits.items():
        assert rows and all(r['split'] == name and r['gold'] == verdict(r) for r in rows)
        assert len({r['task_id'] for r in rows}) == len(rows)
    for key in ['locality_id', 'tile', 'task_id']:
        sets = [set(r[key] for r in rows) for rows in splits.values()]
        assert all(not sets[i] & sets[j] for i in range(3) for j in range(i + 1, 3)), key


def train(seed, rows, validation, steps):
    rng = np.random.default_rng(seed)
    model = init_model(seed)
    x = features(rows)
    gold = np.array([LABELS.index(r['gold']) for r in rows])
    moving = {k: np.zeros_like(v) for k, v in model.items()}
    variance = {k: np.zeros_like(v) for k, v in model.items()}
    baseline = 0.0
    history = []
    # Updates only use rewards of sampled actions, not a supervised target gradient.
    for step in range(1, steps + 1):
        indices = rng.integers(0, len(rows), size=256)
        batch = x[indices]
        hidden, probs = forward(model, batch)
        actions = (rng.random((len(indices), 1)) > probs.cumsum(1)).sum(1)
        rewards = np.where(actions == gold[indices], 1.0, np.where(actions == 2, -.25, -2.0))
        advantage = rewards - baseline
        baseline = .98 * baseline + .02 * rewards.mean()
        logit_grad = -probs.copy()
        logit_grad[np.arange(len(actions)), actions] += 1
        logit_grad *= advantage[:, None] / len(actions)
        hidden_grad = (logit_grad @ model['w2'].T) * (1 - hidden ** 2)
        gradients = dict(w2=hidden.T @ logit_grad, b2=logit_grad.sum(0),
                         w1=batch.T @ hidden_grad, b1=hidden_grad.sum(0))
        for k, gradient in gradients.items():
            moving[k] = .9 * moving[k] + .1 * gradient
            variance[k] = .999 * variance[k] + .001 * gradient ** 2
            model[k] += .003 * (moving[k] / (1 - .9 ** step)) / (np.sqrt(variance[k] / (1 - .999 ** step)) + 1e-8)
        if step == 1 or step % 250 == 0:
            item = dict(seed=seed, step=step, mean_sampled_reward=float(rewards.mean()),
                        validation=evaluate(model, validation))
            history.append(item)
    return model, history


def run(steps):
    splits = {s: read_rows(s) for s in ['train', 'validation', 'test']}
    validate_splits(splits)
    summaries, all_history, models = [], [], []
    for seed in [17, 29, 43]:
        baseline = evaluate(init_model(seed), splits['test'])
        model, history = train(seed, splits['train'], splits['validation'], steps)
        models.append(model)
        all_history.extend(history)
        summaries.append(dict(seed=seed, untrained_test=baseline,
                              validation=evaluate(model, splits['validation']),
                              trained_test=evaluate(model, splits['test'])))
        print(json.dumps(summaries[-1]), flush=True)
    # Selection uses validation only, never test scores. One fixed run, no test-driven tuning.
    selected = max(range(len(models)), key=lambda i: (summaries[i]['validation']['mean_reward'],
                                                     summaries[i]['validation']['macro_f1']))
    model = models[selected]
    payload = dict(model_type='one_step_contextual_bandit_mlp', algorithm='sampled-action REINFORCE with moving scalar reward baseline and Adam ascent',
                   features=FEATURES, labels=LABELS, selected_seed=summaries[selected]['seed'],
                   hidden_activation='tanh', weights={k: v.tolist() for k, v in model.items()},
                   training_steps=steps, batch_size=256, learning_rate=.003,
                   rewards={'correct': 1, 'incorrect_review': -.25, 'incorrect_confident': -2},
                   training_data_sha256=hashlib.sha256((ROOT / 'data/train.jsonl.gz').read_bytes()).hexdigest())
    write_json(ROOT / 'results/policy.json', payload)
    test = splits['test']
    _, probabilities = forward(model, features(test))
    predictions = [dict(task_id=r['task_id'], locality_id=r['locality_id'], country=r['country'],
                        gold=r['gold'], prediction=LABELS[int(p.argmax())],
                        probabilities={label: float(p[i]) for i, label in enumerate(LABELS)})
                   for r, p in zip(test, probabilities)]
    write_jsonl(ROOT / 'results/test-predictions.jsonl.gz', predictions)
    report = dict(status='completed', execution='local CPU; no cloud training job submitted',
                  model_type=payload['model_type'], seeds=summaries, selected_seed=payload['selected_seed'],
                  selected_test=summaries[selected]['trained_test'],
                  deterministic_oracle_test=measurements(test, [LABELS.index(verdict(r)) for r in test]),
                  always_review_test=measurements(test, [2] * len(test)),
                  mean_accuracy_across_seeds=float(np.mean([s['trained_test']['accuracy'] for s in summaries])),
                  test_by_country={c: measurements([r for r in test if r['country'] == c],
                      [p.argmax() for r, p in zip(test, probabilities) if r['country'] == c]) for c in ['AT', 'DE', 'CH']},
                  test_by_variant={v: measurements([r for r in test if r['variant'] == v],
                      [p.argmax() for r, p in zip(test, probabilities) if r['variant'] == v]) for v in sorted({r['variant'] for r in test})},
                  interpretation='Measures imitation of a snapshot-consistency verifier with real map evidence and synthetic challenges. Not independent proof of geographic truth, general geocoding skill or an LLM fine-tune.',
                  limitations=['Same ADM1 regions in train and test; only spatial tiles and locality IDs are held out.',
                               'Coordinate uncertainty is assumed, not measured; source polygon error is not quantified.',
                               'Rule oracle defines the labels and therefore scores 100% by construction.',
                               'No model confidence calibration or production release; exact geometry verifier remains authoritative.'])
    write_json(ROOT / 'results/metrics.json', report)
    write_json(ROOT / 'results/training-history.json', all_history)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--steps', type=int, default=2500)
    run(parser.parse_args().steps)
