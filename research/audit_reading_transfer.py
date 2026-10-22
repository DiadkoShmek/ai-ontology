"""Post-cohort descriptive diagnosis; never changes registered scores."""
import gzip
import hashlib
import json
from pathlib import Path
import re
import statistics

HERE=Path(__file__).resolve().parent
BASE=HERE/'transfer_reading'


def derive():
    raw=gzip.decompress((BASE/'responses.jsonl.gz').read_bytes())
    rows=[json.loads(line) for line in raw.splitlines()]
    episodes=json.loads((BASE/'episodes.json').read_text())['episodes']
    gold={c['source']['id']:c['oracle'] for c in json.loads((BASE/'cases.json').read_text())}
    indexed={(r['case'],r['arm'],r['repetition'],r['stage']):r for r in rows}
    summaries=[];named=[]
    for arm in ('ordinary','book','guide','unrelated'):
        selected=[e for e in episodes if e['arm']==arm]
        approaches=[json.loads(r['response'])['approach'] for r in rows if r['arm']==arm and r['stage']=='prime']
        words=[len(x.split()) for x in approaches]
        empty_named=0
        for e in selected:
            if not e['plan_effect'].get('written') or e['plan_effect']['plan']:continue
            response=json.loads(indexed[e['case'],arm,e['repetition'],'receiver']['response'])
            identifiers=sorted(set(re.findall(r'\bW\d{2}\b',response['reason'])))
            if identifiers and identifiers in gold[e['case']]['plans']:
                empty_named+=1
                named.append({'case':e['case'],'arm':arm,'repetition':e['repetition'],'named_ids':identifiers,
                              'reason':response['reason'],'registered_primary':e['primary']})
        summaries.append({'arm':arm,'approach_word_range':[min(words),max(words)],
                          'outside_requested_150_300_words':sum(not 150<=n<=300 for n in words),
                          'whole_note_bytes_median':statistics.median(e['whole_note_bytes'] for e in selected if 'whole_note_bytes'in e),
                          'empty_plan_reason_names_exact_oracle_set':empty_named})
    return {'schema':'reading-transfer-posthoc-diagnostics/1','posthoc':True,
            'raw_sha256':hashlib.sha256(raw).hexdigest(),
            'inputs':{p:hashlib.sha256((HERE/p).read_bytes()).hexdigest() for p in
                      ('transfer_reading/episodes.json','transfer_reading/cases.json','audit_reading_transfer.py')},
            'summary':summaries,'empty_plan_named_sets':named,
            'scope':'Literal ID-set matches in public reasons, not a semantic judge or an alternative success score. Empty plans remain registered failures.'}


if __name__=='__main__':
    result=derive();(BASE/'diagnostics.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result['summary']))
