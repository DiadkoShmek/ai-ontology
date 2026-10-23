"""Deterministic vocabulary artifacts and a JSON-LD projection, using Python stdlib."""
import argparse
import json
from pathlib import Path
from urllib.parse import quote
from graph import HERE, VOCABULARY, load, validate


def context():
    ns = VOCABULARY['namespace']
    c = {'@version': 1.1, 'ao': ns, 'prov': 'http://www.w3.org/ns/prov#',
         'id': '@id', 'type': '@type', 'data': {'@id': 'ao:recordData', '@type': '@json'}}
    for name in VOCABULARY['classes']:
        c[name] = 'ao:' + name
    for name in VOCABULARY['relations']:
        c[name] = {'@id': 'ao:' + name, '@type': '@id', '@container': '@set'}
    return {'@context': c}


def turtle():
    lines = ['@prefix ao: <' + VOCABULARY['namespace'] + '> .',
             '@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .',
             '@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .',
             '@prefix owl: <http://www.w3.org/2002/07/owl#> .',
             '@prefix dct: <http://purl.org/dc/terms/> .', '']
    lit = lambda s: json.dumps(s, ensure_ascii=False)
    def sources(spec):
        return ', '.join('<https://github.com/DiadkoShmek/ai-ontology/blob/v' + VOCABULARY['bookVersion'] + '/' +
                         src['path'] + '> ' for src in spec['bookSources']).strip()
    for name, spec in VOCABULARY['classes'].items():
        lines.append('ao:' + name + ' a rdfs:Class ;\n  rdfs:label ' + lit(name) + ' ;\n  rdfs:comment ' +
                     lit(spec['definition']) + ' ;\n  rdfs:subClassOf <' + spec['provSuperclass'] + '> ;\n  dct:source ' + sources(spec) + ' .\n')
    for name, spec in VOCABULARY['relations'].items():
        parts = ['ao:' + name + ' a rdf:Property', 'rdfs:comment ' + lit(spec['definition'])]
        for direction in ('domain', 'range'):
            terms = ['ao:' + t for t in spec[direction]]
            value = terms[0] if len(terms) == 1 else '[ a owl:Class ; owl:unionOf ( ' + ' '.join(terms) + ' ) ]'
            parts.append('rdfs:' + direction + ' ' + value)
        if spec.get('provSuperproperty'):
            parts.append('rdfs:subPropertyOf <' + spec['provSuperproperty'] + '>')
        parts.append('dct:source ' + sources(spec))
        lines.append(' ;\n  '.join(parts) + ' .\n')
    lines.append('ao:recordData a rdf:Property ; rdfs:comment "Opaque JSON record data; field validation is specified by vocabulary.json, not this RDF vocabulary." .')
    return '\n'.join(lines) + '\n'


def jsonld(graph):
    validate(graph)
    iri = lambda ident: VOCABULARY['namespace'].split('#')[0] + '/instance#' + quote(ident, safe='')
    indexed = {n['id']: {'id': iri(n['id']), 'type': n['type'], 'data': n['data']} for n in graph['nodes']}
    for edge in graph['edges']:
        indexed[edge['source']].setdefault(edge['relation'], []).append(iri(edge['target']))
    for node in indexed.values():
        for key, value in node.items():
            if isinstance(value, list):
                value.sort()
    return {**context(), '@graph': [indexed[k] for k in sorted(indexed)]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--graph', help='Print a validated graph as JSON-LD instead of vocabulary artifacts')
    parser.add_argument('--check', action='store_true', help='Check committed artifacts without writing')
    args = parser.parse_args()
    if args.graph:
        print(json.dumps(jsonld(load(args.graph)), ensure_ascii=False, sort_keys=True, indent=2))
        return
    expected = {'context.jsonld': json.dumps(context(), ensure_ascii=False, indent=2) + '\n', 'vocabulary.ttl': turtle()}
    for filename, text in expected.items():
        path = HERE / filename
        if args.check:
            if not path.exists() or path.read_text(encoding='utf-8') != text:
                parser.exit(1, 'stale artifact: ' + filename + '\n')
        else:
            path.write_text(text, encoding='utf-8')
    print('vocabulary artifacts match' if args.check else 'vocabulary artifacts written')


if __name__ == '__main__':
    main()
