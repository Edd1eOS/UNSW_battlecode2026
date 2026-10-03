"""Persist completed official-engine comparisons without replacing online evidence."""
import argparse
from collections import Counter
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--record', required=True)
parser.add_argument('--prefix', required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
path = root / args.record
record = json.loads(path.read_text(encoding='utf-8'))
comparisons = []
for report_path in sorted((root / 'test-results').glob(args.prefix + '*/summary.json')):
    report = json.loads(report_path.read_text(encoding='utf-8'))
    games = report['games']
    comparisons.append(dict(name=report_path.parent.name,
        candidate=report['candidate'], opponent=report['opponent'],
        source_hash=report['candidate_hash'], opponent_hash=report['opponent_hash'],
        engine_version=report['engine_version'], map_dir=report['map_dir'],
        results=dict(Counter(g['result'] for g in games)),
        peak_points=max((g['peak_points'] or 0 for g in games), default=0), games=games))
record['local_comparisons'] = comparisons
record['local_game_count'] = sum(len(c['games']) for c in comparisons)
path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
for c in comparisons:
    print(c['name'], c['results'], 'peak', c['peak_points'])
print('Completed:', len(comparisons), 'comparisons,', record['local_game_count'], 'games')
