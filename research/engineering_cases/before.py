"""Historical source excerpt; see provenance.json and receipt_replay.py."""
from common import Path, os, re, read_file, strict_json, digest, atomic, wire, ReferenceValidationError, RecordedEventConflict, _reference_details
HOMES = {}  # Explicit fixture bindings are supplied by the replay.

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
   raw=None;side=p.with_suffix('.receipt.json')
   try:
    raw=read_file(p,16384)
    if side.exists():
     try:
      previous=strict_json(read_file(side,16384))
      if previous.get('inputSha256')==digest(raw):continue
     except (OSError,ValueError,AttributeError):pass
    event=strict_json(raw)
    if type(event) is not dict or event.get('id')!=p.stem:raise ValueError('filename-id-mismatch')
    receipt=journal.append(actor,event);receipt.update(status='recorded',actor=actor,inputSha256=digest(raw))
   except (OSError,ValueError,UnicodeError) as e:
    receipt={'status':'REFUSED','actor':actor,'reason':str(e)[:100],'inputSha256':digest(raw) if raw is not None else None}
    details=_reference_details(e)
    if details is not None:receipt.update(details)
   try:atomic(side,(wire(receipt)+'\n').encode())
   except OSError as e:receipt={**receipt,'receiptDelivery':'UNCONFIRMED','receiptError':type(e).__name__}
   rows.append(receipt);handled+=1
   if handled>=8:break
 return rows
