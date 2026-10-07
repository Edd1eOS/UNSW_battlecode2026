"""Invoke the immutable evidence collector with the explicit final Oct7 scope."""
import json
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
names = ['v5', 'exploration', 'investment', 'foraging', 'cooperation',
         'investment-v2', 'cooperation-egress', 'cooperation-arrival',
         'allocation', 'emergency', 'certainty', 'emergency-v2', 'witness', 'active-v14']
reports = ['exploration', 'investment', 'foraging', 'cooperation', 'investment-v2',
           'egress', 'arrival', 'allocation', 'emergency', 'certainty', 'emergency-v2', 'witness']
command = [sys.executable, 'tools/oct7_build_manifest.py']
for name in names:
    command += ['--panel', f'test-results/oct7-{name}-panel']
for name in reports:
    command += ['--report', f'test-results/oct7-{name}-discovery-compare.json']

evidence = {Path('.gitattributes'), Path('.gitignore'), Path('README.md'),
            Path('test-results/oct7-run-final-checks.py'), Path(__file__).relative_to(root),
            Path('test-results/oct7-final-collector-command.json')}
# Use the immutable round-start tree. Staging or committing this round must not
# silently remove its new tests from a later collection of the same evidence.
base_commit = '70c01361691d96c8b1d74b55893787b9aac688d9'
tracked = {Path(p.decode('utf-8')) for p in subprocess.check_output(
    ['git','ls-tree','-r','--name-only','-z',base_commit], cwd=root).split(b'\0') if p}
evidence.update(Path('tools') / name for name in (
    'audit_online.py', 'trajectory_metrics.py', 'panel_trajectory.py',
    'audit_online_panel.py', 'import_online_replays.py', 'check_cpp.py',
    'verify_candidate.py', 'verify_portal_tracking.py'))
evidence.update(Path('test-results') / name for name in (
    'certainty-v1-physics.log', 'certainty-v1-inherited-physics.log'))
patterns = ['docs/oct7-*', 'docs/generalist-*-v*.md', 'tools/oct7_*.py',
            'tests/*_test.cpp', 'tests/*_test.py', 'tests/inspect_exploration*.cpp',
            'tests/emergency_portal_facing_probe.cpp', 'tests/fixtures/oct7-*.json',
            'test-results/oct7-*', 'test-results/*correctness.json',
            'test-results/*final-protocol.json', 'test-results/*history-budget.json',
            'test-results/*branch*proof.json', 'test-results/*cpp-checks.log',
            'test-results/certainty-v1-*proof.json', 'test-results/certainty-v1-reader-freeze-check.json',
            'test-results/certainty-v1-branch-semantics.log',
            'test-results/generalist-cooperation-v1-freeze.json',
            'test-results/emergency-*evidence*.json', 'test-results/emergency-*evidence*.log',
            'test-results/emergency-facing-review/*.json',
            'test-results/emergency-facing-review/compare_selected_evidence.py',
            'test-results/oct7-exploration-causal-ro/**/*',
            'test-results/inspect_certainty_trauma/**/*',
            'test-results/inspect_allocation_trauma/**/*']
for pattern in patterns:
    evidence.update(p.relative_to(root) for p in root.glob(pattern) if p.is_file()
                    and not (p.relative_to(root).parts[0]=='tests' and p.relative_to(root) in tracked))
evidence.discard(Path('docs/oct7-experiment-manifest.json'))
# The independent KGTS and online51 manifests bind their complete raw panels.
# Do not pass a KGTS plan to the two-opponent primary collector.
assert Path('docs/oct7-kgts-evidence-manifest.json') in evidence
assert Path('docs/oct7-online-baseline-findings-manifest.json') in evidence
for file in sorted(evidence):
    command += ['--evidence', file.as_posix()]
command += ['--out', 'docs/oct7-experiment-manifest.json']
record = root / 'test-results/oct7-final-collector-command.json'
record.write_text(json.dumps({'command':command, 'evidence_count':len(evidence),
                             'primary_panels':names, 'primary_reports':reports}, indent=2)+'\n', encoding='utf-8')
result = subprocess.run(command, cwd=root)
raise SystemExit(result.returncode)
