"""Explicit authenticated GPT study. No key reads, fallback or outcome retries."""
import concurrent.futures
from datetime import datetime,timezone
import gzip
import hashlib
import json
from pathlib import Path
import random
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from design import ARMS,cases,evaluate,target_prompt

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
DISABLED=('hooks','memories','multi_agent','plugins','apps','shell_tool',
          'unified_exec','browser_use','code_mode_host','in_app_browser','computer_use')
MODEL='gpt-6.1-sol'
SEED=947
LOCK=threading.Lock()


def sha(raw):return hashlib.sha256(raw).hexdigest()


def command(work):
    cmd=['codex','exec','--ignore-user-config','--ephemeral','--skip-git-repo-check',
         '-C',str(work),'-m',MODEL,'-c','model_reasoning_effort="high"',
         '-c','project_doc_max_bytes=0','-c','web_search="disabled"']
    for f in DISABLED:cmd+=['--disable',f]
    return cmd+['--json','-']


def pins():
    paths=['PROTOCOL.md','design.py','run.py','analyze.py','test_design.py',
           'METHOD_UA.md','READING_UA.md','cases.json']
    d={p:sha((HERE/p).read_bytes()) for p in paths}
    d['../participation_pilot/design.py']=sha((HERE.parent/'participation_pilot/design.py').read_bytes())
    return d


def schedule():
    s=[[c['id'],arm] for c in cases() for arm in ARMS]
    random.Random(SEED).shuffle(s)
    return s


def freeze():
    if (HERE/'freeze.json').exists():raise ValueError('already-frozen')
    (HERE/'METHOD_UA.md').write_bytes((HERE.parent/'participation_pilot/METHOD_UA.md').read_bytes())
    chapters=['01-core.md','03-relations.md','04-continuity.md','10-method.md']
    (HERE/'READING_UA.md').write_text('\n\n'.join((ROOT/'book/ua'/p).read_text() for p in chapters))
    (HERE/'cases.json').write_text(json.dumps(cases(),ensure_ascii=False,indent=2)+'\n')
    launcher=Path(shutil.which('codex')).resolve()
    preflight=json.loads((ROOT/'build/gpt-route-preflight/result.json').read_text())
    if preflight['exit_code']!=0 or not any(e.get('item',{}).get('text')=='{"ready":true}' for e in preflight['events']):
        raise ValueError('route-preflight-not-ready')
    value={'schema':'gpt-profile-pilot-freeze/1','created_at':datetime.now(timezone.utc).isoformat(),
      'input_sha256':pins(),'cases':20,'scored_calls':100,'qualification_calls':68,'coupled_calls':32,
      'schedule':schedule(),'requested_model':MODEL,'reasoning_effort':'high',
      'cli_version':subprocess.check_output(['codex','--version'],text=True).strip(),
      'cli_launcher_sha256':sha(launcher.read_bytes()),'command_template':command('{isolated-temporary-working-directory}'),
      'preflight':preflight,'chapter_sources':{p:sha((ROOT/'book/ua'/p).read_bytes()) for p in chapters},
      'independent_registration':False,'parent_chat_transferred':False,'gold_transferred':False}
    (HERE/'freeze.json').write_text(json.dumps(value,indent=2)+'\n')
    print(json.dumps({'frozen':100,'freeze_sha256':sha((HERE/'freeze.json').read_bytes())}))


def invoke(prompt):
    start=time.perf_counter()
    result={'response':'','terminal':False,'tools':[],'events':[]}
    try:
        with tempfile.TemporaryDirectory(prefix='ontology-gpt-target-') as work:
            r=subprocess.run(command(work),input=prompt,text=True,capture_output=True,timeout=120)
        result['exit_code']=r.returncode
        result['stderr']=r.stderr[-4000:]
        messages=[]
        for line in r.stdout.splitlines():
            try:e=json.loads(line)
            except ValueError:
                result.setdefault('unparsed_stdout',[]).append(line);continue
            kind=e.get('type')
            if kind=='thread.started':result['thread_id']=e['thread_id']
            if kind=='turn.completed':result['usage']=e.get('usage',{});result['terminal']=True
            if kind in ('turn.failed','error'):
                result['error']=e;result['terminal']=False
            item=e.get('item',{})
            if kind=='item.completed' and item.get('type')=='agent_message':messages.append(item['text'])
            if item and item.get('type') not in ('agent_message','reasoning'):
                result['tools'].append({'event':kind,'item':item})
            if kind in ('thread.started','turn.completed','turn.failed','error'):
                result['events'].append(e)
        result['response']='\n'.join(messages)
        result['terminal']=bool(result['terminal'] and r.returncode==0 and not result['tools'] and not result.get('unparsed_stdout'))
        if r.returncode:result.setdefault('error',{'exit_code':r.returncode})
    except subprocess.TimeoutExpired:
        result['error']={'kind':'timeout','seconds':120}
    except Exception as e:
        result['error']={'kind':type(e).__name__,'message':str(e)}
    result['wall_ms']=round((time.perf_counter()-start)*1000,3)
    return result


def effect(folder,case,index,scored,terminal):
    if not terminal or not scored['shape']:return {'plan_written':False,'reason':'invalid-or-incomplete'}
    choice=scored['choice']
    if choice=='ASK':return {'plan_written':False,'reason':'deferred'}
    action=case['stages'][index]['actions'][choice]
    if not action['available']:return {'plan_written':False,'reason':'unavailable-choice-refused'}
    body={'case':case['id'],'stage':index,'choice':choice,'action':action}
    raw=json.dumps(body,sort_keys=True).encode()
    target=folder/('plan-'+str(index)+'.json')
    with target.open('xb') as stream:stream.write(raw)
    if target.read_bytes()!=raw:raise ValueError('plan-readback-mismatch')
    return {'plan_written':True,'sha256':sha(raw),'body':body}


def run():
    f=json.loads((HERE/'freeze.json').read_text())
    if f['input_sha256']!=pins() or f['schedule']!=schedule():raise ValueError('frozen-input-drift')
    paths=[str((HERE/p).relative_to(ROOT)) for p in f['input_sha256']]+[str((HERE/'freeze.json').relative_to(ROOT))]
    if subprocess.check_output(['git','status','--porcelain','--',*paths],cwd=ROOT):raise ValueError('inputs-not-committed')
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    short=(HERE/'METHOD_UA.md').read_text();long=(HERE/'READING_UA.md').read_text()
    indexed={c['id']:c for c in cases()}
    output=(HERE/'responses.jsonl').open('x');count=0;began=time.perf_counter()
    def episode(pair):
        nonlocal count
        cid,arm=pair;case=indexed[cid];previous=[]
        with tempfile.TemporaryDirectory(prefix='ontology-gpt-effect-') as work:
            for i in range(len(case['stages'])):
                text=target_prompt(case,arm,i,previous,short,long)
                observed=invoke(text)
                scored=evaluate(case,i,observed['response'],observed['terminal'])
                emitted=effect(Path(work),case,i,scored,observed['terminal'])
                row={'model':MODEL,'case':cid,'kind':case['kind'],'family':case['family'],
                     'arm':arm,'stage':i,'prompt':text,'prompt_sha256':sha(text.encode()),
                     **observed,'score':scored,'effect':emitted}
                previous.append({'response':observed['response'],'effect':emitted})
                with LOCK:
                    output.write(json.dumps(row,ensure_ascii=False)+'\n');output.flush();count+=1
                    print(json.dumps({'completed':count,'total':100,'case':cid,'arm':arm,'stage':i}),flush=True)
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            list(pool.map(episode,f['schedule']))
    finally:output.close()
    raw=(HERE/'responses.jsonl').read_bytes()
    (HERE/'responses.jsonl.gz').write_bytes(gzip.compress(raw,mtime=0))
    completion={'schema':'gpt-profile-pilot-completion/1','calls':count,'source_commit':commit,
                'freeze_sha256':sha((HERE/'freeze.json').read_bytes()),'raw_sha256':sha(raw),
                'wall_seconds':round(time.perf_counter()-began,3),'completed_at':datetime.now(timezone.utc).isoformat()}
    (HERE/'completion.json').write_text(json.dumps(completion,indent=2)+'\n')
    print(json.dumps(completion))


if __name__=='__main__':
    if sys.argv[1:] == ['freeze']:freeze()
    elif sys.argv[1:] == ['run']:run()
    else:raise SystemExit('use freeze or run')
