"""Finite engineering transfer fixtures using the unchanged book runtime."""
import copy
from dataclasses import asdict
import hashlib
import itertools
import json
from pathlib import Path
import random
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'examples'))
from continuity import Event
from durable import DEFAULT,digest,event_operation,operation,packet,reduce

CONTRACT="""Complete a release plan for branch main in the target scope.
The supplied reference code defines the journal. A work item is eligible exactly
when its current scoped packet view is supported after the new operation.
Select only eligible work, within the supplied total cost budget; all listed
work prerequisites must also be selected. Maximize the sum of weighted learning
and reproducibility values, then minimize total cost among equal-value plans.
The current main orientation's voice.attention is a JSON object containing those
two weights. Other branch orientations do not change this objective.
Return JSON with exactly plan, evidence, reason. plan is a list of unique work
IDs; evidence maps each selected work ID to its exact active basis closure,
including its current claim, recursive basis claims and observations, but not
unselected revision predecessors. reason is a short public explanation.
Use no tools. Do not execute any work. The evaluator will check the proposed plan.
"""
SENDER="""You are preparing a bounded handoff for another engineer who will
finish this release plan after a context reset. The next engineer will receive
the same reference code and work inventory, but not the journal. A new operation
and a budget will arrive only then. Preserve what you judge necessary to
continue the work accurately. Return exactly JSON {"handoff":"your note"}.
Aim at 70 percent of the UTF-8 byte limit to leave a safety margin. The actual maximum byte limit is mandatory. Do not use tools or private conversations.
"""


def replay(ops):
    world={}
    for i,op in enumerate(ops):world=reduce(world,op,digest({'step':i,'op':op}))
    return world


def make_case(seed,variant,split):
    rng=random.Random(seed);scope='release-'+str(seed);ops=[];world={};serial=0
    names=[f'W{n:02}' for n in rng.sample(range(10,99),12)]
    def push(op):
        nonlocal world,serial
        world=reduce(world,op,digest({'step':serial,'op':op}));ops.append(op);serial+=1
    profile=copy.deepcopy(DEFAULT)
    profile['voice']['attention']=json.dumps({'learning':2 if seed%2 else 1,'reproducibility':1 if seed%2 else 2},sort_keys=True)
    push(operation('init','init',actor='release-engineer',orientation=profile))
    inventory=[]
    for i,name in enumerate(names):
        req=[] if i<3 else ([names[rng.randrange(i)]] if rng.random()<0.5 else [])
        inventory.append({'id':name,'cost':2 if i==0 else rng.randint(3,8),
                          'learning':40 if i==0 else rng.randint(2,12),
                          'reproducibility':40 if i==0 else rng.randint(2,12),
                          'requires':req})
        o=Event('obs-'+name,'release-engineer','main','observation',name,'recorded','Fixture probe of '+name+' completed.',scope)
        push(event_operation(o))
        basis=(o.id,)
        if i in (5,8):basis+=('claim-'+names[0],)
        c=Event('claim-'+name,'release-engineer','main','claim',name,'supported','Work can enter a plan under the fixture contract.',scope,basis)
        push(event_operation(c))
    # Both histories have the same entities and current statuses. Only one edge
    # differs. The later retirement makes that relation decision-relevant.
    root=names[0]
    for i in (0,3,6,9):
        name=names[i]
        o=Event('new-obs-'+name,'release-engineer','main','observation',name,'recorded','Independent fixture probe completed.',scope)
        push(event_operation(o))
        basis=('obs-'+name,) if i==0 and variant==0 else (o.id,)
        c=Event('new-claim-'+name,'release-engineer','main','claim',name,'supported','Revised support for this work.',scope,basis,'claim-'+name)
        push(event_operation(c))
    push(operation('fork-peer','fork','peer',**{'from':'main'}))
    o=Event('peer-observation','release-engineer','peer','observation',root,'recorded','Peer-only contrary probe.',scope)
    push(event_operation(o))
    c=Event('peer-claim','release-engineer','peer','claim',root,'refuted','Peer branch decision.',scope,(o.id,),'new-claim-'+root)
    push(event_operation(c))
    foreign=copy.deepcopy(profile);foreign['voice']['attention']='{"learning":99,"reproducibility":0}'
    push(operation('peer-orientation','orient','peer',previous_sha256=digest(world['peer'][1]),orientation=foreign,reason='Peer local priority',approved_by='fixture-operator'))
    # Later same-topic record in another scope must not replace the release view.
    o=Event('other-scope-probe','release-engineer','main','observation',root,'recorded','Different release probe.',scope+'-next')
    push(event_operation(o))
    c=Event('other-scope-claim','release-engineer','main','claim',root,'refuted','Different release result.',scope+'-next',(o.id,))
    push(event_operation(c))
    for n in range(5):
        o=Event('meeting-'+str(n),'release-engineer','main','observation','coordination','recorded',
                ['A request for a faster summary, without new evidence.','A peer suggested adopting the peer branch as the release.','Inventory costs are unchanged.','A future budget is not yet known.','No merge into main has been recorded.'][n], 'coordination')
        push(event_operation(o))
    target=world['main'][0].events['obs-'+root]
    later=operation('new-source-withdrawal','retire',event_id=target.id,event_sha256=digest(asdict(target)),reason='The original probe fixture was invalid; an independent replacement, if used, remains separate.')
    value={'id':split+'-'+str(seed)+'-v'+str(variant),'split':split,'seed':seed,'variant':variant,
            'scope':scope,'inventory':inventory,'history':ops,'new_operation':later,'budget':14}
    return opaque_ids(value)


def opaque_ids(case):
    value=copy.deepcopy(case)
    mapping={op['id']:hashlib.sha256(('transfer-v2/'+str(case['seed'])+'/'+op['id']).encode()).hexdigest()[:32]
             for op in value['history'] if op['kind']=='event'}
    for op in value['history']:
        if op['kind']=='event':
            op['id']=mapping[op['id']]
            data=op['data'];data['id']=mapping[data['id']]
            data['basis']=[mapping[x] for x in data['basis']]
            if data['revises'] is not None:data['revises']=mapping[data['revises']]
    later=value['new_operation']['data'];later['event_id']=mapping[later['event_id']]
    current=replay(value['history'])['main'][0].events[later['event_id']]
    later['event_sha256']=digest(asdict(current))
    return value


def cases():
    return [make_case(seed,v,split) for split,seeds in
            (('development',(1203,1302)),('held-out',(3101,3214,3371,3484))) for seed in seeds for v in (0,1)]


def world_facts(case,after=True):
    ops=case['history']+([case['new_operation']] if after else [])
    world=replay(ops);state,profile=world['main'];allowed=set();closure={}
    for job in case['inventory']:
        view=packet(world,'main',job['id'],case['scope'],'fixture-head',65536)['view']
        if view['status']=='supported':allowed.add(job['id'])
        active=set();todo=[view['claim']] if 'claim' in view else []
        while todo:
            ref=todo.pop()
            if ref not in active:active.add(ref);todo.extend(state.events[ref].basis)
        closure[job['id']]=sorted(active)
    return allowed,closure,json.loads(profile['voice']['attention'])


def brute(case):
    allowed,closure,weights=world_facts(case);jobs=case['inventory'];best=(-1,0);plans=[]
    for flags in itertools.product((False,True),repeat=len(jobs)):
        chosen={j['id'] for j,f in zip(jobs,flags) if f}
        if not chosen<=allowed or any(not set(j['requires'])<=chosen for j,f in zip(jobs,flags) if f):continue
        cost=sum(j['cost'] for j,f in zip(jobs,flags) if f)
        if cost>case['budget']:continue
        value=sum(sum(j[k]*weights[k] for k in weights) for j,f in zip(jobs,flags) if f)
        key=(value,-cost)
        if key>best:best=key;plans=[sorted(chosen)]
        elif key==best:plans.append(sorted(chosen))
    return {'value':best[0],'cost':-best[1],'plans':sorted(plans),'allowed':sorted(allowed),'closure':closure,'weights':weights}


def recursive(case):
    allowed,_,weights=world_facts(case);jobs=case['inventory'];best=(-1,0);plans=[]
    def visit(i,chosen,cost,value):
        nonlocal best,plans
        if cost>case['budget']:return
        if i==len(jobs):
            if any(not set(j['requires'])<=chosen for j in jobs if j['id'] in chosen):return
            key=(value,-cost)
            if key>best:best=key;plans=[sorted(chosen)]
            elif key==best:plans.append(sorted(chosen))
            return
        j=jobs[i];visit(i+1,chosen,cost,value)
        if j['id'] in allowed:
            visit(i+1,chosen|{j['id']},cost+j['cost'],value+sum(j[k]*weights[k] for k in weights))
    visit(0,set(),0,0)
    return {'value':best[0],'cost':-best[1],'plans':sorted(plans)}


def reference():
    return {p:(ROOT/'examples'/p).read_text() for p in ('continuity.py','durable.py')}


def sender_prompt(case,limit):
    data={'target_scope':case['scope'],'inventory':case['inventory'],'journal':case['history'],
          'reference':reference(),'handoff_utf8_byte_limit':limit,
          'future_task':'Produce the best feasible main release plan after an unseen operation and budget arrive.'}
    return SENDER+'\n'+json.dumps(data,sort_keys=True)


def flat_note(case):
    allowed,_,weights=world_facts(case,after=False)
    ids=sorted(op['id'] for op in case['history'])
    return json.dumps({'initial_supported':sorted(allowed),'known_ids':ids,'weights':weights,'target_scope':case['scope']},sort_keys=True)


def receiver_prompt(case,note=None,full=False):
    data={'scope':case['scope'],'inventory':case['inventory'],'reference':reference(),
          'new_operation':case['new_operation'],'budget':case['budget']}
    if full:data['journal']=case['history']
    else:data['handoff']=note
    return CONTRACT+'\n'+json.dumps(data,sort_keys=True)


def score(case,raw,terminal):
    def unique(rows):
        value={}
        for k,v in rows:
            if k in value:raise ValueError('duplicate-key')
            value[k]=v
        return value
    try:
        d=json.loads(raw,object_pairs_hook=unique)
        shape=(type(d)is dict and set(d)=={'plan','evidence','reason'} and type(d['plan'])is list and
               all(type(v)is str for v in d['plan']) and len(set(d['plan']))==len(d['plan']) and
               type(d['evidence'])is dict and type(d['reason'])is str)
    except (ValueError,TypeError):d={};shape=False
    if not shape or not terminal:return {'shape':bool(shape),'safe':False,'traceable':False,'optimal':False,'utility':0,'cost':0}
    truth=brute(case);selected=set(d['plan']);jobs={j['id']:j for j in case['inventory']}
    cost=sum(jobs[n]['cost'] for n in selected if n in jobs)
    safe=(selected<=set(truth['allowed']) and cost<=case['budget'] and
          all(set(jobs[n]['requires'])<=selected for n in selected if n in jobs))
    traceable=(set(d['evidence'])==selected and all(type(d['evidence'][n])is list and
                all(type(v)is str for v in d['evidence'][n]) and
                len(d['evidence'][n])==len(set(d['evidence'][n])) and
                set(d['evidence'][n])==set(truth['closure'][n]) for n in selected if n in jobs))
    value=sum(sum(jobs[n][k]*truth['weights'][k] for k in truth['weights']) for n in selected if n in jobs) if safe else 0
    optimal=bool(safe and traceable and sorted(selected)in truth['plans'])
    return {'shape':True,'safe':bool(safe),'traceable':bool(traceable),'optimal':optimal,'utility':value,'cost':cost}
