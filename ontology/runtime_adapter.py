"""Project the actual finite participation runtime's records into the public ontology.

No study oracle, optimal planner, provider call or external effect. Actor and
permission labels remain caller assertions. Only store.read() local effect rows
are marked observed; the projection is not proof of real-world delivery.
"""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys

EXAMPLES = Path(__file__).resolve().parents[1] / 'examples'
if str(EXAMPLES) not in sys.path:
    sys.path.insert(0, str(EXAMPLES))
from participation import ParticipationStore, interpret, validate as validate_world
from durable import digest
from graph import InvalidGraph, answer, load, validate


def _ident(kind, value):
    return kind + ':' + digest(value)[:32]


def _project(world, stored=None, readback=None):
    validate_world(world)
    view = interpret(world)  # Actual runtime consumer, not the independent study oracle.
    nodes, edges = {}, set()
    world_sha = digest(world)
    def add(ident, node_type, **data):
        value = {'id': ident, 'type': node_type, 'data': {'label': ident, **data}}
        if ident in nodes and nodes[ident] != value:
            raise InvalidGraph('adapter ID collision')
        nodes[ident] = value
        return ident
    def edge(source, relation, target):
        edges.add((source, relation, target))
    def actor(value):
        # The input supplies a participant label, not authenticated identity/type.
        return add(_ident('actor', value), 'Actor', label='Caller-supplied participant '+value, kind='unknown')
    def scope(value):
        return add(_ident('scope', value), 'Scope', description=json.dumps({'callerScope':value},sort_keys=True))
    def value_record(ident, ref, label, value, availability='available'):
        content=json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'))
        if len(content)<=8000:
            return add(ident,'Observation',label=label,sourceRef=ref,availability=availability,content=content)
        chunks=[content[i:i+1000] for i in range(0,len(content),1000)]
        anchor=add(ident,'Observation',label=label,sourceRef=ref,availability=availability,
                   content=json.dumps({'encoding':'json-text-chunks','parts':len(chunks),'value_sha256':digest(value)},sort_keys=True))
        for i,chunk in enumerate(chunks):
            part=add(_ident('chunk',[ident,i]),'Observation',label=label+' chunk '+str(i),
                     sourceRef=ref+'/chunk/'+str(i),availability=availability,
                     content=json.dumps({'part':i,'parts':len(chunks),'chunk':chunk},ensure_ascii=False,sort_keys=True))
            edge(anchor,'describedBy',part)
        return anchor
    def source(pointer, value, availability='available', label=None):
        return value_record(_ident('source',[world_sha,pointer]),'world:sha256:'+world_sha+'#'+pointer,
                            label or ('Caller-supplied world record '+pointer),value,availability)
    current_scope = scope(world['scope'])
    current_actor = actor(world['actor'])
    # The adapter has invoked this actual function locally; its output is not a world-truth oracle.
    interpreter = add('actor:participation-interpreter', 'Actor', kind='software')
    caller = add('actor:world-caller', 'Actor', label='Unidentified caller asserting world fields', kind='unknown')
    raw = {}
    for key, value in world.items():
        if isinstance(value, list):
            if not value:raw[(key,None)] = source('/'+key,[])
            for i, row in enumerate(value):
                raw[(key,i)] = source('/'+key+'/'+str(i),row)
        else:
            raw[(key,None)] = source('/'+key,value)
    records = {}
    for i,row in enumerate(world['records']):
        ident = _ident('record',row['id']); records[row['id']] = ident
        own_scope = scope(row['scope'])
        if row['kind'] == 'observation':
            add(ident,'Observation',label='Supplied observation record '+row['id'],sourceRef='world:sha256:'+world_sha+'#/records/'+str(i),
                availability='withdrawn' if row['id'] in world['withdrawn'] else 'available',content=json.dumps(row,sort_keys=True))
        elif row['kind'] == 'claim':
            add(ident,'Claim',text=json.dumps(row,sort_keys=True),status='needs-review' if row['id'] in view['withdrawal_paths'] else 'proposed')
            edge(ident,'inScope',own_scope)
        else:
            # The world gives neither the original action text nor its execution/session identity.
            # Keep it unconfirmed rather than inventing a model, profile, run or successful action.
            add(ident,'Decision',action='Unspecified supplied decision '+row['id'],actionStatus='unconfirmed',rationale='Caller-supplied dependency record, not an observed action witness.')
            edge(ident,'inScope',own_scope)
        edge(ident,'describedBy',raw[('records',i)])
    for row in world['records']:
        for basis in row['basis']:
            edge(records[row['id']],'dependsOn',records[basis])
    criteria = {}
    update = world['criterion_update']
    for i,c in enumerate(world['criteria']):
        ident=_ident('criterion',c['id']);criteria[c['id']]=ident
        # Only the new criterion has an explicit acceptance flag. The old criterion
        # is current by default, but the world contains no separate adoption event.
        accepted=c['id']==update['new'] and update['accepted']
        add(ident,'Criterion',version=c['id'],acceptance='accepted' if accepted else ('proposed' if c['id']==update['new'] else 'unknown'))
        edge(ident,'inScope',current_scope);edge(ident,'describedBy',raw[('criteria',i)])
        edge(ident,'describedBy',raw[('criterion_update',None)])
        if accepted:edge(ident,'acceptedBy',caller)
        if accepted and update['authorized']:
            warrant=add(_ident('authority',['criterion',c['id']]),'Authority',actionKind='adopt-criterion')
            edge(warrant,'heldBy',caller);edge(warrant,'grantedBy',caller);edge(warrant,'inScope',current_scope)
            edge(warrant,'describedBy',raw[('criterion_update',None)]);edge(ident,'governedBy',warrant)
        assessment=add(_ident('assessment',c['id']),'Assessment',result={'met':'satisfied','lost':'violated','unknown':'unknown'}[view['assessments'][c['id']]],
                       rationale='Copied from participation.interpret(world), using caller-supplied measurements; not truth certification.')
        edge(assessment,'inScope',current_scope);edge(assessment,'evaluates',current_scope);edge(assessment,'underCriterion',ident)
        edge(assessment,'attributedTo',interpreter)
        measurement=world['measurements'][c['metric']]
        evidence=source('/measurements/'+c['metric'],measurement,'missing' if measurement is None else 'available',
                        'Caller-supplied measurement '+c['metric']+'; None means no measurement')
        edge(assessment,'supportedBy',evidence)
    candidates={c['id']:_ident('candidate',c['id']) for c in world['candidates']}
    applicability={a['id']:a for a in view['candidate_applicability']}
    for i,c in enumerate(world['candidates']):
        ident=candidates[c['id']]
        add(ident,'ActionCandidate',kind=c['kind'],channel=c['channel'],cost=c['cost'],benefit=c['benefit'],effectId=c['effect_id'])
        edge(ident,'inScope',current_scope);edge(ident,'candidateTarget',records[c['target']]);edge(ident,'recipient',actor(c['recipient']))
        edge(ident,'describedBy',raw[('candidates',i)])
        for b in c['basis']:edge(ident,'candidateBasis',records[b])
        for r in c['requires']:edge(ident,'requiresCandidate',candidates[r])
        row=applicability[c['id']]
        aid=add(_ident('applicability',c['id']),'Applicability',result='applies' if row['applicable'] else 'does-not-apply',
                reason=json.dumps(row,sort_keys=True))
        edge(aid,'inScope',current_scope);edge(aid,'appliesRecord',ident);edge(aid,'attributedTo',interpreter)
        edge(aid,'supportedBy',raw[('candidates',i)])
    for i,objection in enumerate(world['open_objections']):
        oid=add(_ident('objection',objection),'Objection',label='Caller-supplied unresolved objection '+str(objection),
                text='Only the objection ID is supplied: '+str(objection),status='open')
        edge(oid,'inScope',current_scope);edge(oid,'describedBy',raw[('open_objections',i)])
    warrants={}
    for i,permission in enumerate(world['permissions']):
        if not permission['allowed']:continue
        key=(permission['recipient'],permission['channel'],permission['scope'])
        aid=add(_ident('authority',['action',key]),'Authority',actionKind='execute-action')
        edge(aid,'inScope',scope(permission['scope']));edge(aid,'heldBy',current_actor);edge(aid,'grantedBy',caller)
        edge(aid,'describedBy',raw[('permissions',i)]);warrants[key]=aid
    # History/delivery/permission/cost/benefit inputs remain exact source records.
    # In particular no prior history effect becomes an observed receipt merely by export.
    if stored is not None:
        did=add(_ident('turn',stored['turn_id']),'Decision',action=json.dumps((stored.get('answer') or {}).get('plan'),sort_keys=True),
                actionStatus='executed' if stored['effects'] else ('withheld' if stored['admission']=='admitted' else 'unconfirmed'),
                rationale='Actual locally read-back controller turn; selected plan may be rejected, empty or incomplete.')
        edge(did,'inScope',current_scope);edge(did,'madeBy',current_actor)
        selected=(stored.get('answer') or {}).get('current_criterion')
        if selected in criteria:edge(did,'withCriterion',criteria[selected])
        read=value_record(_ident('readback',stored['turn_id']),
                 'journal-head:sha256:'+readback['head']+';turn:sha256:'+digest(stored),
                 'Actual ParticipationStore.read() local readback, not external delivery',
                 {'turn_id':stored['turn_id'],'stored_sha256':digest(stored),'world_sha256':stored['world_sha256'],
                     'admission':stored['admission'],'terminal':stored['terminal'],'effects':stored['effects']})
        edge(did,'describedBy',read)
        # Explicit nonempty observed rows only: zero does not create a successful Effect node.
        selected_candidates={c['effect_id']:c for c in world['candidates']}
        for effect in stored['effects']:
            eid=add(_ident('effect',[stored['turn_id'],effect['effect_id']]),'Effect',description=json.dumps(effect,sort_keys=True),state='observed')
            edge(did,'hasEffect',eid);edge(eid,'affects',actor(effect['recipient']));edge(eid,'describedBy',read)
            edge(read,'observesEffect',eid)
            c=selected_candidates.get(effect['effect_id'])
            if c is not None:
                warrant=warrants.get((c['recipient'],c['channel'],world['scope']))
                if warrant is not None:edge(did,'governedBy',warrant)
        # Preserve all remaining turn fields, including model response, without
        # pretending their statements were observed actions or effects.
        for field in ('turn_id','world_sha256','answer','response','terminal','admission'):
            sid=value_record(_ident('turn-source',[stored['turn_id'],field]),
                    'turn:sha256:'+digest(stored)+'#/'+field,'Read-back controller field '+field,stored[field])
            edge(did,'describedBy',sid)
    graph={'nodes':sorted(nodes.values(),key=lambda n:n['id']),
           'edges':[{'source':a,'relation':b,'target':c} for a,b,c in sorted(edges)]}
    return validate(graph)


def world_graph(world):
    """Caller-supplied world + actual interpreter output; no stored effects inferred."""
    return _project(deepcopy(world))


def stored_graph(store, turn_id):
    """Read through the real store, bind its exact world, project local effect rows."""
    if not isinstance(store,ParticipationStore):
        raise InvalidGraph('ParticipationStore required')
    values,tail=store.read()
    matches=[value for value in values if value['turn_id']==turn_id]
    if len(matches)!=1:raise InvalidGraph('exact stored turn not found')
    stored=matches[0]
    if stored['world_sha256']!=digest(stored['world']):raise InvalidGraph('stored world digest mismatch')
    return _project(stored['world'],stored,tail)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    source=p.add_mutually_exclusive_group(required=True)
    source.add_argument('--world');source.add_argument('--store')
    p.add_argument('--turn-id');p.add_argument('--question')
    args=p.parse_args()
    if args.store:
        if not args.turn_id:p.error('--store requires --turn-id')
        graph=stored_graph(ParticipationStore(args.store),args.turn_id)
    else:graph=world_graph(load(args.world))
    print(json.dumps(answer(graph,args.question) if args.question else graph,ensure_ascii=False,sort_keys=True,indent=2))


if __name__=='__main__':main()
