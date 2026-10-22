"""Reconstruct the sensitivity calibration from saved visible data, offline."""
import gzip
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
HERE=ROOT/'research'/(sys.argv[1] if len(sys.argv)==2 else 'transfer_calibration')
if HERE.name not in ('transfer_calibration','transfer_calibration_v2','transfer_calibration_v3'):
    raise SystemExit('supply transfer_calibration, transfer_calibration_v2 or transfer_calibration_v3')


def require(value,reason):
    if not value:raise ValueError(reason)


def verify():
    f=json.loads((HERE/'freeze.json').read_text())
    for name,pin in f['input_sha256'].items():require(hashlib.sha256((HERE/name).read_bytes()).hexdigest()==pin,'source drift: '+name)
    sys.path.insert(0,str(HERE))
    from tasks import brute,cases,flat_note,receiver_prompt,recursive,score,sender_prompt
    prepared_mode=HERE.name=='transfer_calibration_v3'
    if prepared_mode:
        from tasks import planning_success,prepared_sender_prompt,prime_prompt,stored_note
    material=json.loads((HERE/'cases.json').read_text())
    require(material==[{'source':c,'oracle':brute(c)} for c in cases()],'material derivation drift')
    for c in cases():
        a=brute(c);b=recursive(c);require({k:a[k] for k in b}==b,'oracle disagreement')
    raw=gzip.decompress((HERE/'responses.jsonl.gz').read_bytes())
    if (HERE/'responses.jsonl').exists():require(raw==(HERE/'responses.jsonl').read_bytes(),'archive/raw mismatch')
    result=json.loads((HERE/'results.json').read_text())
    require(result['raw_sha256']==hashlib.sha256(raw).hexdigest(),'raw hash mismatch')
    require(result['freeze_sha256']==hashlib.sha256((HERE/'freeze.json').read_bytes()).hexdigest(),'freeze mismatch')
    rows=[json.loads(x) for x in raw.splitlines()];keyed={(r['case'],r['phase']):r for r in rows}
    require(len(rows)==len(keyed)==result['captured_calls'],'duplicate/call count')
    data={c['id']:c for c in cases() if c['split']=='development'}
    require(all(r['case']in data for r in rows),'held-out inference')
    indexed={}
    note_metadata={}
    for row in rows:
        c=data[row['case']];phase=row['phase']
        note=None;cut=False
        if phase=='full-history':prompt=receiver_prompt(c,full=True)
        elif phase=='flat-negative':note=flat_note(c);prompt=receiver_prompt(c,note)
        elif prepared_mode and phase=='prime':prompt=prime_prompt()
        elif prepared_mode and phase=='whole-sender':
            approach=json.loads(keyed[c['id'],'prime']['response'])['approach']
            prompt=prepared_sender_prompt(c,approach)
        elif phase.startswith('sender-'):prompt=sender_prompt(c,int(phase.split('-')[1]))
        elif phase.startswith('receiver-'):
            limit=int(phase.split('-')[1])
            if prepared_mode:
                sent=keyed[c['id'],'whole-sender'];whole=json.loads(sent['response'])['handoff']
                note,cut=stored_note(whole,limit);prompt=receiver_prompt(c,note,truncated=cut)
            else:
                sent=keyed[c['id'],'sender-'+str(limit)]
                note=json.loads(sent['response'])['handoff'];require(len(note.encode())<=limit,'oversize note delivered')
                prompt=receiver_prompt(c,note)
        else:raise ValueError('unknown phase')
        require(row['prompt']==prompt and row['prompt_sha256']==hashlib.sha256(prompt.encode()).hexdigest(),'prompt/history drift')
        terminal=bool(any(e.get('type')=='turn.completed' for e in row['events']) and row.get('exit_code')==0 and
                      not row['tools'] and not row.get('unparsed_stdout') and not any(e.get('type') in ('turn.failed','error') for e in row['events']))
        require(row['terminal']==terminal,'terminal metadata drift')
        if phase in ('full-history','flat-negative') or phase.startswith('receiver-'):
            indexed[row['case'],phase]=score(c,row['response'],row['terminal'])
            note_metadata[row['case'],phase]=(len(note.encode()) if note is not None else None,cut)
    def group(values,phase):
        require({r['case'] for r in values}==set(data),'group coverage')
        for row in values:
            if not row.get('handoff_valid',True):
                require(not row['score']['optimal'] and not row['effect']['written'],'invalid handoff score')
                continue
            evaluated=indexed[row['case'],phase]
            require(row['score']==evaluated,'score drift')
            if prepared_mode:
                require(row['primary']==planning_success(evaluated,data[row['case']]),'primary drift')
                require((row['stored_bytes'],row['truncated'])==note_metadata[row['case'],phase],'stored channel drift')
            native=keyed[row['case'],phase]
            expected={'written':False}
            if evaluated['safe'] and (prepared_mode or evaluated['traceable']):
                plan=json.loads(native['response'])['plan'];body=json.dumps({'case':row['case'],'plan':plan},sort_keys=True).encode()
                expected={'written':True,'sha256':hashlib.sha256(body).hexdigest(),'plan':plan}
            require(row['effect']==expected,'effect drift')
    group(result['full_history'],'full-history');group(result['flat_negative'],'flat-negative')
    full=result['full_history'];flat=result['flat_negative']
    metric=lambda r:r['primary'] if prepared_mode else r['score']['optimal']
    full_gate=sum(metric(r) for r in full)>=3 and all(r['score']['safe'] for r in full) and (prepared_mode or sum(r['score']['traceable'] for r in full)>=3)
    neg_gate=sum(metric(r) for r in flat)<=2
    require(result['full_history_gate']==full_gate and result['negative_gate']==neg_gate,'control gate drift')
    if prepared_mode:
        for r in result['prepared']:
            if not r['valid']:continue
            require(r['approach']==json.loads(keyed[r['case'],'prime']['response'])['approach'],'prepared approach drift')
            require(r['whole_note']==json.loads(keyed[r['case'],'whole-sender']['response'])['handoff'],'prepared note drift')
            require(r['approach_sha256']==hashlib.sha256(r['approach'].encode()).hexdigest() and r['whole_note_sha256']==hashlib.sha256(r['whole_note'].encode()).hexdigest(),'prepared hash drift')
    chosen=None
    for i,level in enumerate(result['levels']):
        require(full_gate and neg_gate and level['limit']==f['limits'][i] and chosen is None,'level/stopping drift')
        group(level['results'],'receiver-'+str(level['limit']))
        good=sum(metric(r) for r in level['results']);safe=sum(r['score']['safe'] for r in level['results'])
        passed=1<=good<=3 and safe>=2
        require(level['passed']==passed,'level gate drift')
        if passed:chosen=level['limit']
    require(chosen==result['selected_limit'],'selection drift')
    require(result['book_condition_calls']==result['held_out_inference_calls']==0,'scope drift')
    print(json.dumps({'calls':len(rows),'controls':{'full':sum(metric(r) for r in full),'flat':sum(metric(r) for r in flat)},'selected_limit':chosen,'internally_consistent':True,'scope':'Sensitivity calibration only; no book effect or independent replication.'}))


if __name__=='__main__':verify()
