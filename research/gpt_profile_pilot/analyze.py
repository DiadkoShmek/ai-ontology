"""Offline exact re-scoring of the strong GPT profile pilot."""
import gzip
import hashlib
import json
from pathlib import Path
from design import ARMS,cases,evaluate,target_prompt
from run import effect,pins,schedule
import tempfile

HERE=Path(__file__).resolve().parent


def derive():
    frozen=json.loads((HERE/'freeze.json').read_text())
    if frozen['input_sha256']!=pins():raise ValueError('input-drift')
    if json.loads((HERE/'cases.json').read_text())!=cases():raise ValueError('case-drift')
    zipped=gzip.decompress((HERE/'responses.jsonl.gz').read_bytes())
    if (HERE/'responses.jsonl').exists() and (HERE/'responses.jsonl').read_bytes()!=zipped:raise ValueError('archive-drift')
    rows=[json.loads(line) for line in zipped.splitlines()]
    keyed={(r['case'],r['arm'],r['stage']):r for r in rows}
    expected={(c['id'],a,i) for c in cases() for a in ARMS for i in range(len(c['stages']))}
    if len(rows)!=100 or len(keyed)!=100 or set(keyed)!=expected:raise ValueError('incomplete-or-duplicate')
    completion=json.loads((HERE/'completion.json').read_text())
    if completion['raw_sha256']!=hashlib.sha256(zipped).hexdigest() or completion['calls']!=100:raise ValueError('completion-drift')
    if completion['freeze_sha256']!=hashlib.sha256((HERE/'freeze.json').read_bytes()).hexdigest():raise ValueError('freeze-drift')
    short=(HERE/'METHOD_UA.md').read_text();long=(HERE/'READING_UA.md').read_text()
    for c in cases():
      for a in ARMS:
        prev=[]
        with tempfile.TemporaryDirectory() as folder:
          for i in range(len(c['stages'])):
            r=keyed[c['id'],a,i]
            p=target_prompt(c,a,i,prev,short,long)
            if p!=r['prompt'] or hashlib.sha256(p.encode()).hexdigest()!=r['prompt_sha256']:raise ValueError('request-drift')
            scored=evaluate(c,i,r['response'],r['terminal'])
            if scored!=r['score']:raise ValueError('score-drift')
            emitted=effect(Path(folder),c,i,scored,r['terminal'])
            if emitted!=r['effect']:raise ValueError('effect-drift')
            prev.append({'response':r['response'],'effect':r['effect']})
    summaries=[];paired=[]
    for kind in ('qualification','coupled'):
      selected_cases=[c for c in cases() if c['kind']==kind]
      groups=[]
      for a in ARMS:
        selected=[r for r in rows if r['kind']==kind and r['arm']==a]
        episodes={c['id']:all(keyed[c['id'],a,i]['score']['correct'] for i in range(len(c['stages']))) for c in selected_cases}
        group={'kind':kind,'arm':a,'episodes':len(episodes),'complete_episodes_correct':sum(episodes.values()),
          'stages':len(selected),'stages_correct':sum(r['score']['correct'] for r in selected),
          'actions_correct':sum(r['score']['action_correct'] and r['terminal'] for r in selected),
          'records_correct':sum(r['score']['record_correct'] and r['terminal'] for r in selected) if kind=='coupled' else None,
          'invalid':sum(not r['score']['shape'] for r in selected),'nonterminal':sum(not r['terminal'] for r in selected),
          'errors':sum('error' in r for r in selected),'tool_items':sum(len(r['tools']) for r in selected),
          'plans_written':sum(r['effect']['plan_written'] for r in selected),
          'unnecessary_ask':sum(r['score']['choice']=='ASK' and (c['expected_choices'][r['stage']] if kind=='qualification' else c['expected'][r['stage']]['action'])!='ASK' for r in selected for c in selected_cases if c['id']==r['case']),
          'input_tokens':sum(r.get('usage',{}).get('input_tokens',0) for r in selected),
          'cached_input_tokens':sum(r.get('usage',{}).get('cached_input_tokens',0) for r in selected),
          'output_tokens':sum(r.get('usage',{}).get('output_tokens',0) for r in selected),
          'wall_ms':round(sum(r['wall_ms'] for r in selected),3),'episode_results':episodes}
        summaries.append(group);groups.append(group)
      delta=[int(groups[1]['episode_results'][c['id']])-int(groups[0]['episode_results'][c['id']]) for c in selected_cases]
      paired.append({'kind':kind,'wins':delta.count(1),'losses':delta.count(-1),'ties':delta.count(0)})
    return {'schema':'gpt-profile-pilot-results/1','model':frozen['requested_model'],'reasoning_effort':frozen['reasoning_effort'],
      'scored_calls':100,'route_canaries':1,'raw_sha256':hashlib.sha256(zipped).hexdigest(),'summary':summaries,'paired':paired,
      'scope':'Profile enactment and coupled-transition qualification; not natural voice, consciousness or a full-book effect.',
      'limits':['developer-authored dependent cases and gold','known qualification set; newly authored coupled cases',
                'single requested model route, no independent backend attestation','fresh calls with supplied visible history, not a continuous autonomous agent',
                'length, Ukrainian reading and conceptual content confounded','no independent judge or replication','native usage includes substantial fixed Codex harness overhead']}


if __name__=='__main__':
    result=derive();(HERE/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
