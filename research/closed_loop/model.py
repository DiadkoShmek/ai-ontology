"""Explicit subscription CLI route; no API keys, fallback or outcome retries."""
from pathlib import Path
import importlib.util
import json
import os
import signal
import subprocess
import tempfile
import time

PRIOR=Path(__file__).resolve().parents[1]/'gpt_profile_pilot_v2/run.py'
# The prior module imports design.py; use only its exact inspected command.
import sys
sys.path.insert(0,str(PRIOR.parent))
spec=importlib.util.spec_from_file_location('prior_closed_loop_route',PRIOR)
prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)
command=prior.command
MODEL='gpt-6.1-sol'


def invoke(prompt):
    begin=time.perf_counter();out={'response':'','terminal':False,'events':[],'tools':[]}
    with tempfile.TemporaryDirectory(prefix='ontology-closed-loop-target-') as work:
        p=subprocess.Popen(command(work),stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                           text=True,start_new_session=True)
        try:
            stdout,stderr=p.communicate(prompt,timeout=150)
        except subprocess.TimeoutExpired:
            os.killpg(p.pid,signal.SIGTERM)
            try:stdout,stderr=p.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(p.pid,signal.SIGKILL);stdout,stderr=p.communicate()
            out['error']={'kind':'timeout','seconds':150,'owned_process_group_reaped':True}
        out['exit_code']=p.returncode
        # Omit provider stderr from the public archive; classify errors by native events.
        out['stderr_present']=bool(stderr.strip())
        messages=[];done=False;failed=False
        for line in stdout.splitlines():
            try:e=json.loads(line)
            except ValueError:
                failed=True;out['unparsed_stdout']=True;continue
            kind=e.get('type');item=e.get('item',{})
            if kind=='thread.started':out['thread_id']=e.get('thread_id')
            if kind=='turn.completed':done=True;out['usage']=e.get('usage',{})
            if kind in ('turn.failed','error'):failed=True;out['error']=e
            if kind=='item.completed' and item.get('type')=='agent_message':messages.append(item.get('text',''))
            if item and item.get('type') not in ('agent_message','reasoning'):
                out['tools'].append({'event':kind,'item_type':item.get('type')})
            if kind in ('turn.completed','turn.failed','error'):out['events'].append(e)
        out['response']='\n'.join(messages)
        out['terminal']=bool(done and not failed and p.returncode==0 and not out['tools'] and 'error' not in out)
    out['wall_ms']=round((time.perf_counter()-begin)*1000,3)
    return out
