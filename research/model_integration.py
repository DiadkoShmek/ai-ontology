"""Two explicit real-model smoke turns through the book's actual run_turn.

Local loopback only; separate from both diagnostic cohorts. No auto-download,
retry, external tools or provider selection. Only final visible text is saved.
"""
from dataclasses import asdict
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'examples'))
from agent_cycle import ModelReply,run_turn
from continuity import read_fixture
from durable import DEFAULT,ZERO,Journal,event_operation,operation

MODELS=['qwen3:4b-instruct-2507-q4_K_M','granite3.3:2b']


def call(path,payload=None):
    req=urllib.request.Request('http://127.0.0.1:11434'+path,data=None if payload is None else json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=60) as f:return json.load(f)


def observed_models():
    tags={r['name']:r for r in call('/api/tags')['models']}
    rows=[]
    for name in MODELS:
        t=tags[name];show=call('/api/show',{'model':name})
        rows.append({'name':name,'digest':t['digest'],'size':t['size'],'details':t.get('details'),
            'template_sha256':hashlib.sha256(show.get('template','').encode()).hexdigest(),
            'parameters_sha256':hashlib.sha256('\n'.join(sorted(show.get('parameters','').splitlines())).encode()).hexdigest(),
            'capabilities':show.get('capabilities')})
    return rows


class LocalModel:
    def __init__(self,name):self.name=name;self.backend=None
    def complete(self,messages):
        reply=call('/api/chat',{'model':self.name,'messages':list(messages),'stream':False,
            'format':{'type':'object','additionalProperties':False,'required':['text','stance','cites'],
                      'properties':{'text':{'type':'string'},'stance':{'type':'string','enum':['answer','abstain','dissent']},
                                    'cites':{'type':'array','items':{'type':'string'}}}},
            'options':{'temperature':0,'seed':317,'num_ctx':8192,'num_predict':192},'keep_alive':'2m'})
        self.backend={k:reply.get(k) for k in ['done','done_reason','model','prompt_eval_count','eval_count','total_duration']}
        if reply.get('done_reason')!='stop':raise ValueError('incomplete-model-turn')
        return ModelReply(reply['model'],reply['message']['content'],reply.get('prompt_eval_count'),reply.get('eval_count'))


def main():
    output=ROOT/'research/model-integration-results.json'
    if output.exists():raise ValueError('existing-smoke-results')
    pins=json.loads((ROOT/'research/continuity_pilot_v2/freeze.json').read_text())['models']
    if observed_models()!=pins:raise ValueError('model-drift-before-smoke')
    results=[]
    for name in MODELS:
        with tempfile.TemporaryDirectory() as d:
            j=Journal(Path(d)/'state.sqlite',create=True)
            tail=j.append(operation('init','init',actor='iris',orientation=DEFAULT),expected=ZERO)
            for e in read_fixture():tail=j.append(event_operation(e),expected=tail['head'])
            adapter=LocalModel(name)
            before=j.read()[1]
            try:
                result=run_turn(j,turn_id='real-turn',branch='main',topic='cache-current',scope='updates-A',
                    question='Explain what the latest test changes, what remains unknown, and cite the relevant events.',
                    model=adapter,expected_model_id=name)
                after=j.read()[1]
                results.append({'model':name,'status':'committed','before_seq':before['seq'],'after_seq':after['seq'],
                                'result':result,'backend':adapter.backend})
            except Exception as exc:
                results.append({'model':name,'status':'rejected','error':type(exc).__name__+':'+str(exc),
                                'before_seq':before['seq'],'after_seq':j.read()[1]['seq'],'backend':adapter.backend})
        call('/api/generate',{'model':name,'keep_alive':0})
    sources=[ROOT/'examples/agent_cycle.py',ROOT/'examples/durable.py',ROOT/'examples/continuity.py',Path(__file__)]
    unchanged=observed_models()==pins
    output.write_text(json.dumps({'kind':'developer-observed-real-model-integration-smoke',
        'observed_at':datetime.now(timezone.utc).isoformat(),'llm_calls':len(MODELS),'model_pins':pins,
        'model_pins_unchanged':unchanged,
        'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        'results':results,'limits':['two smoke turns, not behavioral validation','no independent observer','no general voice or identity result']},ensure_ascii=False,indent=2)+'\n')
    print(json.dumps([{'model':x['model'],'status':x['status']} for x in results]))


if __name__=='__main__':main()
