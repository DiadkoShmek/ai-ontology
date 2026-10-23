"""Preregistered construction -> actual effect -> executable method revision."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
from pathlib import Path
import gzip
import hashlib
import json
import random
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from tasks import ARMS,RULES,make_world,specifications,transfer_cases,parse,score
from model import MODEL,command,invoke
from participation import ParticipationStore,Hold,canonical,digest,interpret,admissible
from participation_method import select_plan

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
LOCK=threading.Lock()


def sha(b):return hashlib.sha256(b).hexdigest()
def dump(p,obj):
    with p.open('x') as s:s.write(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')


def schedule():
    s=[[c['id'],a] for c in specifications() for a in ARMS];random.Random(771230).shuffle(s);return s


def pins():
    names=['PROTOCOL.md','tasks.py','run.py','model.py','analyze.py','test_study.py','test_integrity.py','cases.json',
      '../../examples/participation.py','../../examples/participation_method.py',
      '../../examples/test_participation.py','../../examples/test_participation_method.py',
      '../../examples/durable.py','../../examples/continuity.py',
      '../gpt_profile_pilot_v2/run.py','../gpt_profile_pilot_v2/design.py','../participation_pilot/design.py']
    return {p:sha((HERE/p).read_bytes()) for p in names}


def prompt(world,arm,prior):
    body={'current_world':world,'actual_previous_turns':prior}
    if arm=='ontology_loop':body['prepared_relation_view']=interpret(world)
    elif arm!='ordinary_loop':raise ValueError('arm')
    return RULES+'\n\n'+json.dumps(body,ensure_ascii=False,sort_keys=True)


def preflight():
    r=invoke('Use no tools. Return exactly {"ready":true}.')
    dump(HERE/'canary.json',r)
    if not r['terminal'] or r['response']!='{"ready":true}':raise ValueError('route-canary-failed')
    print(json.dumps({'canary':'ready','terminal':True,'usage':r.get('usage')}))


def freeze():
    c=json.loads((HERE/'canary.json').read_text())
    if not c['terminal'] or c['response']!='{"ready":true}':raise ValueError('route-not-qualified')
    dump(HERE/'cases.json',{'trajectories':specifications(),'transfer_worlds':transfer_cases()})
    launcher=Path(shutil.which('codex')).resolve()
    f={'schema':'closed-loop-freeze/2','created_at':datetime.now(timezone.utc).isoformat(),
       'input_sha256':pins(),'requested_model':MODEL,'reasoning_effort':'high',
       'cli_version':subprocess.check_output(['codex','--version'],text=True).strip(),
       'cli_launcher_sha256':sha(launcher.read_bytes()),'command_template':command('{isolated-temporary-directory}'),
       'canary_sha256':sha((HERE/'canary.json').read_bytes()),'arms':list(ARMS),
       'source_trajectories':8,'intervention_clusters':4,'independent_task_classes':1,
       'model_stages':2,'transfer_worlds':24,'transfer_method_versions':['M0','M1'],
       'transfer_executions':768,'schedule':schedule(),'maximum_scored_calls':32,'canary_calls':1,
       'maximum_concurrent_targets':2,'independent_registration':False,
       'primary':'both-model-stages-correct','revision_endpoint':'M1-minus-M0-on-identical-transfer-worlds',
       'no_outcome_retry':True,'no_gold_in_target':True,'no_private_chat_in_target':True}
    dump(HERE/'freeze.json',f);print(json.dumps({'frozen':True,'sha256':sha((HERE/'freeze.json').read_bytes()),'maximum_calls':32}))


def execution(world,answer,terminal):
    if answer is None or not terminal:return None,None
    result=select_plan(world,answer['method'])
    # This derived plan comes from the supplied method and the common budget
    # planner. It never calls a gold oracle or replaces the target's method.
    effective={**answer,'plan':result['plan']}
    return effective,result


def transfer_rows(methods):
    result=[]
    for spec in transfer_cases():
        world=spec['world']
        for version,answer in methods.items():
            rated=score(world,answer,answer is not None)
            rated={k:rated[k] for k in ('shape','terminal','safe','optimal_plan','benefit','optimal_benefit','excess_abstention')}
            effective,planned=execution(world,answer,answer is not None)
            with tempfile.TemporaryDirectory(prefix='ontology-transfer-method-') as folder:
                store=ParticipationStore(Path(folder)/'loop.sqlite',create=True);_,tail=store.read()
                historical={'frozen_method':answer['method'],'source_answer_sha256':digest(answer),'plan':planned['plan']} if answer else None
                r=store.record_turn('turn-0',world,historical,response='',terminal=answer is not None,expected=tail['head'])
                require_controller_agreement(r,rated)
            result.append({'transfer_case':spec['id'],'transfer_variant':spec['variant'],'version':version,'method_sha256':digest(answer['method']) if answer else None,
                           'execution':planned,'score':rated,'controller':r})
    return result


def require_controller_agreement(emitted,rated):
    if bool(rated['safe'])!=bool(emitted['committed']):raise ValueError('oracle-controller-disagreement')


def run():
    f=json.loads((HERE/'freeze.json').read_text())
    if f['input_sha256']!=pins() or f['schedule']!=schedule():raise ValueError('frozen-input-drift')
    if f.get('cli_launcher_sha256') is not None:
        launcher=Path(shutil.which('codex')).resolve()
        if sha(launcher.read_bytes())!=f['cli_launcher_sha256']:raise ValueError('frozen-launcher-drift')
        if subprocess.check_output(['codex','--version'],text=True).strip()!=f['cli_version']:raise ValueError('frozen-cli-version-drift')
    if sha((HERE/'canary.json').read_bytes())!=f['canary_sha256']:raise ValueError('frozen-canary-drift')
    paths=[str((HERE/p).relative_to(ROOT)) for p in f['input_sha256']]+[str((HERE/'freeze.json').relative_to(ROOT)),str((HERE/'canary.json').relative_to(ROOT))]
    if subprocess.check_output(['git','status','--porcelain','--',*paths],cwd=ROOT):raise ValueError('frozen-inputs-not-committed')
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    output=(HERE/'responses.jsonl').open('x');count=0;began=time.perf_counter();indexed={c['id']:c for c in specifications()};transfers=[]
    def episode(pair):
        nonlocal count
        cid,arm=pair;case=indexed[cid];methods={}
        with tempfile.TemporaryDirectory(prefix='ontology-participation-store-') as folder:
            db=Path(folder)/'loop.sqlite';ParticipationStore(db,create=True)
            for stage in range(2):
                store=ParticipationStore(db)
                # The journal readback, including rejected attempts, is the
                # actual carrier into the next target and environment step.
                previous,effects,tail=store.context()
                world=make_world(case,stage,effects)
                text=prompt(world,arm,previous);observed=invoke(text);answer=parse(observed['response'])
                rated=score(world,answer,observed['terminal']);effective,planned=execution(world,answer,observed['terminal'])
                failure=None
                try:
                    emitted=store.record_turn(f'turn-{stage}',world,effective,response=observed['response'],terminal=observed['terminal'],expected=tail['head'])
                    require_controller_agreement(emitted,rated)
                except (ValueError,OSError,RuntimeError) as exc:
                    # Keep the actual model attempt before stopping. A lost
                    # persistence readback cannot be silently continued in RAM.
                    emitted={'committed':False,'effects':[],'confirmation':'unknown','runtime_error':type(exc).__name__}
                    failure=exc
                row={'case':cid,'family':case['family'],'seed':case['seed'],'arm':arm,'stage':stage,
                     'world':world,'prompt':text,'prompt_sha256':sha(text.encode()),
                     **observed,'execution':planned,'score':rated,'controller':emitted}
                with LOCK:
                    output.write(json.dumps(row,ensure_ascii=True)+'\n');output.flush();count+=1
                    print(json.dumps({'completed':count,'maximum':32,'case':cid,'arm':arm,'stage':stage}),flush=True)
                if failure:raise RuntimeError('recorded-runtime-failure-cohort-partial') from failure
                methods['M'+str(stage)]=answer if observed['terminal'] else None
        local=transfer_rows(methods)
        with LOCK:transfers.extend({'case':cid,'arm':arm,**r} for r in local)
    status='complete'
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(episode,f['schedule']))
    except Exception:
        status='partial';raise
    finally:
        output.close()
        raw=(HERE/'responses.jsonl').read_bytes();(HERE/'responses.jsonl.gz').write_bytes(gzip.compress(raw,mtime=0))
        done={'schema':'closed-loop-completion/2','status':status,'calls':count,'source_commit':commit,
          'freeze_sha256':sha((HERE/'freeze.json').read_bytes()),'raw_sha256':sha(raw),
          'transfer_executions':len(transfers),'wall_seconds':round(time.perf_counter()-began,3),
          'completed_at':datetime.now(timezone.utc).isoformat()}
        dump(HERE/'transfer.json',transfers);dump(HERE/'completion.json',done);print(json.dumps(done))


if __name__=='__main__':
    args=sys.argv[1:]
    if args==['preflight']:preflight()
    elif args==['freeze']:freeze()
    elif args==['run']:run()
    else:raise SystemExit('preflight | freeze | run')
