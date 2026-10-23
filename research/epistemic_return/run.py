"""New sealed cohort. Never invoke a prior sealed inference runner.

No outcome retries or fallback model; one permanent reservation closes both
completed and interrupted cohorts before another provider call is possible.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import gzip
import json
import os
from pathlib import Path
import random
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from task_design import (ARMS,canonical,sha,cases,source_tasks,transfer_tasks,diagnostic,
                    expose,parse,memory_value,initial_prompt,update_prompt,transfer_prompt,score,materialize)
from environment import Environment,persist_memory
_import_paths=sys.path[:]
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'closed_loop'))
from model import invoke,command,MODEL
sys.path[:]=_import_paths  # the reused route must not redirect local analysis imports

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
LOCK=threading.Lock()
OUTPUTS=('run-reservation.json','responses.jsonl','responses.jsonl.gz','completion.json','results.json')


def dump(path,value):
    with path.open('x') as f:
        f.write(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
        f.flush();os.fsync(f.fileno())


def reserve(folder):
    for name in OUTPUTS:
        if os.path.lexists(folder/name):raise ValueError('cohort-already-started-or-sealed:'+name)
    # The directory is an operator-owned, cooperative-writer boundary.
    dump(folder/'run-reservation.json',{'schema':'epistemic-return-reservation/1',
        'created_at':datetime.now(timezone.utc).isoformat(),'pid':os.getpid(),
        'policy':'permanent; no automatic retry or resume'})
    for name in OUTPUTS[1:]:
        if os.path.lexists(folder/name):raise ValueError('cohort-output-race:'+name)


def pins():
    names=['task_design.py','environment.py','run.py','analyze.py','test_design.py','PROTOCOL.md','cases.json',
           '../closed_loop/model.py','../gpt_profile_pilot_v2/run.py','../gpt_profile_pilot_v2/design.py',
           '../participation_pilot/design.py','../../examples/durable.py','../../examples/continuity.py']
    return {n:sha((HERE/n).read_bytes()) for n in names}


def schedule():
    rows=[]
    r=random.Random(918230)
    cs=cases();r.shuffle(cs)
    for c in cs:
        arms=list(ARMS);r.shuffle(arms);rows.append([c['id'],arms])
    return rows


def freeze():
    dump(HERE/'cases.json',materialize())
    launcher=Path(shutil.which('codex')).resolve()
    x={'schema':'epistemic-return-freeze/1','created_at':datetime.now(timezone.utc).isoformat(),
       'input_sha256':pins(),'schedule':schedule(),'requested_model':MODEL,'reasoning_effort':'high',
       'cli_version':subprocess.check_output(['codex','--version'],text=True).strip(),
       'cli_launcher_sha256':sha(launcher.read_bytes()),'command_template':command('{empty-temporary-directory}'),
       'episodes':8,'independent_task_classes':1,'mode_clusters':2,'maximum_scored_calls':72,
       'maximum_canary_calls':1,'maximum_concurrent_targets':2,
       'independent_registration':False,'no_outcome_retry':True,
       'primary':'linked_actual-minus-free_actual-on-new-transfer-optimal-decisions',
       'feedback_ablation':'actual-minus-masked-within-format; unequal-information-by-design',
       'revision_claim':'changed informed decisions, NOT demonstrated new contingent algorithm'}
    dump(HERE/'freeze.json',x)
    print(json.dumps({'frozen':True,'sha256':sha((HERE/'freeze.json').read_bytes())}))


def verify_source():
    frozen=json.loads((HERE/'freeze.json').read_text())
    if pins()!=frozen['input_sha256'] or schedule()!=frozen['schedule']:
        raise ValueError('frozen-input-drift')
    launcher=Path(shutil.which('codex')).resolve()
    if sha(launcher.read_bytes())!=frozen['cli_launcher_sha256'] or subprocess.check_output(['codex','--version'],text=True).strip()!=frozen['cli_version']:
        raise ValueError('frozen-route-drift')
    paths=[str((HERE/n).relative_to(ROOT)) for n in pins()]+[str((HERE/'freeze.json').relative_to(ROOT))]
    if subprocess.check_output(['git','status','--porcelain','--',*paths],cwd=ROOT):
        raise ValueError('source-not-committed')
    return frozen,subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()


def run(inference=invoke, *, verify=True, output_dir=HERE):
    frozen,commit=verify_source() if verify else ({'schedule':schedule()},'authored-test-double')
    reserve(output_dir)  # BEFORE canary AND any output mutation or inference
    raw=(output_dir/'responses.jsonl').open('x');count=0;begin=time.perf_counter()
    def emit(row):
        nonlocal count
        with LOCK:
            raw.write(json.dumps(row,ensure_ascii=True,allow_nan=False)+'\n');raw.flush();os.fsync(raw.fileno())
            count+=1
            print(json.dumps({'captured':count,'case':row.get('case'),'stage':row.get('stage'),'arm':row.get('arm')}),flush=True)
    def call(prompt,cid,stage,arm=None):
        observed=inference(prompt)
        observed.pop('thread_id',None)  # ephemeral target identity is not needed
        row={'case':cid,'stage':stage,'arm':arm,'prompt':prompt,'prompt_sha256':sha(prompt.encode()),**observed}
        emit(row)
        return observed
    indexed={c['id']:c for c in cases()}
    def episode(item):
        cid,arms=item;c=indexed[cid]
        with tempfile.TemporaryDirectory(prefix='ontology-epistemic-return-') as folder:
            folder=Path(folder)
            m0=call(initial_prompt(c),cid,0)
            initial=parse(m0['response'],source_tasks(c),0) if m0['terminal'] else None
            selected=initial['probe'] if initial else 'none'
            env=Environment(folder/'diagnostic.sqlite',c,source_tasks(c))
            actual=env.probe(selected)
            if actual!=diagnostic(c,selected):raise ValueError('diagnostic-fixture-runtime-disagreement')
            for arm in arms:
                feedback=expose(actual,arm.endswith('_actual'))
                m1=call(update_prompt(c,arm,initial,feedback),cid,1,arm)
                answer=parse(m1['response'],source_tasks(c),1) if m1['terminal'] else None
                memory=memory_value(answer,arm)
                # Both arms use the SAME durable mechanism. It interprets no links.
                restored,receipt=persist_memory(folder/(arm+'.sqlite'),memory)
                current=Environment(folder/(arm+'-source.sqlite'),c,source_tasks(c))
                source_effects=current.apply(source_tasks(c),answer,m1['terminal'])
                m2=call(transfer_prompt(c,restored),cid,2,arm)
                final=parse(m2['response'],transfer_tasks(c),2) if m2['terminal'] else None
                later=Environment(folder/(arm+'-transfer.sqlite'),c,transfer_tasks(c))
                effects=later.apply(transfer_tasks(c),final,m2['terminal'])
                # Small local receipts are a separate row, never a model call.
                with LOCK:
                    raw.write(json.dumps({'kind':'runtime','case':cid,'arm':arm,'diagnostic':actual,
                        'exposed_feedback':feedback,'admitted_memory':memory,'readback':receipt,
                        'source_effects':source_effects,'transfer_effects':effects},ensure_ascii=True)+'\n')
                    raw.flush();os.fsync(raw.fileno())
    status='complete'
    try:
        canary=call('Use no tools. Return exactly {"ready":true}.','route-canary',-1)
        if not canary['terminal'] or canary['response']!='{"ready":true}':
            raise ValueError('route-canary-failed')
        with ThreadPoolExecutor(max_workers=2) as pool:
            list(pool.map(episode,frozen['schedule']))
    except BaseException:
        status='partial';raise
    finally:
        raw.close();wire=(output_dir/'responses.jsonl').read_bytes()
        # Compressed output is exclusive, just like the permanent reservation.
        with (output_dir/'responses.jsonl.gz').open('xb') as f:f.write(gzip.compress(wire,mtime=0))
        done={'schema':'epistemic-return-completion/1','status':status,'captured_calls_including_canary':count,
              'source_commit':commit,'raw_sha256':sha(wire),'wall_seconds':round(time.perf_counter()-begin,3),
              'completed_at':datetime.now(timezone.utc).isoformat()}
        dump(output_dir/'completion.json',done);print(json.dumps(done))


if __name__=='__main__':
    if sys.argv[1:]==['freeze']:freeze()
    elif sys.argv[1:]==['run']:run()
    else:raise SystemExit('freeze | run')
