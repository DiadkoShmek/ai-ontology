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
    import analyze
    # This public edition changes only the author credit of a frozen license
    # note. Preserve the original freeze and recorded completion verbatim.
    # The exact permitted derivative is pinned independently below; no model
    # prompt, output, score, timestamp or scientific input is substituted.
    derivative_path=HERE/'privacy-derivative.json'
    derivative=json.loads(derivative_path.read_text())
    if derivative != {
        'schema':'author-privacy-derivative/1',
        'path':'THIRD_PARTY_READING.md',
        'original_sha256':'324effab5cb0575384a152520cd25506d795920b832e8f03b94f4c9c0d50859d',
        'published_sha256':'11f3330fc08702d4e760307fe3f7eda9ed20f17431a2f7b9325209a879d9d4be',
        'change':'Author-credit pseudonymization only; third-party attribution and license terms unchanged.',
    }:raise ValueError('unrecognized author-privacy derivative')
    original_pins=analyze.pins
    def recorded_pins():
        actual=original_pins()
        if actual[derivative['path']] != derivative['published_sha256']:
            raise ValueError('author-privacy derivative drift')
        actual[derivative['path']]=derivative['original_sha256']
        return actual
    analyze.pins=recorded_pins
    result=analyze.derive()
    if result!=json.loads((HERE/'results.json').read_text()):raise ValueError('saved analysis drift')
    from audit_reading_transfer import derive as derive_diagnostics
    if derive_diagnostics()!=json.loads((HERE/'diagnostics.json').read_text()):raise ValueError('post-cohort diagnostics drift')
    print(json.dumps({'captured_calls':result['captured_calls'],'episodes':result['participant_episodes'],
                      'internally_consistent':True,'privacy_derivative':str(derivative_path.relative_to(ROOT)),
                      'scope':'Recorded scientific hashes and results unchanged. One disclosed author-credit derivative accepted; not a rerun, external replication or provider attestation.'}))


if __name__=='__main__':main()
