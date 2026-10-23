"""Post-cohort literal memory-budget diagnosis; no inference or regrading.

Frozen analysis remains unchanged. This descriptive supplement cannot repair
lost notes, claim a larger budget result or replace the registered endpoints.
"""
from collections import Counter
import gzip
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
HERE=ROOT/'research/epistemic_return'
sys.path.insert(0,str(HERE))
from task_design import canonical,sha


def diagnose():
    wire=gzip.decompress((HERE/'responses.jsonl.gz').read_bytes())
    rows=[json.loads(line) for line in wire.splitlines()]
    models=[r for r in rows if r.get('kind')!='runtime']
    index={(r['case'],r['arm'],r['stage']):r for r in models}
    source=json.loads((HERE/'results.json').read_text())
    cases={r['case']:r['mode'] for r in source['details']}
    notes=[]
    for row in rows:
        if row.get('kind')!='runtime':continue
        m=index[(row['case'],row['arm'],1)]
        supplied=json.loads(m['response'])['memory']
        size=len(supplied.encode()) if type(supplied)is str else len(canonical(supplied))
        admission=row['admitted_memory']
        notes.append({'case':row['case'],'mode':cases[row['case']],'arm':row['arm'],
            'supplied_bytes':size,'unavailable_reason':admission.get('unavailable') if type(admission)is dict else None,
            'admitted_wire_bytes':row['readback']['wire_bytes'],
            'source_response_sha256':sha(m['response'].encode())})
    grouped=[]
    for arm in source['arms']:
        xs=[n for n in notes if n['arm']==arm]
        grouped.append({'arm':arm,'notes':len(xs),'accepted':sum(n['unavailable_reason'] is None for n in xs),
            'refusal_reasons':dict(Counter(n['unavailable_reason'] for n in xs if n['unavailable_reason'])),
            'minimum_supplied_bytes':min(n['supplied_bytes'] for n in xs),
            'maximum_supplied_bytes':max(n['supplied_bytes'] for n in xs)})
    return {'schema':'epistemic-return-post-cohort-diagnosis/1',
        'status':'descriptive-only-no-regrading','raw_sha256':sha(wire),
        'registered_results_sha256':sha((HERE/'results.json').read_bytes()),
        'all_model_calls_including_canary':len(models),'nonterminal_calls':sum(not r['terminal'] for r in models),
        'total_usage':{k:sum(r.get('usage',{}).get(k,0) for r in models) for k in ('input_tokens','cached_input_tokens','output_tokens')},
        'shared_diagnostic_cost':sum(r['diagnostic']['cost'] for r in rows if r.get('kind')=='runtime')/4,
        'memory_admission':grouped,'notes':notes,
        'limits':['literal byte counts and refusal reasons, not independent semantic evaluation',
                  'does not estimate results with a larger budget or a repaired writer',
                  'all-or-nothing admission is part of this tested system, not inherent to all ontologies']}


if __name__=='__main__':
    x=diagnose()
    (ROOT/'research/epistemic-return-diagnosis.json').write_text(json.dumps(x,indent=2)+'\n')
    print(json.dumps({'memory_admission':x['memory_admission'],'total_usage':x['total_usage']}))
