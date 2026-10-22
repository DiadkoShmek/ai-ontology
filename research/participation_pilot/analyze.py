"""Recompute all participation choices and descriptive comparisons; no inference."""
import gzip
import hashlib
import json
from pathlib import Path
from design import ARMS, FAMILIES, score

HERE = Path(__file__).resolve().parent


def derive():
    cases = {c['id']: c for c in json.loads((HERE/'cases.json').read_text())}
    frozen = json.loads((HERE/'freeze.json').read_text())
    path = HERE/'responses.jsonl'
    raw = path.read_bytes() if path.exists() else gzip.decompress((HERE/'responses.jsonl.gz').read_bytes())
    rows = [json.loads(line) for line in raw.splitlines()]
    expected = {(model['name'], c['id'], arm, i) for model in frozen['models']
                for c in cases.values() for arm in ARMS for i in range(len(c['stages']))}
    keyed = {(r['model'], r['case'], r['arm'], r['stage']): r for r in rows}
    if len(rows) != len(keyed) or set(keyed) != expected or len(rows) != 136:
        raise ValueError('incomplete-or-duplicate-cohort')
    for r in rows:
        evaluated = score(r.get('response', ''), cases[r['case']]['expected_choices'][r['stage']])
        evaluated['correct'] = bool(evaluated['correct'] and r['terminal'])
        if evaluated != r['score']:
            raise ValueError('score-drift')
    summaries = []
    for model in frozen['models']:
        name = model['name']
        for arm in ARMS:
            selected = [r for r in rows if r['model'] == name and r['arm'] == arm]
            episodes = {c: all(keyed[name, c, arm, i]['score']['correct']
                              for i in range(len(cases[c]['stages']))) for c in cases}
            summaries.append({'model': name, 'arm': arm, 'episodes': 16,
                'complete_episodes_correct': sum(episodes.values()),
                'stages': len(selected), 'stages_correct': sum(r['score']['correct'] for r in selected),
                'shape_valid': sum(r['score']['shape'] for r in selected),
                'nonterminal': sum(not r['terminal'] for r in selected),
                'errors': sum('error' in r for r in selected),
                'unnecessary_ask': sum(r['score']['choice']=='ASK' and cases[r['case']]['expected_choices'][r['stage']]!='ASK' for r in selected),
                'plans_written': sum(r['effect']['plan_written'] for r in selected),
                'unavailable_choices_blocked': sum(r['effect'].get('reason')=='unavailable-choice-refused' for r in selected),
                'counterfactual_pairs_both_initial_correct': sum(all(keyed[name, f+'-'+p, arm, 0]['score']['correct']
                    for p in ('learning','reproducibility')) for f in FAMILIES),
                'family_complete_episodes': {f: sum(episodes[c] for c in cases if cases[c]['family']==f) for f in FAMILIES},
                'input_tokens': sum(r.get('backend', {}).get('prompt_eval_count') or 0 for r in selected),
                'output_tokens': sum(r.get('backend', {}).get('eval_count') or 0 for r in selected),
                'wall_ms': round(sum(r['wall_ms'] for r in selected), 3),
                'episode_results': episodes})
    paired = []
    for model in frozen['models']:
        groups = [g for g in summaries if g['model'] == model['name']]
        first, second = groups
        changes = [int(second['episode_results'][c])-int(first['episode_results'][c]) for c in cases]
        paired.append({'model': model['name'], 'a': ARMS[1], 'b': ARMS[0],
                       'wins': changes.count(1), 'losses': changes.count(-1), 'ties': changes.count(0),
                       'episode_difference': sum(changes)/16})
    return {'schema': 'participation-pilot-results/1', 'scored_calls': len(rows),
        'families': 8, 'episodes_per_condition_model': 16, 'unscored_warmups': 2,
        'raw_sha256': hashlib.sha256(raw).hexdigest(), 'summary': summaries, 'paired': paired,
        'scope': 'Developer-authored functional contract-enactment qualification, not consciousness or autonomous value formation.',
        'limits': ['eight dependent families', 'two small quantized models, one seed',
                   'added method also adds text and Ukrainian reading load', 'no independent validation',
                   'constrained choices and artificial plan effects', 'brief reasons are not scored as natural voice']}


if __name__ == '__main__':
    result = derive()
    (HERE/'results.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps([{k: r[k] for k in ('model','arm','complete_episodes_correct','stages_correct','input_tokens')}
                      for r in result['summary']]))
