"""Exact dependency excerpts; deployment registry is replaced by one fixture actor."""
import hashlib, json, os, re, sqlite3, stat, tempfile, uuid
from pathlib import Path
ACTORS = frozenset({"agent-a"})

_REFERENCE_REASONS=frozenset({'fields-refused','reference-path-type','reference-root','reference-private-or-unsupported','reference-sha','reference-changed','symlink-refused','file-boundary','file-cap'})

def digest(raw):return hashlib.sha256(raw).hexdigest()

def wire(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'))

def read_file(path,cap):
 path=Path(path)
 if any(p.is_symlink() for p in (path,*path.parents)):raise ValueError('symlink-refused')
 fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
 try:
  s=os.fstat(fd)
  if not stat.S_ISREG(s.st_mode) or s.st_size>cap or s.st_nlink!=1:raise ValueError('file-boundary')
  out=bytearray()
  while len(out)<=cap:
   b=os.read(fd,min(8192,cap+1-len(out)))
   if not b:break
   out.extend(b)
  if len(out)>cap:raise ValueError('file-cap')
  return bytes(out)
 finally:os.close(fd)

def atomic(path,raw):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 fd,name=tempfile.mkstemp(prefix='.journal-',dir=path.parent)
 try:
  with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
  os.replace(name,path);fd=os.open(path.parent,os.O_RDONLY);os.fsync(fd);os.close(fd)
 finally:
  if os.path.exists(name):os.unlink(name)

def strict_json(raw):
 def pairs(rows):
  out={}
  for key,value in rows:
   if key in out:raise ValueError("duplicate-json-key")
   out[key]=value
  return out
 try:return json.loads(raw,object_pairs_hook=pairs)
 except RecursionError as e:raise ValueError('json-depth-refused') from e

def exact_uuid(value):
 if type(value) is not str or str(uuid.UUID(value))!=value:raise ValueError('id-refused')

def fields(value,keys):
 if type(value) is not dict or set(value)!=set(keys):raise ValueError('fields-refused')

class ReferenceValidationError(ValueError):
 def __init__(self,reason,field,refIndex):
  super().__init__(reason);self.field=field;self.refIndex=refIndex

class RecordedEventConflict(ValueError):
 """An intact stored event has a different canonical identity for this UUID."""

def _reference_details(error):
 if type(error) is not ReferenceValidationError or str(error) not in _REFERENCE_REASONS:return None
 field=error.field;index=error.refIndex
 if field=='payload.map':
  if index is not None:return None
 elif type(field) is not str or field not in {'payload.evidence','payload.dependencies'} or type(index) is not int or not 0<=index<({'payload.evidence':4,'payload.dependencies':8}[field]):return None
 return {'field':field,'refIndex':index}

def recorded_event(self,actor,event):
  """Read durable event identity only; never append or revalidate artifacts."""
  if actor not in ACTORS:raise ValueError('actor-refused')
  fields(event,{'id','kind','payload'});exact_uuid(event['id'])
  identity=digest(wire({'actor':actor,'kind':event['kind'],'payload':event['payload']}).encode())
  connection=sqlite3.connect((self.runtime/'journal.sqlite').absolute().as_uri()+'?mode=ro',uri=True,timeout=0.25)
  try:
   connection.execute('PRAGMA query_only=ON');connection.execute('BEGIN')
   row=connection.execute('SELECT seq,actor,kind,payload,digest FROM events WHERE id=?',(event['id'],)).fetchone()
   if row is None:return None
   seq,stored_actor,kind,payload,pin=row
   if type(seq) is not int or seq<1 or stored_actor not in ACTORS or kind not in {'change','seen','map-checkpoint','work','work-transport'} or type(payload) is not str or len(payload.encode('utf8'))>16384:raise ValueError('recorded-event-invalid')
   body=strict_json(payload)
   stored=digest(wire({'actor':stored_actor,'kind':kind,'payload':body}).encode())
   if type(body) is not dict or wire(body)!=payload or pin!=stored:raise ValueError('recorded-event-invalid')
   if stored!=identity:raise RecordedEventConflict('idempotency-conflict')
   return {'id':event['id'],'seq':seq,'replayed':True}
  finally:connection.close()
