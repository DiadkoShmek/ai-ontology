"""Prospective baseline-only calibration of approach -> carry -> useful plan."""
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
from tasks import (ROOT,brute,cases,flat_note,planning_success,prepared_sender_prompt,
                   prime_prompt,receiver_prompt,recursive,score,stored_note)

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'gpt_profile_pilot_v2'))
from run import command,invoke

LIMITS=(3200,2400,1600,1000,700,400)
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
    value={'schema':'transfer-calibration-freeze/3','created_at':datetime.now(timezone.utc).isoformat(),
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
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    data=[c for c in cases() if c['split']=='development']
    output=(HERE/'responses.jsonl').open('x');observed=[];began=time.perf_counter()
    def target(c,phase,prompt):
        response=invoke(prompt)
        row={'case':c['id'],'phase':phase,'prompt':prompt,'prompt_sha256':sha(prompt.encode()),**response}
        with LOCK:
            observed.append(row);output.write(json.dumps(row,ensure_ascii=False)+'\n');output.flush()
            print(json.dumps({'calls':len(observed),'maximum':40,'phase':phase,'case':c['id']}),flush=True)
        return row
    def receiver(c,phase,note=None,full=False,truncated=False):
        row=target(c,phase,receiver_prompt(c,note,full,truncated))
        judged=score(c,row['response'],row['terminal']);effect={'written':False}
        if judged['safe']:
            plan=json.loads(row['response'])['plan'];raw=json.dumps({'case':c['id'],'plan':plan},sort_keys=True).encode()
            with tempfile.TemporaryDirectory(prefix='ontology-transfer-v3-effect-') as work:
                p=Path(work)/'plan.json';p.write_bytes(raw)
                if p.read_bytes()!=raw:raise ValueError('effect-readback')
            effect={'written':True,'sha256':sha(raw),'plan':plan}
        return {'case':c['id'],'primary':planning_success(judged,c),'score':judged,'effect':effect,
                'stored_bytes':len(note.encode()) if note is not None else None,'truncated':truncated}
    def batch(fn):
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:return list(pool.map(fn,data))
    def text_field(row,key):
        try:
            value=json.loads(row['response'])
            if row['terminal'] and type(value)is dict and set(value)=={key} and type(value[key])is str and len(value[key].encode())<=12000:
                return value[key]
        except (ValueError,TypeError):pass
        return None
    try:
        full=batch(lambda c:receiver(c,'full-history',full=True))
        flat=batch(lambda c:receiver(c,'flat-negative',flat_note(c)))
        full_gate=sum(r['primary'] for r in full)>=3 and all(r['score']['safe'] for r in full)
        negative_gate=sum(r['primary'] for r in flat)<=2
        prepared=[];levels=[];selected=None
        if full_gate and negative_gate:
            def prepare(c):
                p=target(c,'prime',prime_prompt());approach=text_field(p,'approach')
                if approach is None:return {'case':c['id'],'valid':False,'reason':'invalid-approach'}
                s=target(c,'whole-sender',prepared_sender_prompt(c,approach));note=text_field(s,'handoff')
                if note is None:return {'case':c['id'],'valid':False,'reason':'invalid-handoff'}
                return {'case':c['id'],'valid':True,'approach':approach,'whole_note':note,
                        'approach_sha256':sha(approach.encode()),'whole_note_sha256':sha(note.encode())}
            prepared=batch(prepare)
            if all(r['valid'] for r in prepared):
                notes={r['case']:r['whole_note'] for r in prepared}
                for limit in LIMITS:
                    def step(c):
                        note,truncated=stored_note(notes[c['id']],limit)
                        return receiver(c,'receiver-'+str(limit),note,truncated=truncated)
                    group=batch(step);good=sum(r['primary'] for r in group);safe=sum(r['score']['safe'] for r in group)
                    passed=1<=good<=3 and safe>=2
                    levels.append({'limit':limit,'results':group,'passed':passed})
                    if passed:selected=limit;break
        raw=(HERE/'responses.jsonl').read_bytes()
        result={'schema':'transfer-calibration-results/3','source_commit':commit,
                'freeze_sha256':sha((HERE/'freeze.json').read_bytes()),'raw_sha256':sha(raw),
                'captured_calls':len(observed),'full_history':full,'flat_negative':flat,
                'full_history_gate':full_gate,'negative_gate':negative_gate,'prepared':prepared,
                'levels':levels,'selected_limit':selected,
                'main_study_status':'not-run; separate registration required',
                'status':'instrument-qualified-on-development' if selected else 'instrument-not-qualified',
                'held_out_inference_calls':0,'book_condition_calls':0,'wall_seconds':round(time.perf_counter()-began,3),
                'requested_model':'gpt-6.1-sol','reasoning_effort':'high',
                'limits':['one finite planning class','four dependent development instances','developer-authored law and evaluators','single requested GPT route','no independent validation']}
        (HERE/'responses.jsonl.gz').write_bytes(gzip.compress(raw,mtime=0))
        (HERE/'results.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({k:v for k,v in result.items() if k!='prepared'}))
    finally:output.close()


if __name__=='__main__':
    if sys.argv[1:]==['freeze']:freeze()
    elif sys.argv[1:]==['run']:execute()
    else:raise SystemExit('use freeze or run')
