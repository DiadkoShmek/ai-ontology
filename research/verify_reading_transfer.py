"""Offline verification of the registered reading-transfer cohort."""
import gzip
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
HERE=ROOT/'research/transfer_reading'


def main():
    rows=[json.loads(line) for line in gzip.decompress((HERE/'responses.jsonl.gz').read_bytes()).splitlines()]
    for row in rows:
        completed=[event for event in row['events'] if event.get('type')=='turn.completed']
        if completed and row.get('usage',{})!=completed[-1].get('usage',{}):
            raise ValueError('native usage metadata drift')
    sys.path.insert(0,str(HERE))
    from analyze import derive
    result=derive()
    if result!=json.loads((HERE/'results.json').read_text()):raise ValueError('saved analysis drift')
    from audit_reading_transfer import derive as derive_diagnostics
    if derive_diagnostics()!=json.loads((HERE/'diagnostics.json').read_text()):raise ValueError('post-cohort diagnostics drift')
    print(json.dumps({'captured_calls':result['captured_calls'],'episodes':result['participant_episodes'],
                      'internally_consistent':True,'scope':'Frozen inputs, actual preparation/carry chain, native completion, scores and artifact effects; not external replication or provider attestation.'}))


if __name__=='__main__':main()
