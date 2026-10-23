"""Local experiment world: real SQLite rows, simulated channel semantics.

No resident system or external transaction is touched. The experimenter supplies
the hidden mode; it is not a claim of naturally measured service behavior.
"""
from __future__ import annotations
from contextlib import contextmanager
import json
from pathlib import Path
import sqlite3
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'examples'))
from continuity import Event
from durable import Journal,DEFAULT,operation,event_operation,canonical,digest
from task_design import sha


class Environment:
    def __init__(self,path,case,rows):
        self.path=Path(path);self.case=case
        with self.path.open('xb'):pass
        with self.connect() as db:
            db.executescript('CREATE TABLE ops(operation TEXT NOT NULL);')
            db.execute('INSERT INTO ops VALUES (?)',('sentinel-committed',))
            for row in rows:
                found=row['receipt']=='FOUND' or row['owner_receipt']=='PRESENT'
                absent=row['owner_receipt']=='ABSENT'
                matching=row['deployment']==case['deployment'] and row['epoch']==case['epoch']
                # Other scopes have their own unknown owner/cache contract.
                present=found or (not absent and ((matching and case['mode']=='cache' and
                    (case['present'] if row['id']=='source-uncertain' else int(sha(row['id'].encode())[:2],16)%2==0))
                    or (not matching and int(sha(row['id'].encode())[:2],16)%2==0)))
                if present:db.execute('INSERT INTO ops VALUES (?)',(row['id'],))

    @contextmanager
    def connect(self):
        db=sqlite3.connect(self.path)
        try:
            with db:yield db
        finally:db.close()

    def count(self,key):
        with self.connect() as db:
            return db.execute('SELECT count(*) FROM ops WHERE operation=?',(key,)).fetchone()[0]

    def probe(self,which):
        out={'deployment':self.case['deployment'],'epoch':self.case['epoch'],
             'probe':which,'cost':0,'events':[]}
        if which=='sentinel':
            n=self.count('sentinel-committed')
            if n!=1:raise ValueError('sentinel-not-exactly-committed')
            out.update(cost=1,events=[{'id':'sentinel-authority','kind':'owner-attestation',
                'operation':'sentinel-committed','owner_receipt':'PRESENT'},
                {'id':'sentinel-channel','kind':'status-read','operation':'sentinel-committed',
                 'reply':'FOUND' if self.case['mode']=='owner' and n else 'NOT_FOUND'}])
        elif which=='current_owner':
            out.update(cost=6,events=[{'id':'current-owner-read','kind':'owner-read',
                'operation':'source-uncertain','owner_receipt':'PRESENT' if self.count('source-uncertain') else 'ABSENT'}])
        elif which!='none':raise ValueError('unknown-probe')
        return out

    def apply(self,rows,answer,terminal):
        effects=[]
        for row in rows:
            action=answer['answers'][row['id']]['action'] if terminal and answer else None
            with self.connect() as db:
                db.execute('BEGIN IMMEDIATE')
                before=db.execute('SELECT count(*) FROM ops WHERE operation=?',(row['id'],)).fetchone()[0]
                cost=0;complete=False;bad=None
                if action=='confirm':
                    complete=before>0
                    if not complete:bad='false-confirmation'
                elif action=='retry':
                    cost=1
                    if not before or not row['deduplicated']:
                        db.execute('INSERT INTO ops VALUES (?)',(row['id'],))
                    complete=True
                    if before and not row['deduplicated']:bad='duplicate'
                elif action=='reconcile':
                    cost=row['reconcile_cost']
                    if not before:db.execute('INSERT INTO ops VALUES (?)',(row['id'],))
                    complete=True
                elif action not in ('defer',None):raise ValueError('unknown-action')
                after=db.execute('SELECT count(*) FROM ops WHERE operation=?',(row['id'],)).fetchone()[0]
            value=(-40-cost if bad else ((row['reward'] if complete else 0)-cost))
            effects.append({'task':row['id'],'action':action,'before_count':before,'after_count':after,
                'completed':complete,'cost':cost,'bad_effect':bad,'realized_utility':value})
        return effects


def persist_memory(path,memory):
    """Use the existing journal/CAS, reopen, recover exact admitted bytes.

    Original visible model output is archived separately, including refusals.
    This stores data only: event structure cannot certify a model interpretation.
    """
    journal=Journal(path,create=True)
    _,tail=journal.read()
    tail=journal.append(operation('init','init',actor='participant',orientation=DEFAULT),expected=tail['head'])
    wire=canonical(memory).decode('utf-8')
    chunks=[wire[i:i+800] for i in range(0,len(wire),800)]
    for i,chunk in enumerate(chunks):
        # Event basis is a tuple, never the untrusted linked-memory field.
        e=Event(f'memory-{i}','participant','main','observation','saved-memory','recorded',chunk,
                'experiment',(),origin='model-visible-output')
        tail=journal.append(event_operation(e),expected=tail['head'])
    del journal
    state,read_tail=Journal(path).read(anchor=tail)
    restored=''.join(state['main'][0].events[f'memory-{i}'].text for i in range(len(chunks)))
    if restored!=wire:raise ValueError('memory-readback-drift')
    return json.loads(restored),{'head':read_tail['head'],'seq':read_tail['seq'],
        'wire_sha256':sha(wire.encode()),'wire_bytes':len(wire.encode()),'reopened':True}
