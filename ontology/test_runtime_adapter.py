import json
from pathlib import Path
import sys
import tempfile
import unittest

from runtime_adapter import world_graph, stored_graph
from graph import InvalidGraph, answer, validate
from participation import ParticipationStore, interpret
from durable import digest

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from research.closed_loop.tasks import make_world, specifications


def response(world,plan):
    view=interpret(world)
    return {'plan':plan,'affected':view['affected_decisions'],'current_criterion':view['current_criterion'],
            'assessments':view['assessments'],'own_effects':view['own_prior_effects'],
            'open_objections':sorted(world['open_objections']),'carry':'Integration fixture, not a model response.','reason':'Local test selection.'}


class RuntimeAdapterTests(unittest.TestCase):
    def test_actual_generated_worlds_and_actual_interpreter_agree(self):
        for spec in specifications():
            for stage in range(3):
                w=make_world(spec,stage);graph=world_graph(w);view=interpret(w)
                with self.subTest(spec=spec['id'],stage=stage):
                    validate(graph)
                    apps=answer(graph,'applicability')
                    actual=sorted((json.loads(n['data']['reason'])['id'],n['data']['result']) for n in graph['nodes'] if n['type']=='Applicability')
                    expected=sorted((r['id'],'applies' if r['applicable'] else 'does-not-apply') for r in view['candidate_applicability'])
                    self.assertEqual(actual,expected)
                    self.assertEqual(len(apps),len(w['candidates']))
                    self.assertEqual(answer(graph,'identity'),[])  # No invented session/model/profile.
                    self.assertFalse(any(n['type']=='Effect' for n in graph['nodes']))
                    self.assertEqual(len(answer(graph,'objections')),len(w['open_objections']))
                    self.assertTrue(all(r['author'] is None and r['target'] is None for r in answer(graph,'objections')))
                    observed=sorted(n['data']['result'] for n in graph['nodes'] if n['type']=='Assessment')
                    self.assertEqual(observed,sorted({'met':'satisfied','lost':'violated','unknown':'unknown'}[r] for r in view['assessments'].values()))

    def test_every_world_field_row_is_preserved_as_source_json(self):
        w=make_world(specifications()[0],1);g=world_graph(w)
        source={n['data']['sourceRef'].split('#',1)[1]:json.loads(n['data']['content']) for n in g['nodes'] if n['type']=='Observation' and n['data']['sourceRef'].startswith('world:sha256:')}
        for key,value in w.items():
            if isinstance(value,list):
                if not value:self.assertEqual(source['/'+key],[])
                for i,row in enumerate(value):self.assertEqual(source['/'+key+'/'+str(i)],row)
            else:self.assertEqual(source['/'+key],value)

    def test_unauthorized_acceptance_is_preserved_without_fabricated_warrant(self):
        spec=next(s for s in specifications() if s['family']=='criterion')
        w=make_world(spec,2);g=world_graph(w)
        new=next(n for n in g['nodes'] if n['type']=='Criterion' and n['data']['version']=='criterion-new')
        self.assertTrue(w['criterion_update']['accepted']);self.assertFalse(w['criterion_update']['authorized'])
        self.assertEqual(new['data']['acceptance'],'accepted')
        self.assertFalse(any(e['source']==new['id'] and e['relation']=='governedBy' for e in g['edges']))
        self.assertEqual(interpret(w)['current_criterion'],'criterion-old')
        assessment=next(n for n in g['nodes'] if n['type']=='Assessment' and n['data']['result']=='unknown')
        support=next(e['target'] for e in g['edges'] if e['source']==assessment['id'] and e['relation']=='supportedBy')
        obs=next(n for n in g['nodes'] if n['id']==support)
        self.assertEqual(obs['data']['availability'],'missing');self.assertEqual(json.loads(obs['data']['content']),None)

    def test_actual_commit_reopen_and_readback_projects_only_recorded_local_effects(self):
        w=make_world(specifications()[0],0)
        eligible={r['id'] for r in interpret(w)['candidate_applicability'] if r['applicable']}
        chosen=next(c for c in w['candidates'] if c['id'] in eligible and c['cost']<=w['budget'] and not c['requires'])
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'journal.sqlite';store=ParticipationStore(path,create=True)
            _,tail=store.read();receipt=store.commit('turn-0',w,response(w,[chosen['id']]),expected=tail['head'])
            reopened=ParticipationStore(path)
            body,read_tail=reopened.read();self.assertEqual(digest(body[0]),receipt['stored_sha256'])
            graph=stored_graph(reopened,'turn-0')
            effects=[n for n in graph['nodes'] if n['type']=='Effect']
            self.assertEqual(len(effects),len(receipt['effects']))
            self.assertEqual(json.loads(effects[0]['data']['description']),receipt['effects'][0])
            self.assertEqual(effects[0]['data']['state'],'observed')
            read_obs=[n for n in graph['nodes'] if n['type']=='Observation' and n['data']['sourceRef'].startswith('journal-head:')]
            self.assertEqual(len(read_obs),1);self.assertIn(read_tail['head'],read_obs[0]['data']['sourceRef'])
            self.assertIn(receipt['stored_sha256'],read_obs[0]['data']['sourceRef'])
            self.assertTrue(any(e['relation']=='observesEffect' and e['target']==effects[0]['id'] for e in graph['edges']))
            self.assertEqual(answer(graph,'returnPath')[0]['recordedPathComplete'],False)
            self.assertEqual(len(next(r for r in answer(graph,'authority') if r['recordedWarrants'])['recordedWarrants']),1)
            # Available source records were not necessarily available to or used by a model.
            self.assertEqual(answer(graph,'evidenceUse'),[])
            with self.assertRaisesRegex(InvalidGraph,'not found'):stored_graph(reopened,'missing')

    def test_empty_or_rejected_actual_turn_has_no_observed_effect(self):
        w=make_world(specifications()[0],0)
        for mode in ('empty','rejected','incomplete'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as temp:
                store=ParticipationStore(Path(temp)/'journal.sqlite',create=True);_,tail=store.read()
                if mode=='empty':store.commit('turn-0',w,response(w,[]),expected=tail['head'])
                else:
                    payload=None if mode=='incomplete' else response(w,['nonexistent-action'])
                    store.record_turn('turn-0',w,payload,response='Unsuccessful local fixture',terminal=mode!='incomplete',expected=tail['head'])
                graph=stored_graph(store,'turn-0')
                self.assertFalse(any(n['type']=='Effect' for n in graph['nodes']))
                self.assertFalse(any(e['relation']=='observesEffect' for e in graph['edges']))
                self.assertEqual(answer(graph,'returnPath'),[])

    def test_long_readback_response_is_preserved_without_truncation(self):
        w=make_world(specifications()[0],0)
        text='readback\n' * 1200
        with tempfile.TemporaryDirectory() as temp:
            store=ParticipationStore(Path(temp)/'journal.sqlite',create=True);_,tail=store.read()
            store.record_turn('turn-0',w,None,response=text,terminal=False,expected=tail['head'])
            graph=stored_graph(store,'turn-0')
            anchor=next(n for n in graph['nodes'] if n['type']=='Observation' and n['data']['sourceRef'].endswith('#/response'))
            metadata=json.loads(anchor['data']['content']);self.assertEqual(metadata['encoding'],'json-text-chunks')
            parts=[json.loads(n['data']['content']) for n in graph['nodes'] if n['type']=='Observation' and '#/response/chunk/' in n['data']['sourceRef']]
            recovered=json.loads(''.join(part['chunk'] for part in sorted(parts,key=lambda x:x['part'])))
            self.assertEqual(recovered,text)
            self.assertEqual(metadata['value_sha256'],digest(text))
            self.assertFalse(any(n['type']=='Effect' for n in graph['nodes']))

    def test_no_store_duck_typing_or_unvalidated_world(self):
        with self.assertRaisesRegex(InvalidGraph,'ParticipationStore'):stored_graph(object(),'turn-0')
        with self.assertRaises(Exception):world_graph({'actor':'fake'})


if __name__=='__main__':unittest.main()
