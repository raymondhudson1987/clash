"""Validate template references and rule payloads before publishing updates."""
import ipaddress
import sys
from pathlib import Path
from urllib.parse import urlparse

import yaml

class UniqueLoader(yaml.SafeLoader):
    pass

def mapping(loader, node, deep=False):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise ValueError(f'duplicate YAML key: {key}')
        result[key] = loader.construct_object(value_node, deep=deep)
    return result

UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, mapping)

def read_yaml(path):
    return yaml.load(Path(path).read_text(encoding='utf-8-sig'), Loader=UniqueLoader)

def rule_path(provider):
    u = urlparse(provider['url'])
    prefix = '/raymondhudson1987/clash/main/'
    assert u.scheme == 'https' and u.netloc == 'raw.githubusercontent.com'
    assert u.path.startswith(prefix), provider['url']
    p = Path(u.path[len(prefix):])
    assert p.parts[0] in ('list', 'custom') and '..' not in p.parts
    return p

def validate_payload(path, behavior):
    doc = read_yaml(path)
    assert isinstance(doc, dict) and isinstance(doc.get('payload'), list), path
    assert doc['payload'], f'empty upstream payload: {path}'
    for rule in doc['payload']:
        assert isinstance(rule, str) and rule.strip(), path
        assert '<html' not in rule.lower(), path
        if behavior == 'ipcidr':
            ipaddress.ip_network(rule, strict=False)
        elif behavior == 'domain':
            assert ',' not in rule, (path, rule)
        else:
            assert ',' in rule and not rule.startswith(('MATCH,', 'RULE-SET,')), (path, rule)
    return len(doc['payload'])

def check(root):
    root = Path(root)
    c = read_yaml(root / 'config/substore_template.yaml')
    assert c['mode'] == 'rule' and c['tun']['enable'] is False
    groups = {g['name']: g for g in c['proxy-groups']}
    assert len(groups) == len(c['proxy-groups'])
    targets = set(groups) | {'DIRECT', 'REJECT'}
    for group in groups.values():
        assert 'dialer-proxy' not in group
        assert all(p in targets for p in group.get('proxies', [])), group['name']
    assert groups['全球直连']['proxies'] == ['DIRECT']
    providers = c['rule-providers']
    cache_paths = [p['path'] for p in providers.values()]
    assert len(cache_paths) == len(set(cache_paths))
    total = 0
    for name, p in providers.items():
        assert p['proxy'] in targets, name
        total += validate_payload(root / rule_path(p), p['behavior'])
    rules = c['rules']
    assert rules[:2] == ['IP-CIDR,192.168.5.13/32,DIRECT,no-resolve', 'IP-CIDR,192.168.5.33/32,DIRECT,no-resolve']
    assert rules[-1] == 'MATCH,漏网之鱼'
    for rule in rules:
        fields = rule.split(',')
        target = fields[-2] if fields[-1] == 'no-resolve' else fields[-1]
        assert target in targets, rule
        if fields[0] == 'RULE-SET':
            assert fields[1] in providers, rule
    for n in ('ChinaMedia', 'ChinaMaxDomain', 'ChinaMaxIP', 'SteamCN'):
        assert f'RULE-SET,{n},DIRECT' in rules
    assert rules.index('RULE-SET,ManualAdjust,节点选择') < rules.index('RULE-SET,ChinaMaxDomain,DIRECT')
    assert rules.index('RULE-SET,YouTube,油管视频') < rules.index('RULE-SET,Google,谷歌')
    print(f'Validated {len(providers)} providers, {len(rules)} routes, {total} payload entries.')

if __name__ == '__main__':
    check(sys.argv[1] if len(sys.argv) > 1 else '.')
