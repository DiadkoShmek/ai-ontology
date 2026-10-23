"""Finite participation queries and closed-loop local receipts.

Trusted caller supplies typed records, permissions and meaning. No semantic
entailment, authenticated authority, hidden-state inference or external send.
The generic query result is an engineering intervention, not a model oracle.
"""
from __future__ import annotations
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from continuity import Event
from durable import DEFAULT, ZERO, Hold, Journal, canonical, digest, event_operation, operation

LIMIT = 256


def require(ok, message):
    if not ok:
        raise Hold(message)


def validate(world):
    require(type(world) is dict and set(world) == {
        'actor', 'scope', 'records', 'withdrawn', 'deliveries', 'permissions',
        'criteria', 'criterion_update', 'measurements', 'candidates', 'budget',
        'history', 'open_objections'}, 'world-shape')
    require(type(world['budget']) is int and 0 <= world['budget'] <= 100, 'budget')
    require(all(type(world[k]) is list and len(world[k]) <= LIMIT for k in
                ('records','withdrawn','deliveries','permissions','criteria','candidates','history','open_objections')), 'world-size')
    for key in ('actor','scope'):
        require(type(world[key]) is str and 0 < len(world[key]) <= 128, 'world-identity')
    nodes = {}
    for row in world['records']:
        require(type(row) is dict and set(row) == {'id','kind','scope','basis'}, 'record-shape')
        require(type(row['id']) is str and 0 < len(row['id']) <= 128 and row['id'] not in nodes, 'record-id')
        require(row['kind'] in ('observation','claim','decision'), 'record-kind')
        require(type(row['scope']) is str and row['scope'], 'record-scope')
        require(type(row['basis']) is list and len(set(row['basis'])) == len(row['basis']), 'basis-shape')
        require(all(type(x) is str and x in nodes for x in row['basis']), 'basis-missing-or-not-topological')
        require(row['kind'] != 'observation' or not row['basis'], 'observation-basis')
        nodes[row['id']] = row
    require(len(set(world['withdrawn'])) == len(world['withdrawn']) and all(x in nodes for x in world['withdrawn']), 'withdrawn-reference')
    for d in world['deliveries']:
        require(set(d) == {'id','decision','recipient','scope','origin_effect'}, 'delivery-shape')
        require(d['decision'] in nodes and nodes[d['decision']]['kind'] == 'decision', 'delivery-decision')
    ids = set()
    for c in world['candidates']:
        require(set(c) == {'id','kind','target','recipient','channel','basis','cost','benefit','requires','effect_id'}, 'candidate-shape')
        require(type(c['id']) is str and c['id'] and c['id'] not in ids, 'candidate-id')
        require(c['kind'] in ('publish','correct','quarantine'), 'candidate-kind')
        require(type(c['cost']) is int and 0 < c['cost'] <= 100, 'candidate-cost')
        require(type(c['benefit']) is int and 0 <= c['benefit'] <= 100, 'candidate-benefit')
        require(c['target'] in nodes and type(c['basis']) is list and all(x in nodes for x in c['basis']), 'candidate-reference')
        require(type(c['requires']) is list and len(set(c['requires'])) == len(c['requires']), 'candidate-requires')
        ids.add(c['id'])
    require(all(set(c['requires']) <= ids and c['id'] not in c['requires'] for c in world['candidates']), 'candidate-prerequisite')
    require(len({d['id'] for d in world['deliveries']}) == len(world['deliveries']), 'duplicate-delivery')
    require(len({c['effect_id'] for c in world['candidates']}) == len(world['candidates']), 'duplicate-effect-id')
    criteria = {c['id']: c for c in world['criteria']}
    require(len(criteria) == len(world['criteria']) and len(criteria) >= 2, 'criteria')
    for c in criteria.values():
        require(set(c) == {'id','metric','minimum'}, 'criterion-shape')
        require(type(c['minimum']) is int and c['metric'] in world['measurements'], 'criterion-value')
    u = world['criterion_update']
    require(set(u) == {'old','new','accepted','authorized'}, 'criterion-update')
    require(u['old'] in criteria and u['new'] in criteria and type(u['accepted']) is bool and type(u['authorized']) is bool, 'criterion-reference')
    for p in world['permissions']:
        require(set(p) == {'recipient','channel','scope','allowed'}, 'permission-shape')
        require(type(p['allowed']) is bool, 'permission-boolean')
    require(len({(p['recipient'],p['channel'],p['scope']) for p in world['permissions']}) == len(world['permissions']), 'permission-conflict')
    for h in world['history']:
        require(set(h) == {'effect_id','actor','kind','target','recipient','scope','plan_id'}, 'history-shape')
    return nodes


def ancestors(world):
    nodes = validate(world)
    result = {}
    for row in world['records']:
        reach = {row['id']}
        for parent in row['basis']:
            reach.update(result[parent])
        result[row['id']] = reach
    return nodes, result


def interpret(world):
    """Expose derivation witnesses, not an optimal plan or a gold response."""
    nodes, reach = ancestors(world)
    withdrawn = set(world['withdrawn'])
    scope = world['scope']
    invalid = {i: sorted(r & withdrawn) for i,r in reach.items() if r & withdrawn}
    affected = sorted(i for i in invalid if nodes[i]['kind'] == 'decision' and nodes[i]['scope'] == scope)
    deliveries = [d for d in world['deliveries'] if d['decision'] in affected and d['scope'] == scope]
    permissions = {(p['recipient'],p['channel'],p['scope']): p['allowed'] for p in world['permissions']}
    table = []
    for c in world['candidates']:
        errors = []
        if nodes[c['target']]['scope'] != scope: errors.append('target-outside-scope')
        if any(x in invalid for x in c['basis']): errors.append('withdrawn-basis')
        if any(nodes[x]['scope'] != scope for x in c['basis']): errors.append('basis-outside-scope')
        if c['kind'] == 'publish':
            if c['target'] in invalid: errors.append('target-needs-review')
        else:
            if c['target'] not in affected: errors.append('target-not-affected')
            if c['kind'] == 'correct' and not any(d['decision']==c['target'] and d['recipient']==c['recipient'] for d in deliveries):
                errors.append('no-affected-delivery-to-recipient')
        if not permissions.get((c['recipient'],c['channel'],scope),False):
            errors.append('channel-not-authorized')
        table.append({'id':c['id'],'applicable':not errors,'reasons':errors,
                      'basis_paths':{x:sorted(reach[x]) for x in c['basis']},
                      'requires':list(c['requires'])})
    criteria = {c['id']:c for c in world['criteria']}
    assessments = {}
    for i,c in criteria.items():
        observed = world['measurements'][c['metric']]
        assessments[i] = 'unknown' if observed is None else ('met' if observed>=c['minimum'] else 'lost')
    update = world['criterion_update']
    current = update['new'] if update['accepted'] and update['authorized'] else update['old']
    responsibility = sorted({d['origin_effect'] for d in deliveries if any(
        h['effect_id']==d['origin_effect'] and h['actor']==world['actor'] for h in world['history'])})
    return {'affected_decisions':affected,'affected_deliveries':deliveries,
            'withdrawal_paths':invalid,'candidate_applicability':table,
            'current_criterion':current,'assessments':assessments,
            'own_prior_effects':responsibility,'open_objections':deepcopy(world['open_objections'])}


def admissible(world, plan):
    """Common controller in both arms. No utility or oracle check at admission."""
    view = interpret(world)
    require(type(plan) is list and len(plan)<=LIMIT and all(type(x)is str for x in plan), 'plan-shape')
    require(len(set(plan)) == len(plan), 'duplicate-plan-action')
    indexed = {c['id']:c for c in world['candidates']}
    require(set(plan)<=indexed.keys(), 'unknown-action')
    status = {x['id']:x['applicable'] for x in view['candidate_applicability']}
    require(all(status[x] for x in plan), 'inapplicable-action')
    require(all(set(indexed[x]['requires'])<=set(plan) for x in plan), 'missing-prerequisite')
    require(len({(indexed[x]['target'],indexed[x]['recipient']) for x in plan})==len(plan), 'duplicate-target-recipient')
    require(sum(indexed[x]['cost'] for x in plan)<=world['budget'], 'plan-over-budget')
    return [indexed[x] for x in sorted(plan)]


class ParticipationStore:
    """Reuse the existing SQLite/CAS journal; no parallel persistence engine.

    Records an entire bounded controller result atomically as one observation.
    It has no real-world delivery, authority-authentication or semantic oracle.
    """
    def __init__(self, path, *, create=False):
        self.journal = Journal(path,create=create)
        if create:
            self.journal.append(operation('participation-genesis','init',actor='participant',orientation=DEFAULT),expected=ZERO)

    def read(self):
        world, tail = self.journal.read()
        values = [json.loads(e.text) for e in world['main'][0].events.values()]
        return values, tail

    def _append(self, turn_id, world, answer, effects, response, terminal, admission, expected):
        body = {'turn_id':turn_id,'world_sha256':digest(world),'answer':deepcopy(answer),
                'effects':effects,'world':deepcopy(world),'response':response,
                'terminal':terminal,'admission':admission}
        raw = canonical(body)
        require(len(raw)<=60000,'turn-too-large')
        values, tail = self.read()
        prior = next((v for v in values if v['turn_id']==turn_id),None)
        if prior is not None:
            require(prior==body,'turn-id-collision')
        else:
            require(tail['head']==expected,'stale-head')
            emitted={e['effect_id'] for v in values for e in v['effects']}
            require(not emitted.intersection(e['effect_id'] for e in effects),'effect-already-recorded')
        e = Event(turn_id,'participant','main','observation','participation',
                  'recorded',raw.decode(),'simulation',origin='controller')
        receipt = self.journal.append(event_operation(e),expected=expected)
        values, tail = self.read()
        require(any(v==body for v in values),'effect-readback-missing')
        return {'receipt':receipt,'effects':effects,'stored_sha256':digest(body),
                'committed':admission=='admitted','admission':admission,
                'scope':'local-simulated-effects-only'}

    def commit(self, turn_id, world, answer, *, expected):
        rows = admissible(world,answer['plan'])
        effects = [{'effect_id':c['effect_id'],'actor':world['actor'],'kind':c['kind'],
                    'target':c['target'],'recipient':c['recipient'],'scope':world['scope'],
                    'plan_id':turn_id} for c in rows]
        return self._append(turn_id,world,answer,effects,'',True,'admitted',expected)

    def record_turn(self,turn_id,world,answer,*,response,terminal,expected):
        """Keep rejected attempts in the SAME durable history, without effects."""
        # Full raw output remains in the caller's raw archive. Continuity has
        # an explicit unavailable marker for outputs outside its wire limit.
        # This is a documented rejection, never an invisible prefix truncation.
        try:
            raw_response=response.encode('utf-8')
            valid_utf8=True
        except UnicodeError:
            raw_response=response.encode('utf-8',errors='backslashreplace')
            valid_utf8=False
        if not valid_utf8 or len(raw_response)>16384:
            response=canonical({'continuity_delivery':'not-delivered',
                'reason':'invalid-utf8' if not valid_utf8 else 'response-over-wire-limit',
                'raw_sha256':hashlib.sha256(raw_response).hexdigest(),
                'raw_bytes':len(raw_response),'raw_location':'cohort responses archive'}).decode()
            answer=None
        effects=[];admission='invalid-or-incomplete'
        if answer is not None and terminal:
            try:
                rows=admissible(world,answer['plan'])
                effects=[{'effect_id':c['effect_id'],'actor':world['actor'],'kind':c['kind'],
                          'target':c['target'],'recipient':c['recipient'],'scope':world['scope'],
                          'plan_id':turn_id} for c in rows]
                admission='admitted'
            except Hold as exc:admission=str(exc)
        return self._append(turn_id,world,answer,effects,response,terminal,admission,expected)

    def context(self):
        """Reconstruct current continuity only from durable readback."""
        values,tail=self.read();previous=[];effects=[]
        for v in values:
            previous.append({'stage':int(v['turn_id'].removeprefix('turn-')),
                             'response':v['response'],
                             'actual_controller_effect':{'effects':v['effects'],
                               'committed':v['admission']=='admitted','admission':v['admission'],
                               'stored_sha256':digest(v)}})
            effects.extend(v['effects'])
        return previous,effects,tail
