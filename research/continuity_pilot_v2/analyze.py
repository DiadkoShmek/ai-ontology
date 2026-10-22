"""Recompute descriptive results from visible responses and frozen manual gold."""
import hashlib
import json
from pathlib import Path
import random
import statistics
from design import ARMS,FAMILIES,score

HERE=Path(__file__).resolve().parent


def main():
    cases={c['id']:c for c in json.loads((HERE/'cases.json').read_text())}
    frozen=json.loads((HERE/'freeze.json').read_text())
    rows=[json.loads(x) for x in (HERE/'responses.jsonl').read_text().splitlines()]
    unique={(r['model'],r['case'],r['arm']) for r in rows}
    if len(unique)!=len(rows):raise ValueError('duplicate trial')
    expected={(m['name'],c,a) for m in frozen['models'] for c in cases for a in ARMS}
    if unique!=expected:raise ValueError('incomplete or extra cohort')
    for row in rows:
        evaluated=score(row.get('response',''),cases[row['case']]['gold'])
        if bool(evaluated['exact'] and row.get('terminal'))!=row['score']['exact']:
            raise ValueError('score drift')
    summary=[];comparisons=[]
    for model in [m['name'] for m in frozen['models']]:
        for arm in ARMS:
            subset=[r for r in rows if r['model']==model and r['arm']==arm]
            summary.append({'model':model,'arm':arm,'n':len(subset),
                'correct':sum(r['score']['exact'] for r in subset),
                'shape_valid':sum(r['score']['shape'] for r in subset),
                'errors':sum('error' in r for r in subset),
                'median_wall_ms':statistics.median(r['wall_ms'] for r in subset),
                'input_tokens':sum(r.get('backend',{}).get('prompt_eval_count') or 0 for r in subset),
                'output_tokens':sum(r.get('backend',{}).get('eval_count') or 0 for r in subset),
                'families':{f:{'n':4,'correct':sum(r['score']['exact'] for r in subset if r['family']==f)} for f in FAMILIES}})
        keyed={(r['case'],r['arm']):r for r in rows if r['model']==model}
        for a,b in [('ontology_prompt','journal'),('compiled','journal'),('compiled','simple_index')]:
            ds={f:[int(keyed[c,a]['score']['exact'])-int(keyed[c,b]['score']['exact']) for c in cases if cases[c]['family']==f] for f in FAMILIES}
            values=[x for xs in ds.values() for x in xs];rng=random.Random(317)
            boot=[]
            for _ in range(5000):
                draw=[f for f in rng.choices(FAMILIES,k=len(FAMILIES))]
                boot.append(statistics.mean(x for f in draw for x in ds[f]))
            boot.sort()
            comparisons.append({'model':model,'a':a,'b':b,'n':24,
                'wins':sum(x==1 for x in values),'losses':sum(x==-1 for x in values),
                'ties':sum(x==0 for x in values),'difference':statistics.mean(values),
                'exploratory_family_cluster_interval_95':[boot[124],boot[4874]]})
    report={'schema':'continuity-pilot-results/1','kind':'developer-run-authored-diagnostic-pilot',
        'n_cases':24,'n_families':6,'n_models':2,'n_calls':len(rows),'summary':summary,'paired':comparisons,
        'raw_sha256':hashlib.sha256((HERE/'responses.jsonl').read_bytes()).hexdigest(),
        'freeze_sha256':hashlib.sha256((HERE/'freeze.json').read_bytes()).hexdigest(),
        'limits':['synthetic and author-scored','not independent','six dependent family clusters',
                  'not a voice or consciousness test','compiled preprocessing not isolated ontology effect']}
    (HERE/'results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'calls':len(rows),'summary':[{k:r[k] for k in ('model','arm','correct','n','input_tokens')} for r in summary]}))


if __name__=='__main__':main()
