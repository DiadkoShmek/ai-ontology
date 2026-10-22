"""Registered reading -> public approach -> handoff -> held-out planning study."""
import concurrent.futures
from datetime import datetime,timezone
import gzip
import hashlib
import json
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import threading
import time

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(HERE.parent/'transfer_calibration_v3'))
from tasks import (brute,cases,planning_success,prepared_sender_prompt,prime_prompt,
                   receiver_prompt,recursive,score,stored_note)
sys.path.insert(0,str(HERE.parent/'gpt_profile_pilot_v2'))
from run import command,invoke

ARMS=('ordinary','book','guide','unrelated')
READINGS={'book':'BOOK_READING_UA.md','guide':'OPERATIONAL_GUIDE_UA.md','unrelated':'UNRELATED_READING_UA.txt'}
REPETITIONS=2
SCHEDULE_SEED=9541
LOCK=threading.Lock()


def sha(raw):return hashlib.sha256(raw).hexdigest()


def held_cases():return [c for c in cases() if c['split']=='held-out']


def schedule():
    pairs=[[c['id'],a,r] for c in held_cases() for r in range(REPETITIONS) for a in ARMS]
    random.Random(SCHEDULE_SEED).shuffle(pairs)
    return pairs


def pins():
    names=['study.py','analyze.py','test_study.py','PROTOCOL.md','cases.json',
           'BOOK_READING_UA.md','OPERATIONAL_GUIDE_UA.md','UNRELATED_READING_UA.txt',
           'UNRELATED_READING_SOURCE_UA.txt','reading-provenance.json',
           'unrelated-reading-provenance.json','THIRD_PARTY_READING.md',
           'prepare_control.py','length-preparation.json',
           '../transfer_calibration_v3/tasks.py','../transfer_calibration_v3/cases.json',
           '../transfer_calibration_v3/freeze.json','../transfer_calibration_v3/results.json',
           '../../examples/continuity.py','../../examples/durable.py',
           '../gpt_profile_pilot_v2/run.py','../gpt_profile_pilot_v2/design.py',
           '../participation_pilot/design.py']
    return {p:sha((HERE/p).read_bytes()) for p in names}


def freeze():
    if (HERE/'freeze.json').exists():raise ValueError('already-frozen')
    cal=json.loads((HERE.parent/'transfer_calibration_v3/results.json').read_text())
    if cal['selected_limit']is None or cal['held_out_inference_calls'] or cal['book_condition_calls']:
        raise ValueError('calibration-not-qualified-or-held-out-already-used')
    prep=json.loads((HERE/'length-preparation.json').read_text())
    if prep['status']!='matched' or prep['unrelated']['relative_difference']>0.01:
        raise ValueError('unmatched-reading-control')
    material=[]
    for c in held_cases():
        a=brute(c);b=recursive(c)
        if {k:a[k] for k in b}!=b:raise ValueError('solver-disagreement')
        material.append({'source':c,'oracle':a})
    (HERE/'cases.json').write_text(json.dumps(material,indent=2)+'\n')
    value={'schema':'reading-transfer-freeze/1','created_at':datetime.now(timezone.utc).isoformat(),
           'input_sha256':pins(),'requested_model':'gpt-6.1-sol','reasoning_effort':'high',
           'command_template':command('{isolated-temporary-working-directory}'),
           'arms':list(ARMS),'repetitions':REPETITIONS,'schedule':schedule(),
           'capacity':cal['selected_limit'],'held_out_instances':8,'source_clusters':4,
           'episodes':64,'maximum_participant_calls':192,'full_history_control_calls':8,
           'maximum_total_calls':200,'unscored_length_preparation_calls':prep['unscored_calls'],
           'independent_registration':False,'prior_qualifications_not_main_evidence':True}
    (HERE/'freeze.json').write_text(json.dumps(value,indent=2)+'\n')
    print(json.dumps({'registered':True,'episodes':64,'maximum_calls':200,'sha256':sha((HERE/'freeze.json').read_bytes())}))


def field(row,key):
    def unique(pairs):
        value={}
        for k,v in pairs:
            if k in value:raise ValueError('duplicate-key')
            value[k]=v
        return value
    try:
        d=json.loads(row['response'],object_pairs_hook=unique)
        if row['terminal'] and type(d)is dict and set(d)=={key} and type(d[key])is str and len(d[key].encode())<=12000:
            return d[key]
    except (ValueError,TypeError):pass
    return None


def artifact(folder,name,raw):
    p=folder/name
    with p.open('xb') as stream:stream.write(raw)
    if p.read_bytes()!=raw:raise ValueError('artifact-readback')
    return {'name':name,'sha256':sha(raw),'bytes':len(raw)}


def run():
    frozen=json.loads((HERE/'freeze.json').read_text())
    if frozen['input_sha256']!=pins() or frozen['schedule']!=schedule():raise ValueError('frozen-input-drift')
    paths=[str((HERE/p).relative_to(ROOT)) for p in frozen['input_sha256']]+[str((HERE/'freeze.json').relative_to(ROOT))]
    if subprocess.check_output(['git','status','--porcelain','--',*paths],cwd=ROOT):raise ValueError('inputs-not-committed')
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    readings={'ordinary':'',**{a:(HERE/p).read_text() for a,p in READINGS.items()}}
    indexed={c['id']:c for c in held_cases()};capacity=frozen['capacity']
    output=(HERE/'responses.jsonl').open('x');calls=[];began=time.perf_counter()
    def target(c,arm,rep,stage,prompt):
        observed=invoke(prompt)
        row={'case':c['id'],'arm':arm,'repetition':rep,'stage':stage,
             'prompt':prompt,'prompt_sha256':sha(prompt.encode()),**observed}
        with LOCK:
            calls.append(row);output.write(json.dumps(row,ensure_ascii=False)+'\n');output.flush()
            print(json.dumps({'calls':len(calls),'maximum':200,'case':c['id'],'arm':arm,'repetition':rep,'stage':stage}),flush=True)
        return row
    def finish(c,row,folder):
        evaluated=score(c,row['response'],row['terminal'])
        effect={'written':False}
        if evaluated['safe']:
            plan=json.loads(row['response'])['plan']
            raw=json.dumps({'case':c['id'],'plan':plan},sort_keys=True).encode()
            effect={'written':True,**artifact(folder,'plan.json',raw),'plan':plan}
        return {'score':evaluated,'primary':planning_success(evaluated,c),'plan_effect':effect}
    def control(c):
        row=target(c,'full-history',-1,'receiver',receiver_prompt(c,full=True))
        with tempfile.TemporaryDirectory(prefix='reading-full-history-') as work:
            return {'case':c['id'],**finish(c,row,Path(work))}
    def episode(spec):
        cid,arm,rep=spec;c=indexed[cid]
        base={'case':cid,'seed':c['seed'],'variant':c['variant'],'arm':arm,'repetition':rep,'artifacts':[],
              'primary':False,'score':{'shape':False,'safe':False,'traceable':False,'optimal':False,'utility':0,'cost':0},
              'plan_effect':{'written':False}}
        with tempfile.TemporaryDirectory(prefix='reading-transfer-') as work:
            folder=Path(work)
            first=target(c,arm,rep,'prime',prime_prompt(readings[arm]));approach=field(first,'approach')
            if approach is None:return {**base,'failure_stage':'prime'}
            base['artifacts'].append(artifact(folder,'approach.txt',approach.encode()))
            sent=target(c,arm,rep,'sender',prepared_sender_prompt(c,approach));whole=field(sent,'handoff')
            if whole is None:return {**base,'failure_stage':'sender'}
            base['artifacts'].append(artifact(folder,'whole-note.txt',whole.encode()))
            note,truncated=stored_note(whole,capacity)
            base['artifacts'].append(artifact(folder,'stored-note.txt',note.encode()))
            row=target(c,arm,rep,'receiver',receiver_prompt(c,note,truncated=truncated))
            return {**base,**finish(c,row,folder),'failure_stage':None if row['terminal'] else 'receiver',
                    'truncated':truncated,'whole_note_bytes':len(whole.encode()),'stored_note_bytes':len(note.encode())}
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:controls=list(pool.map(control,held_cases()))
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:episodes=list(pool.map(episode,frozen['schedule']))
        raw=(HERE/'responses.jsonl').read_bytes()
        (HERE/'responses.jsonl.gz').write_bytes(gzip.compress(raw,mtime=0))
        (HERE/'episodes.json').write_text(json.dumps({'controls':controls,'episodes':episodes},indent=2)+'\n')
        result={'schema':'reading-transfer-completion/1','source_commit':commit,'captured_calls':len(calls),
                'planned_episodes':64,'recorded_episodes':len(episodes),'full_history_controls':len(controls),
                'freeze_sha256':sha((HERE/'freeze.json').read_bytes()),'raw_sha256':sha(raw),
                'episodes_sha256':sha((HERE/'episodes.json').read_bytes()),'input_pins_after':pins(),
                'source_unchanged':pins()==frozen['input_sha256'],'wall_seconds':round(time.perf_counter()-began,3),
                'completed_at':datetime.now(timezone.utc).isoformat()}
        (HERE/'completion.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(result))
    finally:output.close()


if __name__=='__main__':
    if sys.argv[1:]==['freeze']:freeze()
    elif sys.argv[1:]==['run']:run()
    else:raise SystemExit('use freeze or run')
