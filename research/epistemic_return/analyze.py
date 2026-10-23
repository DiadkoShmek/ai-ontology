"""Offline full replay of model-visible prompts, local probes and readback.

No model imports, network, credentials or provider execution. Source pins are
checked directly from frozen paths without importing the inference runner.
"""
from collections import defaultdict
import gzip
import json
from pathlib import Path
import tempfile
from task_design import (ARMS,sha,canonical,cases,source_tasks,transfer_tasks,diagnostic,expose,
    parse,memory_value,initial_prompt,update_prompt,transfer_prompt,score,materialize,information_witness)
from environment import Environment,persist_memory

HERE=Path(__file__).resolve().parent


def analyze(folder=HERE, *, check_pins=True):
    frozen=json.loads((folder/'freeze.json').read_text()) if check_pins else None
    if check_pins:
        for name,expected in frozen['input_sha256'].items():
            if sha((folder/name).read_bytes())!=expected:raise ValueError('frozen-source-drift:'+name)
        if json.loads((folder/'cases.json').read_text())!=materialize():raise ValueError('materialized-case-drift')
    completion=json.loads((folder/'completion.json').read_text())
    wire=gzip.decompress((folder/'responses.jsonl.gz').read_bytes())
    if sha(wire)!=completion['raw_sha256']:raise ValueError('raw-archive-drift')
    rows=[json.loads(line) for line in wire.splitlines()]
    model=[r for r in rows if r.get('kind')!='runtime']
    runtime=[r for r in rows if r.get('kind')=='runtime']
    if len(model)!=completion['captured_calls_including_canary'] or completion['status']!='complete':
        raise ValueError('partial-or-count-mismatch')
    canary=[r for r in model if r['stage']==-1]
    if len(canary)!=1 or not canary[0]['terminal'] or canary[0]['response']!='{"ready":true}':
        raise ValueError('canary-mismatch')
    index={}
    for row in model:
        key=(row['case'],row['stage'],row['arm'])
        if key in index:raise ValueError('duplicate-model-row')
        index[key]=row
        if sha(row['prompt'].encode())!=row['prompt_sha256']:raise ValueError('prompt-sha-mismatch')
        # Native terminal claims must match the captured lifecycle, not only a bool.
        done=any(e.get('type')=='turn.completed' for e in row['events'])
        failed=any(e.get('type') in ('turn.failed','error') for e in row['events'])
        expect=bool(done and not failed and row['exit_code']==0 and not row['tools'] and 'error' not in row and not row.get('unparsed_stdout'))
        if row['terminal']!=expect:raise ValueError('terminal-native-mismatch')
    rt={}
    for row in runtime:
        key=(row['case'],row['arm'])
        if key in rt:raise ValueError('duplicate-runtime-row')
        rt[key]=row
    if len(model)!=73 or len(rt)!=32:raise ValueError('unexpected-cohort-size')
    arms={a:{'source_optimal':0,'transfer_optimal':0,'source_total':0,'transfer_total':0,
             'upstream_warranted_transfer':0,'source_utility':0,'upstream_transfer_utility':0,
             'full_information_transfer_optimal':0,'full_information_transfer_utility':0,
             'memory_unavailable':0,'changed_source_decisions':0,
             'reversed_good_source_decisions':0,'episodes_perfect':0,
             'input_tokens':0,'output_tokens':0,'model_wall_ms':0,'realized_bad_effects':0} for a in ARMS}
    details=[];probe_choices=defaultdict(int);initial_optimal=0;initial_total=0
    for c in cases():
        m0=index[(c['id'],0,None)]
        if m0['prompt']!=initial_prompt(c):raise ValueError('initial-prompt-drift')
        first=parse(m0['response'],source_tasks(c),0) if m0['terminal'] else None
        before=score(source_tasks(c),first,m0['terminal'],c,None)
        initial_optimal+=before['optimal'];initial_total+=before['total']
        probe=first['probe'] if first else 'none';probe_choices[probe]+=1
        with tempfile.TemporaryDirectory(prefix='epistemic-offline-replay-') as work:
            work=Path(work)
            env=Environment(work/'probe.sqlite',c,source_tasks(c));actual=env.probe(probe)
            if actual!=diagnostic(c,probe):raise ValueError('diagnostic-replay-drift')
            for arm in ARMS:
                saved=rt[(c['id'],arm)];feedback=expose(actual,arm.endswith('_actual'))
                m1=index[(c['id'],1,arm)];m2=index[(c['id'],2,arm)]
                if m1['prompt']!=update_prompt(c,arm,first,feedback):raise ValueError('update-prompt-drift')
                a=parse(m1['response'],source_tasks(c),1) if m1['terminal'] else None
                memory=memory_value(a,arm)
                read,receipt=persist_memory(work/(arm+'.sqlite'),memory)
                # A fresh SQLite stream has a different stream/head; wire is exact.
                for key in ('wire_sha256','wire_bytes','seq','reopened'):
                    if receipt[key]!=saved['readback'][key]:raise ValueError('memory-readback-receipt-drift')
                if saved['admitted_memory']!=memory or saved['diagnostic']!=actual or saved['exposed_feedback']!=feedback:
                    raise ValueError('runtime-feedback-or-memory-drift')
                if m2['prompt']!=transfer_prompt(c,read):raise ValueError('transfer-prompt-drift')
                b=parse(m2['response'],transfer_tasks(c),2) if m2['terminal'] else None
                current=Environment(work/(arm+'-current.sqlite'),c,source_tasks(c))
                later=Environment(work/(arm+'-later.sqlite'),c,transfer_tasks(c))
                if current.apply(source_tasks(c),a,m1['terminal'])!=saved['source_effects'] or later.apply(transfer_tasks(c),b,m2['terminal'])!=saved['transfer_effects']:
                    raise ValueError('actual-sqlite-effect-drift')
                s=score(source_tasks(c),a,m1['terminal'],c,feedback)
                t=score(transfer_tasks(c),b,m2['terminal'],c,feedback)
                informed=score(transfer_tasks(c),b,m2['terminal'],c,diagnostic(c,'sentinel'))
                initial_by={x['id']:x for x in before['decisions']}
                changed=sum(x['action']!=initial_by[x['id']]['action'] for x in s['decisions'])
                regressed=sum(initial_by[x['id']]['optimal'] and not x['optimal'] for x in s['decisions'])
                d={'case':c['id'],'mode':c['mode'],'arm':arm,'probe':probe,'source':s,'transfer':t,
                   'full_information_transfer':informed,
                   'transfer_score_scope':'relative-to-feedback-exposed-upstream; not an automatic interpretation of saved-memory meaning',
                   'changed_source_decisions':changed,'reversed_good_source_decisions':regressed,
                   'memory_unavailable':type(memory) is dict and 'unavailable' in memory,
                   'memory_wire_bytes':receipt['wire_bytes']}
                details.append(d);total=arms[arm]
                for stem,report in [('source',s),('transfer',t)]:
                    total[stem+'_optimal']+=report['optimal'];total[stem+'_total']+=report['total']
                    total['upstream_transfer_utility' if stem=='transfer' else 'source_utility']+=report['guaranteed_utility']
                total['upstream_warranted_transfer']+=t['justified']
                total['full_information_transfer_optimal']+=informed['optimal']
                total['full_information_transfer_utility']+=informed['guaranteed_utility']
                total['memory_unavailable']+=d['memory_unavailable']
                total['changed_source_decisions']+=changed;total['reversed_good_source_decisions']+=regressed
                total['episodes_perfect']+=t['optimal']==t['total']
                total['realized_bad_effects']+=sum(bool(x['bad_effect']) for x in saved['source_effects']+saved['transfer_effects'])
                for r in (m1,m2):
                    for k in ('input_tokens','output_tokens'):total[k]+=r.get('usage',{}).get(k,0)
                    total['model_wall_ms']+=r['wall_ms']
    paired=[]
    for c in cases():
        ds={r['arm']:r for r in details if r['case']==c['id']}
        opt=lambda a:ds[a]['full_information_transfer']['optimal']
        paired.append({'case':c['id'],'mode':c['mode'],
            'format_actual':opt('linked_actual')-opt('free_actual'),
            'format_masked':opt('linked_masked')-opt('free_masked'),
            'feedback_free':opt('free_actual')-opt('free_masked'),
            'feedback_linked':opt('linked_actual')-opt('linked_masked'),
            'factorial_interaction':opt('linked_actual')-opt('free_actual')-opt('linked_masked')+opt('free_masked'),
            'feedback_free_utility':ds['free_actual']['full_information_transfer']['guaranteed_utility']-ds['free_masked']['full_information_transfer']['guaranteed_utility'],
            'feedback_linked_utility':ds['linked_actual']['full_information_transfer']['guaranteed_utility']-ds['linked_masked']['full_information_transfer']['guaranteed_utility']})
    shared={k:sum(r.get('usage',{}).get(k,0) for r in model if r['stage'] in (-1,0)) for k in ('input_tokens','output_tokens')}
    return {'schema':'epistemic-return-results/1','status':'offline-recomputed',
        'episodes':8,'task_classes':1,'scored_model_calls':72,'canary_calls':1,
        'initial':{'optimal':initial_optimal,'total':initial_total,'probe_choices':dict(probe_choices)},
        'arms':arms,'shared_route_and_initial_usage':shared,'paired_episode_deltas':paired,
        'information_witness':information_witness(),'details':details,
        'limits':['developer-authored single finite class','eight instances are not independent task families',
                  'masked feedback intentionally has less information; it is not the primary format baseline',
                  'decision revision is not necessarily algorithm or method formation',
                  'model versions/transport retries not independently attested by provider',
                  'memory allocation differs under identical maximum UTF8-byte allowance',
                  'M2 upstream-feedback-relative scores measure retention opportunity, not epistemic rationality under arbitrary saved-memory meaning',
                  'no full-book or stable-voice intervention','no real human outcome measured']}


if __name__=='__main__':
    out=analyze()
    # Results are derived; inference archive and reservation are never modified.
    (HERE/'results.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:out[k] for k in ('status','initial','arms','paired_episode_deltas')},ensure_ascii=False))
