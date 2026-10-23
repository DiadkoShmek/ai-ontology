"""Descriptive supplement to the frozen analyzer; never changes registered scores."""
from collections import defaultdict
import gzip,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
HERE=ROOT/'research/closed_loop'

def main():
    report=json.loads((HERE/'results.json').read_text())
    rows=json.loads((HERE/'transfer.json').read_text())
    groups=defaultdict(list)
    for r in rows:groups[(r['arm'],r['version'],r['transfer_variant'])].append(r)
    variants=[{'arm':arm,'version':version,'variant':variant,'executions':len(rs),
      'optimal':sum(r['score']['optimal_plan'] for r in rs),
      'safe':sum(r['score']['safe'] for r in rs),
      'benefit':sum(r['score']['benefit'] for r in rs),
      'available_benefit':sum(r['score']['optimal_benefit'] for r in rs)}
      for (arm,version,variant),rs in sorted(groups.items())]
    changes=[{'arm':arm,**{k:sum(r[k] for r in report['method_revisions'] if r['arm']==arm)
      for k in ('behavior_changed','newly_optimal','regressed','benefit_change')}}
      for arm in ('ordinary_loop','ontology_loop')]
    a,b=report['summary']
    out={'schema':'closed-loop-descriptive-supplement/1','registered_results_unchanged':True,
      'variants':variants,'changes':changes,
      'input_relative_change':b['input_tokens']/a['input_tokens']-1,
      'output_relative_change':b['output_tokens']/a['output_tokens']-1,
      'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
        for p in [HERE/'results.json',HERE/'transfer.json',Path(__file__)]},
      'boundary':'Post-cohort descriptive grouping of the frozen outcomes. No new model trials, regrading or population inference.'}
    (ROOT/'research/closed-loop-supplement.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out))
if __name__=='__main__':main()
