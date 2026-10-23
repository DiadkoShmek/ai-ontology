"""Finite record-shape validation and transparent joins; no truth or permission oracle."""
import argparse
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
VOCABULARY = json.loads((HERE / 'vocabulary.json').read_text(encoding='utf-8'))
ID = re.compile(r'[A-Za-z][A-Za-z0-9_.:-]{0,127}\Z')


class InvalidGraph(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise InvalidGraph(message)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise InvalidGraph('duplicate JSON key: ' + key)
        result[key] = value
    return result


def load(path):
    """Bound file bytes before decoding; reject duplicate JSON keys and nonfinite numbers."""
    with Path(path).open('rb') as source:
        raw = source.read(VOCABULARY['limits']['fileBytes'] + 1)
    require(len(raw) <= VOCABULARY['limits']['fileBytes'], 'file byte limit')
    try:
        return json.loads(raw, object_pairs_hook=unique_object,
                          parse_constant=lambda value: (_ for _ in ()).throw(InvalidGraph('nonfinite number')))
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise InvalidGraph('invalid JSON') from exc


def validate(graph):
    """Validate this local closed-record profile, not RDF/OWL or external facts."""
    require(type(graph) is dict and set(graph) == {'nodes', 'edges'}, 'graph keys')
    require(type(graph['nodes']) is list and type(graph['edges']) is list, 'graph arrays')
    require(len(graph['nodes']) <= VOCABULARY['limits']['nodes'], 'node limit')
    require(len(graph['edges']) <= VOCABULARY['limits']['edges'], 'edge limit')
    nodes = {}
    for node in graph['nodes']:
        require(type(node) is dict and set(node) == {'id', 'type', 'data'}, 'node keys')
        ident, kind, data = node['id'], node['type'], node['data']
        require(type(ident) is str and ID.fullmatch(ident) is not None, 'node ID')
        require(ident not in nodes, 'duplicate node: ' + ident)
        require(type(kind) is str and kind in VOCABULARY['classes'], 'unknown node type')
        require(type(data) is dict, 'node data')
        fields = VOCABULARY['classes'][kind]['fields']
        required = {key for key, spec in fields.items() if spec.get('required', True)}
        require(required <= set(data) <= set(fields), 'data fields: ' + ident)
        for key, spec in fields.items():
            if key not in data:
                continue
            value = data[key]
            if spec['type'] == 'integer':
                require(type(value) is int, 'integer: ' + ident + '.' + key)
            else:
                require(type(value) is str and bool(value.strip()), 'nonempty string: ' + ident + '.' + key)
                require(len(value) <= VOCABULARY['limits']['stringCharacters'], 'string limit')
            require('enum' not in spec or value in spec['enum'], 'enum: ' + ident + '.' + key)
        nodes[ident] = node
    outgoing, seen = {}, set()
    for edge in graph['edges']:
        require(type(edge) is dict and set(edge) == {'source', 'relation', 'target'}, 'edge keys')
        require(all(type(edge[k]) is str for k in edge), 'edge strings')
        source, relation, target = edge['source'], edge['relation'], edge['target']
        require(source in nodes and target in nodes, 'dangling edge')
        require(relation in VOCABULARY['relations'], 'unknown relation')
        triple = (source, relation, target)
        require(triple not in seen, 'duplicate edge')
        seen.add(triple)
        spec = VOCABULARY['relations'][relation]
        require(nodes[source]['type'] in spec['domain'], 'relation domain: ' + relation)
        require(nodes[target]['type'] in spec['range'], 'relation range: ' + relation)
        outgoing.setdefault((source, relation), []).append(target)
    def targets(ident, relation):
        return outgoing.get((ident, relation), [])
    def one(ident, relation):
        found = targets(ident, relation)
        require(len(found) == 1, 'exactly one ' + relation + ': ' + ident)
        return found[0]
    for ident, node in nodes.items():
        kind, data = node['type'], node['data']
        for relation in VOCABULARY['classes'][kind].get('exactlyOne', []):
            one(ident, relation)
        for relation in VOCABULARY['classes'][kind].get('atMostOne', []):
            require(len(targets(ident, relation)) <= 1, 'at most one ' + relation + ': ' + ident)
        for predecessor in targets(ident, 'previousVersion'):
            require(ident != predecessor, 'self revision')
            require(nodes[predecessor]['type'] == kind, 'previousVersion type')
        if kind == 'Decision':
            session = targets(ident, 'inSession')
            if session:
                require(one(ident, 'madeBy') == one(session[0], 'madeBy'), 'decision/session actor mismatch')
        accepted = (kind == 'Criterion' and data['acceptance'] == 'accepted') or (
            kind == 'Revision' and data['status'] == 'accepted')
        if kind in ('Criterion', 'Revision'):
            require(len(targets(ident, 'acceptedBy')) <= 1, 'multiple acceptors')
            require(len(targets(ident, 'governedBy')) <= 1, 'multiple acceptance warrants')
            if accepted:
                actor = one(ident, 'acceptedBy')
                authority = single_authority[0] if (single_authority := targets(ident, 'governedBy')) else None
                if authority is None:
                    continue
                require(one(authority, 'heldBy') == actor, 'acceptance warrant holder mismatch')
                require(one(authority, 'inScope') == one(ident, 'inScope'), 'acceptance warrant scope mismatch')
                expected = 'adopt-criterion' if kind == 'Criterion' else 'accept-revision'
                require(nodes[authority]['data']['actionKind'] == expected, 'acceptance warrant action mismatch')
            else:
                require(not targets(ident, 'acceptedBy'), 'unaccepted record has acceptor')
        if kind == 'Applicability' and targets(ident, 'toDecision'):
            require(one(ident, 'inScope') == one(one(ident, 'toDecision'), 'inScope'), 'applicability decision scope')
        if kind == 'Assessment':
            require(one(ident, 'inScope') == one(one(ident, 'underCriterion'), 'inScope'), 'assessment criterion scope')
    # Iterative three-colour DFS: no recursion-depth dependency on valid long chains.
    state = {}
    for ident in nodes:
        if state.get(ident):
            continue
        stack = [(ident, False)]
        while stack:
            current, done = stack.pop()
            if done:
                state[current] = 2
                continue
            require(state.get(current) != 1, 'previousVersion cycle')
            if state.get(current) == 2:
                continue
            state[current] = 1
            stack.append((current, True))
            stack.extend((prev, False) for prev in targets(current, 'previousVersion'))
    return graph


def answer(graph, question):
    """Explicit local graph joins. Empty/missing means unrecorded, never false in the world."""
    validate(graph)
    nodes = {node['id']: node for node in graph['nodes']}
    edges = {}
    for e in graph['edges']:
        edges.setdefault((e['source'], e['relation']), []).append(e['target'])
    def ts(ident, relation):
        return sorted(edges.get((ident, relation), []))
    def single(ident, relation):
        values = ts(ident, relation)
        return values[0] if values else None
    def ids(kind):
        return sorted(k for k, v in nodes.items() if v['type'] == kind)
    result = []
    if question == 'identity':
        result = [{'session': s, 'actor': single(s, 'madeBy'), 'model': single(s, 'runsModel'),
                   'profile': single(s, 'usesProfile')} for s in ids('Session')]
    elif question == 'criterionAssessment':
        result = [{'assessment': a, 'subject': single(a, 'evaluates'), 'criterion': single(a, 'underCriterion'),
                   'criterionAcceptance': nodes[single(a, 'underCriterion')]['data']['acceptance'],
                   'result': nodes[a]['data']['result'], 'support': ts(a, 'supportedBy')} for a in ids('Assessment')]
    elif question == 'evidenceUse':
        for d in ids('Decision'):
            used = [i for i in ts(d, 'usedRecord') if nodes[i]['type'] == 'Observation']
            for o in sorted(set(ts(d, 'availableEvidence') + used)):
                result.append({'decision': d, 'observation': o, 'availableEdge': o in ts(d, 'availableEvidence'),
                               'usedEdge': o in used, 'recordAvailability': nodes[o]['data']['availability']})
    elif question == 'lessonUse':
        for lesson in ids('Lesson'):
            result.append({'lesson': lesson, 'status': nodes[lesson]['data']['status'],
                           'usedIn': [d for d in ids('Decision') if lesson in ts(d, 'usedRecord')]})
    elif question == 'applicability':
        result = [{'record': single(a, 'appliesRecord'), 'decision': single(a, 'toDecision'),
                   'result': nodes[a]['data']['result'], 'assessment': a} for a in ids('Applicability')]
    elif question == 'authority':
        for d in ids('Decision'):
            result.append({'decision': d, 'recordedWarrants': ts(d, 'governedBy'),
                           'adoptedRevisions': ts(d, 'adoptsRevision')})
    elif question == 'objections':
        result = [{'objection': o, 'target': single(o, 'challenges'), 'author': single(o, 'attributedTo'),
                   'status': nodes[o]['data']['status'],
                   'respondingRevisions': [r for r in ids('Revision') if o in ts(r, 'respondsTo')]} for o in ids('Objection')]
    elif question == 'returnPath':
        for d in ids('Decision'):
            for effect in ts(d, 'hasEffect'):
                observations = [o for o in ids('Observation') if effect in ts(o, 'observesEffect')]
                assessments = [a for a in ids('Assessment') if effect in ts(a, 'evaluates') and
                               set(ts(a, 'supportedBy')) & set(observations)]
                revisions = [r for r in ids('Revision') if effect in ts(r, 'respondsTo') and
                             set(ts(r, 'basedOn')) & set(assessments) and nodes[r]['data']['status'] == 'accepted']
                later = [next_d for next_d in ids('Decision') if next_d != d and
                         set(ts(next_d, 'adoptsRevision')) & set(revisions)]
                result.append({'decision': d, 'effect': effect, 'observations': observations,
                               'assessments': assessments, 'acceptedRevisions': revisions, 'laterDecisions': later,
                               'recordedPathComplete': bool(observations and assessments and revisions and later)})
    else:
        raise InvalidGraph('unknown competency question: ' + str(question))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('graph')
    parser.add_argument('--question', choices=['identity', 'criterionAssessment', 'evidenceUse', 'lessonUse',
                                              'applicability', 'authority', 'objections', 'returnPath'])
    args = parser.parse_args()
    try:
        graph = validate(load(args.graph))
        output = answer(graph, args.question) if args.question else {'valid': True, 'nodes': len(graph['nodes']), 'edges': len(graph['edges'])}
        print(json.dumps(output, ensure_ascii=False, sort_keys=True, indent=2))
    except (InvalidGraph, OSError) as exc:
        parser.exit(2, 'invalid: ' + str(exc) + '\n')


if __name__ == '__main__':
    main()
