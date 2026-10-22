"""Historical source excerpt; see provenance.json and receipt_replay.py."""
from common import Path, os, re, read_file, strict_json, digest, atomic, wire, ReferenceValidationError, RecordedEventConflict, _reference_details
HOMES = {}  # Explicit fixture bindings are supplied by the replay.

def _reconcile_inbox(journal,actor,event,input_sha):
 # Failure returning from append says nothing about whether COMMIT happened.
 # Exact durable identity is historical evidence, not fresh evidence validation.
 unknown={'status':'UNCONFIRMED','actor':actor,'reason':'append-unconfirmed','inputSha256':input_sha,'appendOutcome':'UNKNOWN','retryAppend':False}
 try:recorded=journal.recorded_event(actor,event)
 except RecordedEventConflict:
  return {'status':'REFUSED','actor':actor,'reason':'idempotency-conflict','inputSha256':input_sha}
 except Exception:return unknown
 if recorded is None:return unknown
 return {**recorded,'status':'recorded','actor':actor,'inputSha256':input_sha,'reconciled':True}

def _inbox_status(journal,actor,p,side):
 # (receipt, persist, charge): count unknown readbacks even if no receipt changes.
 # An existing uncertainty fence must survive errors reading either file.
 def unknown(reason):
  return {'status':'UNCONFIRMED','actor':actor,'reason':reason,'inputSha256':None,'appendOutcome':'UNKNOWN','retryAppend':False},False,True
 previous=None
 if os.path.lexists(side):
  try:
   previous=strict_json(read_file(side,16384))
   if (type(previous) is not dict or type(previous.get('status')) is not str or previous['status'] not in {'recorded','REFUSED','UNCONFIRMED'}
       or previous.get('actor')!=actor or type(previous.get('inputSha256')) is not str
       or re.fullmatch('[a-f0-9]{64}',previous['inputSha256']) is None
       or previous['status']=='UNCONFIRMED' and (previous.get('appendOutcome')!='UNKNOWN' or previous.get('retryAppend') is not False)):
    return unknown('receipt-unreadable')
  except (OSError,ValueError,UnicodeError):return unknown('receipt-unreadable')
 raw=None
 try:
  raw=read_file(p,16384);input_sha=digest(raw)
  if previous is not None:
   if previous['status']=='UNCONFIRMED' and previous['inputSha256']!=input_sha:return unknown('input-changed-after-unknown')
   if previous['status']!='UNCONFIRMED' and previous['inputSha256']==input_sha:return None,False,False
  event=strict_json(raw)
  if type(event) is not dict or event.get('id')!=p.stem:raise ValueError('filename-id-mismatch')
 except (OSError,ValueError,UnicodeError) as error:
  if previous is not None:return unknown('input-unavailable')
  return {'status':'REFUSED','actor':actor,'reason':str(error)[:100],'inputSha256':digest(raw) if raw is not None else None},True,True
 if previous is not None and previous['status']=='UNCONFIRMED':
  receipt=_reconcile_inbox(journal,actor,event,input_sha)
  return (None,False,True) if receipt==previous else (receipt,True,True)
 try:
  receipt=journal.append(actor,event);receipt.update(status='recorded',actor=actor,inputSha256=input_sha)
 except ReferenceValidationError as error:
  details=_reference_details(error)
  if details is None:receipt=_reconcile_inbox(journal,actor,event,input_sha)
  else:receipt={'status':'REFUSED','actor':actor,'reason':str(error),'inputSha256':input_sha,**details}
 except Exception:receipt=_reconcile_inbox(journal,actor,event,input_sha)
 return receipt,True,True

def drain(journal,homes=HOMES):
 rows=[]
 # Retain bounded directory iterators across ticks. Completed history cannot hide
 # new entries behind the first eight names; a full pass restarts on a later tick.
 if not hasattr(journal,'_scans'):journal._scans={}
 for actor,home in homes.items():
  folder=home/'shared-memory-inbox'
  if not folder.is_dir() or any(p.is_symlink() for p in (folder,*folder.parents)):continue
  scan=journal._scans.get(actor)
  if scan is None:scan=os.scandir(folder);journal._scans[actor]=scan
  handled=0
  for _ in range(128):
   try:p=Path(next(scan).path)
   except StopIteration:
    scan.close();journal._scans.pop(actor,None);break
   if not re.fullmatch('[a-f0-9-]{36}\\.json',p.name):continue
   side=p.with_suffix('.receipt.json')
   receipt,persist,charge=_inbox_status(journal,actor,p,side)
   if charge:handled+=1
   if receipt is not None:
    if persist:
     try:atomic(side,(wire(receipt)+'\n').encode())
     except OSError as e:receipt={**receipt,'receiptDelivery':'UNCONFIRMED','receiptError':type(e).__name__}
    rows.append(receipt)
   if handled>=8:break
 return rows
