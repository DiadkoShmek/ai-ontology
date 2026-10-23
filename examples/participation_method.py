"""Bounded declarative working methods. No eval, tools, oracle or learned weights."""
from __future__ import annotations
from time import perf_counter
from participation import Hold,ancestors,require,digest

BOOL_FIELDS={'target_in_scope','basis_in_scope','basis_clear','target_clear',
             'target_affected','recipient_has_affected_delivery','channel_allowed'}
FIELDS=BOOL_FIELDS|{'kind'}


def validate_method(m):
    require(type(m)is dict and set(m)=={'default','rules'},'method-shape')
    require(type(m['default'])is str and m['default'] in ('allow','deny'),'method-default')
    require(type(m['rules'])is list and len(m['rules'])<=8,'method-rules')
    for rule in m['rules']:
        require(type(rule)is dict and set(rule)=={'all','decision'},'method-rule')
        require(type(rule['decision'])is str and rule['decision'] in ('allow','deny'),'method-decision')
        require(type(rule['all'])is list and len(rule['all'])<=8,'method-atoms')
        used=set()
        for atom in rule['all']:
            require(type(atom)is dict and set(atom)=={'field','equals'},'method-atom')
            f=atom['field'];v=atom['equals']
            require(type(f)is str and f in FIELDS and f not in used,'method-field')
            require((type(v)is bool) if f in BOOL_FIELDS else (type(v)is str and v in ('publish','correct','quarantine')),'method-value')
            used.add(f)
    return m


def predicate_rows(world):
    nodes,reach=ancestors(world);withdrawn=set(world['withdrawn']);scope=world['scope']
    bad={i for i,r in reach.items() if r&withdrawn}
    permissions={(p['recipient'],p['channel'],p['scope']) for p in world['permissions'] if p['allowed']}
    deliveries={(d['decision'],d['recipient']) for d in world['deliveries'] if d['scope']==scope and d['decision'] in bad}
    return {c['id']:{'kind':c['kind'],
        'target_in_scope':nodes[c['target']]['scope']==scope,
        'basis_in_scope':all(nodes[x]['scope']==scope for x in c['basis']),
        'basis_clear':all(x not in bad for x in c['basis']),
        'target_clear':c['target'] not in bad,
        'target_affected':c['target'] in bad and nodes[c['target']]['scope']==scope and nodes[c['target']]['kind']=='decision',
        'recipient_has_affected_delivery':(c['target'],c['recipient']) in deliveries,
        'channel_allowed':(c['recipient'],c['channel'],scope) in permissions}
        for c in world['candidates']}


def allows(method,fields):
    validate_method(method)
    for rule in method['rules']:
        if all(type(fields[a['field']])is type(a['equals']) and fields[a['field']]==a['equals'] for a in rule['all']):
            return rule['decision']=='allow'
    return method['default']=='allow'


def select_plan(world,method):
    """Shared optimizer consumes METHOD eligibility, never gold eligibility."""
    started=perf_counter();validate_method(method);facts=predicate_rows(world)
    require(len(world['candidates'])<=20,'method-candidate-limit')
    rows=[c for c in world['candidates'] if allows(method,facts[c['id']])]
    best=(0,0,())
    def visit(i,chosen,cost,benefit,targets):
        nonlocal best
        if cost>world['budget']:return
        if i==len(rows):
            ids={c['id'] for c in chosen}
            if any(not set(c['requires'])<=ids for c in chosen):return
            rank=(-benefit,cost,tuple(sorted(ids)))
            if rank<best:best=rank
            return
        c=rows[i];visit(i+1,chosen,cost,benefit,targets)
        target=(c['target'],c['recipient'])
        if target not in targets:visit(i+1,chosen+[c],cost+c['cost'],benefit+c['benefit'],targets|{target})
    visit(0,[],0,0,set())
    return {'plan':list(best[2]),'proposed_benefit':-best[0],'cost':best[1],
            'method_sha256':digest(method),'predicate_sha256':digest(facts),
            'method_eligible':sorted(c['id'] for c in rows),
            'wall_ms':round((perf_counter()-started)*1000,3)}


def reference_method():
    """Authored rule fixture for tests ONLY. Never injected into model targets."""
    common=[{'field':x,'equals':True} for x in ['target_in_scope','basis_in_scope','basis_clear','channel_allowed']]
    rules=[]
    for kind in ['publish','correct','quarantine']:
        atoms=common+[{'field':'kind','equals':kind}]
        atoms+=[{'field':'target_clear' if kind=='publish' else 'target_affected','equals':True}]
        if kind=='correct':atoms+=[{'field':'recipient_has_affected_delivery','equals':True}]
        rules.append({'all':atoms,'decision':'allow'})
    return {'default':'deny','rules':rules}
