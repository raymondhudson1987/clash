"""Sync only template-referenced upstream files; custom/ is never written."""
import shutil
import sys
from pathlib import Path

from check_rules import read_yaml, rule_path, validate_payload

def sync(root, upstream):
    root, upstream = Path(root), Path(upstream)
    config = read_yaml(root / 'config/substore_template.yaml')
    staged = []
    for provider in config['rule-providers'].values():
        relative = rule_path(provider)
        if relative.parts[0] != 'list':
            continue
        source = upstream / 'rule' / 'Clash' / Path(*relative.parts[1:])
        validate_payload(source, provider['behavior'])
        staged.append((source, root / relative))
    # Validate every source before changing any destination; missing/invalid files fail the job.
    for source, destination in staged:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
    print(f'Synced {len(staged)} upstream files; custom/ and unrelated list/ files preserved.')

if __name__ == '__main__':
    sync(sys.argv[1], sys.argv[2])
