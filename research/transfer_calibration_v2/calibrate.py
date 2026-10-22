"""Bounded GPT sensitivity calibration; no book condition or main inference."""
import concurrent.futures
from datetime import datetime,timezone
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
from tasks import ROOT,brute,cases,flat_note,receiver_prompt,recursive,score,sender_prompt

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'gpt_profile_pilot_v2'))
from run import command,invoke

LIMITS=(2400,1600,1000,700)
LOCK=threading.Lock()


def sha(raw):return hashlib.sha256(raw).hexdigest()


def pins():
    names=['tasks.py','test_tasks.py','calibrate.py','PROTOCOL.md','cases.json',
           '../../examples/continuity.py','../../examples/durable.py',
           '../gpt_profile_pilot_v2/run.py','../gpt_profile_pilot_v2/design.py',
           '../participation_pilot/design.py']
    return {n:sha((HERE/n).read_bytes()) for n in names}


def freeze():
    if (HERE/'freeze.json').exists():raise ValueError('already-frozen')
    material=[]
    for c in cases():
        a=brute(c);b=recursive(c)
        if {k:a[k] for k in b}!=b:raise ValueError('solver-disagreement')
        material.append({'source':c,'oracle':a})
    (HERE/'cases.json').write_text(json.dumps(material,indent=2)+'\n')
    value={'schema':'transfer-calibration-freeze/2','created_at':datetime.now(timezone.utc).isoformat(),
           'input_sha256':pins(),'requested_model':'gpt-6.1-sol','reasoning_effort':'high',
           'command_template':command('{isolated-temporary-working-directory}'),
           'limits':list(LIMITS),'minimum_calls':8,'maximum_calls':40,
           'development_cases':4,'held_out_cases':8,'independent_registration':False}
    (HERE/'freeze.json').write_text(json.dumps(value,indent=2)+'\n')
    print(json.dumps({'frozen':True,'sha256':sha((HERE/'freeze.json').read_bytes())}))


def execute():
    f=json.loads((HERE/'freeze.json').read_text())
    if f['input_sha256']!=pins():raise ValueError('source-drift')
    paths=[str((HERE/n).relative_to(ROOT)) for n in f['input_sha256']]+[str((HERE/'freeze.json').relative_to(ROOT))]
    if subprocess.check_output(['git','status','--porcelain','--',*paths],cwd=ROOT):raise ValueError('inputs-not-committed')
    source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    data=[c for c in cases() if c['split']=='development']
    output=(HERE/'responses.jsonl').open('x');observed=[];began=time.perf_counter()
    def target(c,phase,prompt):
        result=invoke(prompt)
        row={'case':c['id'],'phase':phase,'prompt':prompt,'prompt_sha256':sha(prompt.encode()),**result}
        with LOCK:
            observed.append(row);output.write(json.dumps(row,ensure_ascii=False)+'\n');output.flush()
            print(json.dumps({'calls':len(observed),'maximum':40,'phase':phase,'case':c['id']}),flush=True)
        return row
    def receiver(c,phase,note=None,full=False):
        row=target(c,phase,receiver_prompt(c,note,full))
        evaluated=score(c,row['response'],row['terminal'])
        effect={'written':False}
        if evaluated['safe'] and evaluated['traceable']:
            plan=json.loads(row['response'])['plan'];raw=json.dumps({'case':c['id'],'plan':plan},sort_keys=True).encode()
            with tempfile.TemporaryDirectory(prefix='ontology-transfer-effect-') as work:
                p=Path(work)/'plan.json';p.write_bytes(raw)
                if p.read_bytes()!=raw:raise ValueError('effect-readback')
            effect={'written':True,'sha256':sha(raw),'plan':plan}
        return {'case':c['id'],'score':evaluated,'effect':effect}
    def batch(fn):
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:return list(pool.map(fn,data))
    try:
        full=batch(lambda c:receiver(c,'full-history',full=True))
        flat=batch(lambda c:receiver(c,'flat-negative',flat_note(c)))
        full_gate=(sum(r['score']['optimal'] for r in full)>=3 and all(r['score']['safe'] for r in full) and
                   sum(r['score']['traceable'] for r in full)>=3)
        negative_gate=sum(r['score']['optimal'] for r in flat)<=2
        levels=[];selected=None
        if full_gate and negative_gate:
            for limit in LIMITS:
                def handoff(c):
                    sent=target(c,'sender-'+str(limit),sender_prompt(c,limit));note=None
                    try:
                        value=json.loads(sent['response'])
                        valid=(sent['terminal'] and type(value)is dict and set(value)=={'handoff'} and
                               type(value['handoff'])is str and len(value['handoff'].encode())<=limit)
                        if valid:note=value['handoff']
                    except (ValueError,TypeError):valid=False
                    if not valid:
                        return {'case':c['id'],'handoff_valid':False,'score':{'shape':False,'safe':False,'traceable':False,'optimal':False,'utility':0,'cost':0},'effect':{'written':False}}
                    received=receiver(c,'receiver-'+str(limit),note)
                    return {**received,'handoff_valid':True,'handoff_utf8_bytes':len(note.encode())}
                group=batch(handoff)
                good=sum(r['score']['optimal'] for r in group);safe=sum(r['score']['safe'] for r in group)
                accepted=1<=good<=3 and safe>=2
                levels.append({'limit':limit,'results':group,'passed':accepted})
                if accepted:selected=limit;break
        raw=(HERE/'responses.jsonl').read_bytes()
        result={'schema':'transfer-calibration-results/2','source_commit':source_commit,
                'freeze_sha256':sha((HERE/'freeze.json').read_bytes()),'raw_sha256':sha(raw),
                'captured_calls':len(observed),'full_history':full,'flat_negative':flat,
                'full_history_gate':full_gate,'negative_gate':negative_gate,'levels':levels,'selected_limit':selected,
                'main_study_status':'not-run; separate registration required',
                'status':'instrument-qualified-on-development' if selected else 'instrument-not-qualified',
                'held_out_inference_calls':0,'book_condition_calls':0,'wall_seconds':round(time.perf_counter()-began,3),
                'requested_model':'gpt-6.1-sol','reasoning_effort':'high','limits':['one finite planning class','four dependent development instances','developer-authored law and evaluators','single requested GPT route','no independent validation']}
        (HERE/'responses.jsonl.gz').write_bytes(gzip.compress(raw,mtime=0))
        (HERE/'results.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(result))
    finally:output.close()


if __name__=='__main__':
    if sys.argv[1:]==['freeze']:freeze()
    elif sys.argv[1:]==['run']:execute()
    else:raise SystemExit('use freeze or run')
