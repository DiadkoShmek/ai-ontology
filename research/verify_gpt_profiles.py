"""Offline GPT cohort reconstruction. No inference, provider access or key reads."""
import gzip
import hashlib
import json
from pathlib import Path
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]


def require(value,reason):
    if not value:raise ValueError(reason)


def verify(name):
    here=ROOT/'research'/name
    frozen=json.loads((here/'freeze.json').read_text())
    for p,pin in frozen['input_sha256'].items():
        require(hashlib.sha256((here/p).read_bytes()).hexdigest()==pin,'source drift: '+p)
    sys.path.insert(0,str(here))
    from design import ARMS,cases,evaluate,target_prompt
    from run import command,effect,schedule
    require(frozen['command_template']==command('{isolated-temporary-working-directory}'),'command drift')
    require(frozen['schedule']==schedule(),'schedule drift')
    require(json.loads((here/'cases.json').read_text())==cases(),'case drift')
    require(frozen['requested_model']=='gpt-6.1-sol' and frozen['reasoning_effort']=='high','route mismatch')
    raw=gzip.decompress((here/'responses.jsonl.gz').read_bytes())
    if (here/'responses.jsonl').exists():require(raw==(here/'responses.jsonl').read_bytes(),'archive/raw drift')
    rows=[json.loads(line) for line in raw.splitlines()]
    keyed={(r['case'],r['arm'],r['stage']):r for r in rows}
    require(len(keyed)==len(rows),'duplicate turn')
    short=(here/'METHOD_UA.md').read_text();long=(here/'READING_UA.md').read_text()
    checked=0
    for c in cases():
      for arm in ARMS:
        previous=[]
        with tempfile.TemporaryDirectory() as folder:
          for i in range(len(c['stages'])):
            key=c['id'],arm,i
            if key not in keyed:
                require(not any((c['id'],arm,j) in keyed for j in range(i+1,len(c['stages']))),'gapped episode')
                break
            r=keyed[key];checked+=1
            require(r['model']==frozen['requested_model'] and r['kind']==c['kind'] and r['family']==c['family'],'turn metadata drift')
            prompt=target_prompt(c,arm,i,previous,short,long)
            require(r['prompt']==prompt and r['prompt_sha256']==hashlib.sha256(prompt.encode()).hexdigest(),'prompt/history drift')
            terminal=bool(any(e.get('type')=='turn.completed' for e in r['events']) and r.get('exit_code')==0 and
                          not r['tools'] and not r.get('unparsed_stdout') and
                          not any(e.get('type') in ('turn.failed','error') for e in r['events']))
            require(r['terminal']==terminal,'terminal drift')
            scored=evaluate(c,i,r['response'],terminal)
            require(scored==r['score'],'score drift')
            require(effect(Path(folder),c,i,scored,terminal)==r['effect'],'effect drift')
            previous.append({'response':r['response'],'effect':r['effect']})
    require(checked==len(rows),'unexpected turn')
    digest=hashlib.sha256(raw).hexdigest()
    if name=='gpt_profile_pilot':
        stopped=json.loads((here/'interruption.json').read_text())
        require(stopped['observed_complete_rows']==len(rows)==53 and stopped['raw_sha256']==digest,'partial archive drift')
        require(all(not r['terminal'] and not r['score']['correct'] for r in rows),'strict interrupted scores drift')
        status='partial-instrument-failure'
    else:
        from analyze import derive
        completion=json.loads((here/'completion.json').read_text())
        require(len(rows)==completion['calls']==frozen['scored_calls']==100,'completed coverage mismatch')
        require(completion['raw_sha256']==digest,'completed archive drift')
        require(derive()==json.loads((here/'results.json').read_text()),'analysis drift')
        status='completed'
    print(json.dumps({'cohort':name,'captured_turns':checked,'status':status,'internally_consistent':True,
                      'scope':'Published source, prompts, visible replies, native completion metadata, deterministic scores and fixture effects; not independent replication or backend attestation.'}))


if __name__=='__main__':
    if len(sys.argv)!=2 or sys.argv[1] not in ('gpt_profile_pilot','gpt_profile_pilot_v2'):
        raise SystemExit('supply gpt_profile_pilot or gpt_profile_pilot_v2')
    verify(sys.argv[1])
