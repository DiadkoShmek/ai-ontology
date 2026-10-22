"""Explicit local-only experiment. Download models separately; no auto-pull.

freeze -> commit inputs -> run once -> analyze. Raw rows are append-only and
failed requests count as failures. No provider fallback or automatic retry.
"""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import random
import subprocess
import sys
import time
import urllib.request

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from design import ARMS,material,messages,score

BASE="http://127.0.0.1:11434"
MODELS=("qwen3:4b-instruct-2507-q4_K_M","granite3.3:2b")
OPTIONS={"temperature":0,"seed":317,"num_ctx":8192,"num_predict":128}


def sha(b):return hashlib.sha256(b).hexdigest()


def request(path,data=None,timeout=60):
    body=None if data is None else json.dumps(data).encode()
    req=urllib.request.Request(BASE+path,data=body,
        headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req,timeout=timeout) as r:
        raw=r.read(4*1024*1024+1)
    if len(raw)>4*1024*1024:raise ValueError('backend-response-limit')
    return json.loads(raw)


def inputs():
    return {str(p.relative_to(HERE.parents[1])):sha(p.read_bytes()) for p in [
        HERE/'design.py',HERE/'run.py',HERE/'analyze.py',HERE/'cases.json',HERE/'PROTOCOL.md',
        *(HERE.parents[1]/'examples'/n for n in ('continuity.py','durable.py','agent_cycle.py'))]}


def model_rows():
    tags=request('/api/tags')['models']
    by_name={x['name']:x for x in tags}
    selected=[]
    for name in MODELS:
        if name not in by_name:raise ValueError('model-not-installed:'+name)
        show=request('/api/show',{'model':name})
        t=by_name[name]
        selected.append({'name':name,'digest':t['digest'],'size':t['size'],
            'details':t.get('details'),
            'template_sha256':sha(show.get('template','').encode()),
            'parameters_sha256':sha('\n'.join(sorted(show.get('parameters','').splitlines())).encode()),
            'capabilities':show.get('capabilities')})
    return selected


def freeze():
    p=HERE/'freeze.json'
    if p.exists():raise ValueError('already-frozen')
    cases=json.loads((HERE/'cases.json').read_text())
    for c in cases:material(c)
    value={'schema':'continuity-pilot-freeze/1','created_at':datetime.now(timezone.utc).isoformat(),
           'input_sha256':inputs(),'models':model_rows(),'backend':request('/api/version'),
           'options':OPTIONS,'cases':len(cases),'arms':list(ARMS),'scored_calls':len(cases)*len(ARMS)*len(MODELS),
           'schedule_seed':317,'independent_registration':False}
    p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'frozen':value['scored_calls'],'sha256':sha(p.read_bytes())}))


def run():
    frozen=json.loads((HERE/'freeze.json').read_text())
    if frozen['input_sha256']!=inputs():raise ValueError('frozen-input-drift')
    if frozen['models']!=model_rows():raise ValueError('model-drift')
    output=HERE/'responses.jsonl'
    if output.exists():raise ValueError('existing-results-no-automatic-resume')
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=HERE).decode().strip()
    # Refuse uncommitted changes in the declared materials before scoring.
    root=HERE.parents[1]
    paths=list(frozen['input_sha256'])+[str((HERE/'freeze.json').relative_to(root))]
    if subprocess.check_output(['git','status','--porcelain','--',*paths],cwd=root):
        raise ValueError('frozen-inputs-not-committed')
    cases=json.loads((HERE/'cases.json').read_text())
    start=time.perf_counter();count=0
    with output.open('x') as out:
        for model in MODELS:
            # A declared neutral warm-up, not a scored or tuned example.
            warm=request('/api/chat',{'model':model,'messages':[{'role':'user','content':'Return JSON {"ready":true}'}],
                         'format':'json','stream':False,'options':OPTIONS,'keep_alive':'10m'},timeout=90)
            (HERE/('warmup-'+str(MODELS.index(model))+'.json')).write_text(json.dumps({
                k:v for k,v in warm.items() if k!='message'},indent=2)+'\n')
            schedule=[(c,a) for c in cases for a in ARMS]
            random.Random(frozen['schedule_seed']).shuffle(schedule)
            for case,arm in schedule:
                prompts=messages(case,arm)
                payload={'model':model,'messages':prompts,'format':'json','stream':False,
                         'options':OPTIONS,'keep_alive':'10m'}
                row={'model':model,'case':case['id'],'family':case['family'],'arm':arm,
                     'input_commit':commit,'request_sha256':sha(json.dumps(payload,sort_keys=True).encode()),
                     'messages':prompts,'started_at':datetime.now(timezone.utc).isoformat()}
                t=time.perf_counter()
                try:
                    answer=request('/api/chat',payload,timeout=60)
                    # Only the final visible answer is retained. Never request
                    # or store a private reasoning field.
                    content=answer.get('message',{}).get('content','')
                    terminal=answer.get('done') is True and answer.get('done_reason')=='stop' and answer.get('model')==model
                    row.update(response=content,terminal=terminal,
                        backend={k:answer.get(k) for k in ('model','done','done_reason','total_duration','load_duration',
                            'prompt_eval_count','prompt_eval_cached_count','prompt_eval_duration','eval_count','eval_duration')},
                        score=score(content,case['gold']))
                    row['score']['exact']=row['score']['exact'] and terminal
                except Exception as exc:
                    row.update(error=type(exc).__name__,terminal=False,
                               score={'exact':False,'shape':False,'fields':{}})
                row['wall_ms']=round((time.perf_counter()-t)*1000,3)
                out.write(json.dumps(row,ensure_ascii=False,sort_keys=True)+'\n');out.flush()
                count+=1
                print(json.dumps({'completed':count,'total':frozen['scored_calls'],'model':model,
                    'case':case['id'],'arm':arm,'exact':row['score']['exact'],'elapsed_s':round(time.perf_counter()-start,1)}),flush=True)
            # Release only the model this run loaded; do not stop Ollama or
            # alter another resident model's keep-alive policy.
            request('/api/generate',{'model':model,'keep_alive':0})
    if frozen['models']!=model_rows():raise ValueError('model-drift-after-run')
    (HERE/'completion.json').write_text(json.dumps({'input_commit':commit,'scored_calls':count,
        'response_sha256':sha(output.read_bytes()),'wall_seconds':time.perf_counter()-start,
        'models_unchanged':True,'completed_at':datetime.now(timezone.utc).isoformat()},indent=2)+'\n')


if __name__=='__main__':
    {'freeze':freeze,'run':run}[sys.argv[1]]()
