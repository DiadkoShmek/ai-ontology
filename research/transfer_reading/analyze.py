"""Offline reconstruction and predeclared paired descriptive analysis."""
import gzip
import hashlib
import itertools
import json
from pathlib import Path
import statistics
import tempfile
from study import (ARMS,HERE,READINGS,artifact,field,held_cases,pins,planning_success,
                   prepared_sender_prompt,prime_prompt,receiver_prompt,schedule,
                   score,sha,stored_note,brute)


def require(value,reason):
    if not value:raise ValueError(reason)


def terminal(row):
    return bool(any(e.get('type')=='turn.completed' for e in row['events']) and row.get('exit_code')==0 and
                not row['tools'] and not row.get('unparsed_stdout') and
                not any(e.get('type')in('turn.failed','error') for e in row['events']))


def quantile(values,p):
    values=sorted(values);at=(len(values)-1)*p;left=int(at);fraction=at-left
    return values[left]*(1-fraction)+values[min(left+1,len(values)-1)]*fraction


def derive():
    frozen=json.loads((HERE/'freeze.json').read_text())
    require(frozen['input_sha256']==pins(),'source drift')
    require(frozen['schedule']==schedule(),'schedule drift')
    raw=gzip.decompress((HERE/'responses.jsonl.gz').read_bytes())
    if (HERE/'responses.jsonl').exists():require(raw==(HERE/'responses.jsonl').read_bytes(),'archive/raw mismatch')
    complete=json.loads((HERE/'completion.json').read_text())
    require(complete['raw_sha256']==sha(raw),'raw hash mismatch')
    require(complete['freeze_sha256']==sha((HERE/'freeze.json').read_bytes()),'freeze drift')
    require(complete['source_unchanged'] and complete['input_pins_after']==frozen['input_sha256'],'execution source drift')
    records=json.loads((HERE/'episodes.json').read_text())
    require(sha((HERE/'episodes.json').read_bytes())==complete['episodes_sha256'],'episode archive drift')
    rows=[json.loads(x) for x in raw.splitlines()]
    keys={(r['case'],r['arm'],r['repetition'],r['stage']):r for r in rows}
    require(len(keys)==len(rows)==complete['captured_calls'] and len(rows)<=200,'call coverage/duplicate')
    cs={c['id']:c for c in held_cases()};readings={'ordinary':'',**{a:(HERE/p).read_text() for a,p in READINGS.items()}}
    require(json.loads((HERE/'cases.json').read_text())==[{'source':c,'oracle':brute(c)} for c in held_cases()],'case drift')
    consumed=set()
    def row(cid,a,rep,stage,prompt):
        k=cid,a,rep,stage;require(k in keys,'missing expected stage');r=keys[k];consumed.add(k)
        require(r['prompt']==prompt and r['prompt_sha256']==sha(prompt.encode()),'prompt/history drift')
        require(r['terminal']==terminal(r),'terminal metadata drift')
        return r
    def finish(c,r,folder):
        evaluated=score(c,r['response'],r['terminal']);effect={'written':False}
        if evaluated['safe']:
            plan=json.loads(r['response'])['plan'];body=json.dumps({'case':c['id'],'plan':plan},sort_keys=True).encode()
            effect={'written':True,**artifact(folder,'plan.json',body),'plan':plan}
        return {'score':evaluated,'primary':planning_success(evaluated,c),'plan_effect':effect}
    require({r['case'] for r in records['controls']}==set(cs) and len(records['controls'])==8,'control coverage')
    for r in records['controls']:
        c=cs[r['case']];observed=row(c['id'],'full-history',-1,'receiver',receiver_prompt(c,full=True))
        with tempfile.TemporaryDirectory() as work:expected={'case':c['id'],**finish(c,observed,Path(work))}
        require(r==expected,'control effect/score drift')
    expected_episodes={tuple(s) for s in frozen['schedule']}
    keyed={(r['case'],r['arm'],r['repetition']):r for r in records['episodes']}
    require(len(keyed)==len(records['episodes'])==64 and set(keyed)==expected_episodes,'episode coverage/duplicate')
    for cid,arm,rep in frozen['schedule']:
        c=cs[cid];record=keyed[cid,arm,rep]
        base={'case':cid,'seed':c['seed'],'variant':c['variant'],'arm':arm,'repetition':rep,'artifacts':[],
              'primary':False,'score':{'shape':False,'safe':False,'traceable':False,'optimal':False,'utility':0,'cost':0},'plan_effect':{'written':False}}
        with tempfile.TemporaryDirectory() as work:
            folder=Path(work)
            first=row(cid,arm,rep,'prime',prime_prompt(readings[arm]));approach=field(first,'approach')
            if approach is None:require(record=={**base,'failure_stage':'prime'},'invalid prime score drift');continue
            base['artifacts'].append(artifact(folder,'approach.txt',approach.encode()))
            sent=row(cid,arm,rep,'sender',prepared_sender_prompt(c,approach));whole=field(sent,'handoff')
            if whole is None:require(record=={**base,'failure_stage':'sender'},'invalid handoff score drift');continue
            base['artifacts'].append(artifact(folder,'whole-note.txt',whole.encode()))
            note,cut=stored_note(whole,frozen['capacity'])
            base['artifacts'].append(artifact(folder,'stored-note.txt',note.encode()))
            received=row(cid,arm,rep,'receiver',receiver_prompt(c,note,truncated=cut))
            expected={**base,**finish(c,received,folder),'failure_stage':None if received['terminal'] else 'receiver',
                      'truncated':cut,'whole_note_bytes':len(whole.encode()),'stored_note_bytes':len(note.encode())}
            require(record==expected,'episode effect/score drift')
    require(consumed==set(keys),'unexpected target call')
    summaries=[]
    for arm in ARMS:
        chosen=[r for r in records['episodes'] if r['arm']==arm];calls=[r for r in rows if r['arm']==arm]
        summaries.append({'arm':arm,'episodes':16,'primary_successes':sum(r['primary'] for r in chosen),
          'safe_plans':sum(r['score']['safe'] for r in chosen),'traceable_plans':sum(r['score']['traceable'] for r in chosen),
          'certified_optimal':sum(r['score']['optimal'] for r in chosen),
          'unsafe_valid_proposals':sum(r['score']['shape'] and not r['score']['safe'] for r in chosen),
          'empty_admitted_plans':sum(r['plan_effect'].get('written',False) and not r['plan_effect']['plan'] for r in chosen),
          'stage_failures':sum(r['failure_stage']is not None for r in chosen),
          'mean_normalized_admitted_utility':statistics.mean(r['score']['utility']/brute(cs[r['case']])['value'] if r['plan_effect']['written'] else 0 for r in chosen),
          'calls':len(calls),'errors':sum('error'in r for r in calls),'nonterminal':sum(not r['terminal'] for r in calls),
          'unexpected_items':sum(len(r['tools']) for r in calls),'truncated_notes':sum(r.get('truncated',False) for r in chosen),
          'input_tokens':sum(r.get('usage',{}).get('input_tokens',0) for r in calls),
          'cached_input_tokens':sum(r.get('usage',{}).get('cached_input_tokens',0) for r in calls),
          'output_tokens':sum(r.get('usage',{}).get('output_tokens',0) for r in calls),
          'aggregate_call_wall_ms':round(sum(r['wall_ms'] for r in calls),3)})
    paired=[]
    for other in ('ordinary','guide','unrelated'):
        changes={(c['id'],rep):int(keyed[c['id'],'book',rep]['primary'])-int(keyed[c['id'],other,rep]['primary']) for c in cs.values() for rep in range(2)}
        seeds=sorted({c['seed'] for c in cs.values()})
        clusters=[statistics.mean(v for (cid,rep),v in changes.items() if cs[cid]['seed']==seed) for seed in seeds]
        samples=[statistics.mean(group) for group in itertools.product(clusters,repeat=4)]
        values=list(changes.values())
        paired.append({'a':'book','b':other,'wins':values.count(1),'losses':values.count(-1),'ties':values.count(0),
                       'difference':statistics.mean(values),'source_clusters':4,'cluster_differences':dict(zip(map(str,seeds),clusters)),
                       'descriptive_cluster_bootstrap_95_percentile':[quantile(samples,0.025),quantile(samples,0.975)]})
    return {'schema':'reading-transfer-results/1','captured_calls':len(rows),'participant_episodes':64,
            'requested_model':'gpt-6.1-sol','reasoning_effort':'high','capacity':frozen['capacity'],
            'full_history_controls':{'cases':8,'primary_successes':sum(r['primary'] for r in records['controls'])},
            'summary':summaries,'paired':paired,'raw_sha256':sha(raw),'wall_seconds':complete['wall_seconds'],
            'scope':'Reading-mediated operating approach and constrained transfer on one authored planning class; not natural voice, general agency or subjective experience.',
            'limits':['four source-seed clusters with dependent counterfactual variants and repetitions','developer-authored cases, law and evaluators','exploratory after three development calibrations','same model family and shared Codex harness','source language/genre/style not fully isolated','reference-runtime rehearsal included in book reading','no external replication or independent preregistration']}


if __name__=='__main__':
    result=derive();(HERE/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
