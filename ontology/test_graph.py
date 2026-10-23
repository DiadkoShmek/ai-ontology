import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from urllib.parse import unquote

from graph import HERE, VOCABULARY, InvalidGraph, answer, load, validate
from export import context, jsonld, turtle


def base():
    return load(HERE / 'fixtures/closed-loop.json')


def node(graph, ident):
    return next(n for n in graph['nodes'] if n['id'] == ident)


def drop(graph, source, relation, target=None):
    graph['edges'] = [e for e in graph['edges'] if not (e['source'] == source and e['relation'] == relation and (target is None or target == e['target']))]


class GraphTests(unittest.TestCase):
    def test_valid_closed_and_open_record_paths(self):
        closed = answer(base(), 'returnPath')[0]
        opened = answer(load(HERE / 'fixtures/open-loop.json'), 'returnPath')[0]
        self.assertTrue(closed['recordedPathComplete'])
        self.assertEqual(closed['laterDecisions'], ['decision:next'])
        self.assertFalse(opened['recordedPathComplete'])
        self.assertEqual(opened['acceptedRevisions'], ['revision:criterion'])
        self.assertEqual(opened['laterDecisions'], [])

    def test_identity_does_not_collapse_actor_model_profile_session(self):
        rows = answer(base(), 'identity')
        self.assertEqual(rows, [{'session': 'session:s1', 'actor': 'actor:operator', 'model': 'model:m1', 'profile': 'profile:p1'}])
        self.assertEqual(len(set(rows[0].values())), 4)

    def test_accepted_criterion_can_be_violated_and_replacement_cannot_erase_it(self):
        rows = answer(base(), 'criterionAssessment')
        by_id = {r['assessment']: r for r in rows}
        self.assertEqual(by_id['assessment:old']['criterionAcceptance'], 'accepted')
        self.assertEqual(by_id['assessment:old']['result'], 'violated')
        self.assertEqual(by_id['assessment:new']['result'], 'satisfied')
        self.assertEqual(by_id['assessment:old']['subject'], by_id['assessment:new']['subject'])

    def test_available_does_not_mean_used(self):
        rows = answer(base(), 'evidenceUse')
        unused = next(r for r in rows if r['observation'] == 'observation:unused')
        self.assertTrue(unused['availableEdge'])
        self.assertFalse(unused['usedEdge'])
        g = base()
        drop(g, 'decision:first', 'usedRecord', 'observation:source')
        self.assertTrue(all(not r['usedEdge'] for r in answer(g, 'evidenceUse')))

    def test_stored_lesson_does_not_mean_current_use_or_benefit(self):
        rows = {r['lesson']: r for r in answer(base(), 'lessonUse')}
        self.assertEqual(rows['lesson:stored']['usedIn'], [])
        self.assertEqual(rows['lesson:used']['usedIn'], ['decision:next'])
        self.assertNotIn('benefit', rows['lesson:used'])
        self.assertEqual(answer(base(), 'applicability')[0]['result'], 'unknown')

    def test_revision_does_not_inherit_action_warrant(self):
        next_decision = next(r for r in answer(base(), 'authority') if r['decision'] == 'decision:next')
        self.assertEqual(next_decision['adoptedRevisions'], ['revision:criterion'])
        self.assertEqual(next_decision['recordedWarrants'], [])

    def test_objection_keeps_author_target_and_response(self):
        self.assertEqual(answer(base(), 'objections'), [{'objection': 'objection:loss', 'target': 'claim:original', 'author': 'actor:reviewer', 'status': 'upheld', 'respondingRevisions': ['revision:criterion']}])

    def test_positive_and_negative_competency_fixtures(self):
        suite = load(HERE / 'competency-questions.json')
        self.assertEqual(len(suite['questions']), 9)
        for case in suite['cases']:
            with self.subTest(case=case['fixture'], question=case['question']):
                self.assertEqual(answer(load(HERE / case['fixture']), case['question']), case['expected'])

    def test_legacy_eight_query_bytes_and_registry_order_are_preserved(self):
        legacy = ['identity', 'criterionAssessment', 'evidenceUse', 'lessonUse',
                  'applicability', 'authority', 'objections', 'returnPath']
        suite = load(HERE / 'competency-questions.json')
        self.assertEqual([q['id'] for q in suite['questions']], legacy + ['claimUse'])
        expected = {'closed-loop.json': 'd8dcd3df7eba681fcb58b2416b846c950919a30822b812f526a0a0fe8fb62edb',
                    'open-loop.json': '7579e116447b83ffe48dbcd733aa1cb4986a7b7975edae124d19aabf698233d5'}
        for fixture, digest in expected.items():
            rows = {question: answer(load(HERE / 'fixtures' / fixture), question) for question in legacy}
            raw = json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), digest)

    def test_claim_use_keeps_historical_version_and_current_independent_acceptance(self):
        g = load(HERE / 'fixtures/historical-claim-use.json')
        original = copy.deepcopy(g)
        rows = {row['claim']: row for row in answer(g, 'claimUse')}
        self.assertEqual(rows['claim:v1']['claimStatus'], 'superseded')
        self.assertEqual(rows['claim:v1']['supportingObservations'], ['observation:retired'])
        self.assertEqual(rows['claim:v1']['usedIn'], [{
            'decision': 'decision:old', 'decisionActionStatus': 'executed',
            'effects': [{'effect': 'effect:reported', 'state': 'reported', 'affectedActors': ['actor:affected']}]}])
        self.assertEqual(rows['claim:v2'], {'claim': 'claim:v2', 'claimStatus': 'accepted',
            'previousVersions': ['claim:v1'], 'supportingObservations': ['observation:independent'], 'usedIn': []})
        self.assertEqual(node(g, 'observation:retired')['data']['availability'], 'withdrawn')
        self.assertEqual(g, original)

    def test_claim_use_is_not_inferred_from_dependency_availability_support_or_history(self):
        g = load(HERE / 'fixtures/historical-claim-use.json')
        drop(g, 'decision:old', 'usedRecord')
        g['edges'].extend([
            {'source': 'decision:old', 'relation': 'dependsOn', 'target': 'claim:v1'},
            {'source': 'decision:old', 'relation': 'availableEvidence', 'target': 'observation:retired'},
            {'source': 'decision:old', 'relation': 'availableEvidence', 'target': 'observation:independent'}])
        self.assertTrue(all(row['usedIn'] == [] for row in answer(g, 'claimUse')))
        observations = answer(g, 'evidenceUse')
        self.assertEqual([row['observation'] for row in observations], ['observation:independent', 'observation:retired'])
        self.assertTrue(all(not row['usedEdge'] for row in observations))

    def test_claim_use_missing_effect_or_actor_remains_visible_as_empty(self):
        g = load(HERE / 'fixtures/historical-claim-use.json')
        drop(g, 'decision:old', 'hasEffect')
        self.assertEqual(answer(g, 'claimUse')[0]['usedIn'][0]['effects'], [])
        g = load(HERE / 'fixtures/historical-claim-use.json')
        drop(g, 'effect:reported', 'affects')
        self.assertEqual(answer(g, 'claimUse')[0]['usedIn'][0]['effects'], [
            {'effect': 'effect:reported', 'state': 'reported', 'affectedActors': []}])

    def test_claim_use_previous_versions_and_support_are_direct_only(self):
        g = load(HERE / 'fixtures/historical-claim-use.json')
        g['nodes'].append({'id': 'claim:v0', 'type': 'Claim', 'data': {
            'label': 'Older authored version', 'text': 'Not directly used.', 'status': 'superseded'}})
        g['edges'].extend([
            {'source': 'claim:v0', 'relation': 'inScope', 'target': 'scope:synthetic'},
            {'source': 'claim:v1', 'relation': 'previousVersion', 'target': 'claim:v0'}])
        drop(g, 'claim:v1', 'supportedBy')
        rows = {row['claim']: row for row in answer(g, 'claimUse')}
        self.assertEqual(rows['claim:v2']['previousVersions'], ['claim:v1'])
        self.assertEqual(rows['claim:v1']['previousVersions'], ['claim:v0'])
        self.assertEqual(rows['claim:v1']['supportingObservations'], [])
        self.assertEqual(rows['claim:v2']['supportingObservations'], ['observation:independent'])
        self.assertEqual(rows['claim:v0']['usedIn'], [])
        self.assertEqual(rows['claim:v2']['usedIn'], [])

    def test_claim_use_order_and_authored_statuses_are_preserved(self):
        g = load(HERE / 'fixtures/historical-claim-use.json')
        node(g, 'decision:old')['data']['actionStatus'] = 'withheld'
        node(g, 'effect:reported')['data']['state'] = 'unknown'
        expected = answer(g, 'claimUse')
        g['nodes'].reverse()
        g['edges'].reverse()
        self.assertEqual(answer(g, 'claimUse'), expected)
        self.assertEqual(expected[0]['usedIn'][0]['decisionActionStatus'], 'withheld')
        self.assertEqual(expected[0]['usedIn'][0]['effects'][0]['state'], 'unknown')
        self.assertEqual(answer({'nodes': [], 'edges': []}, 'claimUse'), [])

    def test_shape_negative_fixture_mutations(self):
        cases = load(HERE / 'fixtures/invalid-records.json')['cases']
        for case in cases:
            g = base()
            if case['operation'] == 'replace-node-type':
                node(g, case['id'])['type'] = case['value']
            elif case['operation'] == 'replace-data':
                node(g, case['id'])['data'][case['field']] = case['value']
            elif case['operation'] == 'append-edge':
                g['edges'].append(case['value'])
            elif case['operation'] == 'drop-edge':
                drop(g, case['id'], case['relation'])
            with self.subTest(case=case['name']):
                with self.assertRaisesRegex(InvalidGraph, case['error']):
                    validate(g)

    def test_bad_wire_types_never_become_truthy_identifiers(self):
        for value in [True, None, [], {}, 3.0]:
            g = base()
            g['nodes'][0]['id'] = value
            with self.subTest(value=value), self.assertRaises(InvalidGraph):
                validate(g)
        for value in [True, None, [], {}]:
            g = base()
            g['edges'][0]['target'] = value
            with self.subTest(value=value), self.assertRaises(InvalidGraph):
                validate(g)

    def test_unknown_fields_and_duplicate_nodes_edges_rejected(self):
        mutations = [lambda g: g.update(extra=1), lambda g: g['nodes'][0].update(extra=1),
                     lambda g: g['nodes'].append(g['nodes'][0]), lambda g: g['edges'].append(g['edges'][0])]
        for mutate in mutations:
            g = base(); mutate(g)
            with self.assertRaises(InvalidGraph): validate(g)

    def test_domain_range_and_missing_references_rejected(self):
        for edge in [
            {'source': 'actor:operator', 'relation': 'usesProfile', 'target': 'profile:p1'},
            {'source': 'session:s1', 'relation': 'runsModel', 'target': 'profile:p1'},
            {'source': 'session:s1', 'relation': 'runsModel', 'target': 'missing'},
            {'source': 'session:s1', 'relation': 'permitsAnything', 'target': 'actor:operator'},
        ]:
            g = base();g['edges'].append(edge)
            with self.assertRaises(InvalidGraph): validate(g)

    def test_previous_version_cycles_rejected_but_long_chains_supported(self):
        g = base()
        g['edges'].append({'source': 'criterion:old', 'relation': 'previousVersion', 'target': 'criterion:new'})
        with self.assertRaisesRegex(InvalidGraph, 'cycle'):validate(g)
        g = {'nodes': [], 'edges': []}
        for i in range(1500):
            g['nodes'].append({'id': 'orientation:n' + str(i), 'type': 'Orientation', 'data': {'label': 'n', 'version': str(i), 'purpose': 'fixture'}})
            if i:
                g['edges'].append({'source': 'orientation:n' + str(i), 'relation': 'previousVersion', 'target': 'orientation:n' + str(i-1)})
        validate(g)

    def test_each_return_link_is_needed(self):
        for source, relation in [('observation:effect', 'observesEffect'), ('assessment:old', 'supportedBy'),
                                 ('revision:criterion', 'basedOn'), ('revision:criterion', 'respondsTo'),
                                 ('decision:next', 'adoptsRevision')]:
            g=base();drop(g,source,relation)
            with self.subTest(relation=relation):
                self.assertFalse(answer(g,'returnPath')[0]['recordedPathComplete'])

    def test_a_different_effect_cannot_complete_this_return_path(self):
        g=base()
        g['nodes'].append({'id':'effect:other','type':'Effect','data':{'label':'other','description':'different effect','state':'unknown'}})
        drop(g,'revision:criterion','respondsTo','effect:loss')
        g['edges'].append({'source':'revision:criterion','relation':'respondsTo','target':'effect:other'})
        self.assertFalse(answer(g,'returnPath')[0]['recordedPathComplete'])

    def test_missing_records_are_not_asserted_false_and_false_claims_can_be_structurally_valid(self):
        g=base()
        node(g,'claim:original')['data']['text']='2 + 2 = 5'
        validate(g)  # Deliberate semantic negative: shape is not truth.
        self.assertNotIn('truth', node(g,'claim:original')['data'])
        self.assertEqual(answer({'nodes':[],'edges':[]},'criterionAssessment'),[])

    def test_loader_rejects_duplicate_keys_nonfinite_and_oversize_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'bad.json'
            for raw in [b'{"nodes":[],"nodes":[],"edges":[]}', b'{"value":NaN}', b'\xff', b'{bad']:
                p.write_bytes(raw)
                with self.assertRaises(InvalidGraph):load(p)
            p.write_bytes(b' ' * (VOCABULARY['limits']['fileBytes']+1))
            with self.assertRaisesRegex(InvalidGraph,'byte limit'):load(p)

    def test_limits_before_node_walk(self):
        with self.assertRaisesRegex(InvalidGraph,'node limit'):
            validate({'nodes':[None]*(VOCABULARY['limits']['nodes']+1),'edges':[]})
        with self.assertRaisesRegex(InvalidGraph,'edge limit'):
            validate({'nodes':[],'edges':[None]*(VOCABULARY['limits']['edges']+1)})

    def test_book_mappings_point_to_existing_numbered_sections(self):
        import re
        for category in ('classes','relations'):
            for spec in VOCABULARY[category].values():
                for source in spec['bookSources']:
                    text=(HERE.parent/source['path']).read_text(encoding='utf-8')
                    self.assertRegex(text, r'(?m)^## '+str(source['section'])+r'\b')

    def test_context_preserves_relations_and_opaque_data_without_merging_ids(self):
        g=base(); projected=jsonld(g)
        self.assertEqual(projected['@context'],context()['@context'])
        recovered_nodes=[]; recovered_edges=[]
        local=lambda iri:unquote(iri.split('#',1)[1])
        for n in projected['@graph']:
            recovered_nodes.append({'id':local(n['id']),'type':n['type'],'data':n['data']})
            for relation in VOCABULARY['relations']:
                for target in n.get(relation,[]):
                    recovered_edges.append({'source':local(n['id']),'relation':relation,'target':local(target)})
        sort=lambda xs:sorted(json.dumps(x,sort_keys=True) for x in xs)
        self.assertEqual(sort(g['nodes']),sort(recovered_nodes))
        self.assertEqual(sort(g['edges']),sort(recovered_edges))

    def test_generated_artifacts_are_current(self):
        self.assertEqual((HERE/'context.jsonld').read_text(encoding='utf-8'),json.dumps(context(),ensure_ascii=False,indent=2)+'\n')
        self.assertEqual((HERE/'vocabulary.ttl').read_text(encoding='utf-8'),turtle())
        self.assertIn('owl:unionOf',turtle())
        self.assertNotIn('owl:equivalent',turtle())

    def test_cli_accepts_fixture_and_rejects_invalid_without_traceback(self):
        success=subprocess.run([sys.executable,str(HERE/'graph.py'),str(HERE/'fixtures/closed-loop.json')],capture_output=True,text=True)
        self.assertEqual(success.returncode,0,success.stderr)
        self.assertTrue(json.loads(success.stdout)['valid'])
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'bad.json';p.write_text('{"nodes": [], "edges": [{}]}')
            fail=subprocess.run([sys.executable,str(HERE/'graph.py'),str(p)],capture_output=True,text=True)
            self.assertEqual(fail.returncode,2)
            self.assertNotIn('Traceback',fail.stderr)


if __name__=='__main__':unittest.main()
