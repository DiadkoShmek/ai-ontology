"""Run ontology/instrument checks in separate interpreters; never call a model."""
from datetime import datetime,timezone
import hashlib,json,platform,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
    commands=[['ontology/export.py','--check'],
      ['-m','unittest','discover','-s','ontology','-p','test_*.py','-q'],
      ['-O','-m','unittest','discover','-s','ontology','-p','test_*.py','-q'],
      ['-m','unittest','discover','-s','research/closed_loop','-q']]
    rows=[]
    for args in commands:
        result=subprocess.run([sys.executable,*args],cwd=ROOT,text=True,capture_output=True)
        rows.append({'args':args,'exit_code':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
    sources=sorted([p for folder in ('ontology','research/closed_loop') for p in (ROOT/folder).rglob('*')
      if p.is_file() and '__pycache__' not in p.parts and p.suffix in ('.py','.md','.ttl','.json','.jsonld')
      and p.name not in ('results.json','completion.json','transfer.json')])
    sources+=[Path(__file__),ROOT/'examples/participation.py',ROOT/'examples/participation_method.py']
    report={'schema':'ontology-foundation-checks/1','observed_at':datetime.now(timezone.utc).isoformat(),
      'python':platform.python_version(),'llm_calls':0,'authored_fixture':True,
      'success':all(r['exit_code']==0 for r in rows),'runs':rows,
      'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
      'boundary':'Mechanical developer checks; the authored full-loop test double is not model evidence. Optimized-mode repeats are not additional independent tests.'}
    (ROOT/'research/foundation-checks.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'success':report['success'],'output':'research/foundation-checks.json'}))
    return 0 if report['success'] else 1
if __name__=='__main__':raise SystemExit(main())
