"""Independent raw readback/replay; never calls a provider or trusts stored scores."""
from collections import defaultdict
from pathlib import Path
import gzip
import hashlib
import itertools
import json
import tempfile
from tasks import ARMS,make_world,specifications,parse,score
from run import prompt,pins,schedule,execution,transfer_rows
from participation import ParticipationStore

HERE=Path(__file__).resolve().parent

def require(ok,why):
    if not ok:raise ValueError(why)
def sha(b):return hashlib.sha256(b).hexdigest()

def normalized(v):
    if type(v)is list:return [normalized(x) for x in v]
    if type(v)is dict:return {k:normalized(x) for k,x in v.items() if k not in ('wall_ms','receipt')}
    return v


def analyze(base=HERE):
    f=json.loads((base/'freeze.json').read_text());done=json.loads((base/'completion.json').read_text())
    require(f['canary_sha256']==sha((base/'canary.json').read_bytes()),'canary-drift')
    require(f['input_sha256']==pins(),'frozen-source-drift');require(f['schedule']==schedule(),'schedule-drift')
    require(done['freeze_sha256']==sha((base/'freeze.json').read_bytes()),'freeze-drift')
    raw=gzip.decompress((base/'responses.jsonl.gz').read_bytes());require(sha(raw)==done['raw_sha256'],'raw-drift')
    rows=[json.loads(x) for x in raw.splitlines()];require(done['status']=='complete' and len(rows)==done['calls']==32,'incomplete-cohort')
    indexed={};cases={c['id']:c for c in specifications()}
    for row in rows:
        key=(row['case'],row['arm'],row['stage']);require(key not in indexed,'duplicate-call');indexed[key]=row
    summary=[];episodes={};traces=[];transfer=[]
    for cid,arm in f['schedule']:
        stages=[];methods={}
        with tempfile.TemporaryDirectory(prefix='ontology-analysis-replay-') as folder:
            db=Path(folder)/'loop.sqlite';ParticipationStore(db,create=True)
            for stage in range(2):
                require((cid,arm,stage) in indexed,'missing-call');r=indexed[cid,arm,stage]
                store=ParticipationStore(db);previous,effects,tail=store.context()
                world=make_world(cases[cid],stage,effects);require(r['world']==world,'world-not-from-actual-effects')
                text=prompt(world,arm,previous);require(r['prompt']==text and r['prompt_sha256']==sha(text.encode()),'prompt-drift')
                require(r['terminal']==bool(r['exit_code']==0 and not r['tools'] and any(e['type']=='turn.completed' for e in r['events']) and 'error' not in r and not r.get('unparsed_stdout')),'terminal-drift')
                answer=parse(r['response']);rated=score(world,answer,r['terminal']);require(r['score']==rated,'score-drift')
                effective,planned=execution(world,answer,r['terminal']);require(normalized(planned)==normalized(r['execution']),'method-execution-drift')
                emitted=store.record_turn(f'turn-{stage}',world,effective,response=r['response'],terminal=r['terminal'],expected=tail['head'])
                require(normalized(emitted)==normalized(r['controller']),'controller-readback-drift')
                require(bool(rated['safe'])==bool(emitted['committed']),'oracle-controller-disagree')
                methods['M'+str(stage)]=answer if r['terminal'] else None;stages.append(rated)
        local=transfer_rows(methods);transfer.extend({'case':cid,'arm':arm,**r} for r in local)
        episodes[cid,arm]=all(x['all_correct'] for x in stages)
        traces.append({'case':cid,'family':cases[cid]['family'],'arm':arm,'complete':episodes[cid,arm],'stages':stages})
    captured=json.loads((base/'transfer.json').read_text())
    key=lambda r:(r['case'],r['arm'],r['transfer_case'],r['version'])
    require(len(captured)==len(transfer)==done['transfer_executions']==768,'transfer-count')
    require(normalized(sorted(captured,key=key))==normalized(sorted(transfer,key=key)),'transfer-replay-drift')
    for arm in ARMS:
        rr=[r for r in rows if r['arm']==arm]
        s={'arm':arm,'trajectories':8,'complete':sum(v for (c,a),v in episodes.items() if a==arm),'calls':len(rr)}
        for k in ['all_correct','safe','optimal_plan','excess_abstention','affected_correct','current_criterion_correct','assessments_correct','own_effects_correct','open_objections_correct']:
            s[k]=sum(r['score'][k] for r in rr)
        s['stages']=[{'stage':stage,'all_correct':sum(r['score']['all_correct'] for r in rr if r['stage']==stage),'n':8} for stage in range(2)]
        s['benefit']=sum(r['score']['benefit'] for r in rr);s['available_benefit']=sum(r['score']['optimal_benefit'] for r in rr)
        for k in ['input_tokens','cached_input_tokens','output_tokens']:s[k]=sum(r.get('usage',{}).get(k,0) for r in rr)
        s['wall_ms']=round(sum(r['wall_ms'] for r in rr),3);s['nonterminal']=sum(not r['terminal'] for r in rr);s['tool_calls']=sum(bool(r['tools']) for r in rr)
        s['method_transfer']={version:{'executions':192,'optimal':sum(r['score']['optimal_plan'] for r in transfer if r['arm']==arm and r['version']==version),'safe':sum(r['score']['safe'] for r in transfer if r['arm']==arm and r['version']==version),'benefit':sum(r['score']['benefit'] for r in transfer if r['arm']==arm and r['version']==version)} for version in ['M0','M1']}
        summary.append(s)
    pairs=[];clusters=defaultdict(list);revision=[]
    for c in specifications():
        a,b=episodes[c['id'],ARMS[0]],episodes[c['id'],ARMS[1]];delta=int(b)-int(a)
        pairs.append({'case':c['id'],'family':c['family'],'ordinary':a,'ontology':b,'delta':delta});clusters[c['family']].append(delta)
        for arm in ARMS:
            case_rows=[r for r in transfer if r['case']==c['id'] and r['arm']==arm]
            old={r['transfer_case']:r for r in case_rows if r['version']=='M0'};new={r['transfer_case']:r for r in case_rows if r['version']=='M1'}
            transitions=[(old[k],new[k]) for k in old]
            revision.append({'case':c['id'],'arm':arm,'behavior_changed':sum((a['execution'] or {}).get('plan')!=(b['execution'] or {}).get('plan') for a,b in transitions),
              'newly_optimal':sum(not a['score']['optimal_plan'] and b['score']['optimal_plan'] for a,b in transitions),
              'regressed':sum(a['score']['optimal_plan'] and not b['score']['optimal_plan'] for a,b in transitions),
              'benefit_change':sum(b['score']['benefit']-a['score']['benefit'] for a,b in transitions)})
    means=[sum(v)/len(v) for v in clusters.values()];samples=sorted(sum(x)/4 for x in itertools.product(means,repeat=4))
    return {'schema':'closed-loop-results/2','requested_model':f['requested_model'],'reasoning_effort':'high',
      'scored_calls':len(rows),'source_commit':done['source_commit'],'raw_sha256':sha(raw),'summary':summary,
      'pairs':pairs,'trajectories':traces,'method_revisions':revision,'primary_difference':sum(means)/4,
      'descriptive_four_cluster_interval':[samples[6],samples[249]],'bootstrap_resamples':256,
      'independent_task_classes':1,'intervention_clusters':4,
      'boundary':'Developer-controlled relation-assisted construction/revision of executable methods. Shared planner/predicates/controller in both arms; added relation view is treatment. Feedback-associated, not feedback-causal without ablation. No full-book, voice, consciousness or general learning benefit.'}


if __name__=='__main__':
    r=analyze();(HERE/'results.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k not in ('trajectories','pairs','method_revisions')},ensure_ascii=False))
