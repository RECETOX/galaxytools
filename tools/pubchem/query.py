from typing import Dict

from rdfs import Graph


def pubchem_graphs() -> Dict[str, Graph]:
    return {
        'compound/general': ('compound/general', '*.ttl.gz', 'http://rdf.ncbi.nlm.nih.gov/pubchem/compound'),
        'compound/nbr2d': ('compound/nbr2d', '*.ttl.gz', 'http://rdf.ncbi.nlm.nih.gov/pubchem/compound'),
        'compound/nbr3d': ('compound/nbr3d', '*.ttl.gz', 'http://rdf.ncbi.nlm.nih.gov/pubchem/compound'),
        'descriptor/compound': ('descriptor/compound', '*.ttl.gz', 'http://rdf.ncbi.nlm.nih.gov/pubchem/descriptor'),
        'descriptor/substance': ('descriptor/substance', '*.ttl.gz', 'http://rdf.ncbi.nlm.nih.gov/pubchem/descriptor'),
        'substance': ('substance', '*.ttl.gz', 'http://rdf.ncbi.nlm.nih.gov/pubchem/substance'),
        'synonym': ('synonym', '*.ttl.gz', 'http://rdf.ncbi.nlm.nih.gov/pubchem/synonym'),
        'inchikey': ('inchikey', '*.ttl.gz', 'http://rdf.ncbi.nlm.nih.gov/pubchem/inchikey'),
        'bioassay': ('bioassay', '*.ttl.gz', 'http://rdf.ncbi.nlm.nih.gov/pubchem/bioassay'),
        'measuregroup': ('measuregroup', '*.ttl.gz', 'http://rdf.ncbi.nlm.nih.gov/pubchem/measuregroup'),
        'endpoint': ('endpoint', '*.ttl.gz', 'http://rdf.ncbi.nlm.nih.gov/pubchem/endpoint'),
        'protein': ('protein', '*.ttl.gz', 'http://rdf.ncbi.nlm.nih.gov/pubchem/protein'),
        'pathway': ('pathway', '*.ttl.gz', 'http://rdf.ncbi.nlm.nih.gov/pubchem/pathway'),
        'conserveddomain': ('conserveddomain', '*.ttl.gz', 'http://rdf.ncbi.nlm.nih.gov/pubchem/conserveddomain'),
        'gene': ('gene', '*.ttl.gz', 'http://rdf.ncbi.nlm.nih.gov/pubchem/gene'),
        'source': ('source', '*.ttl.gz', 'http://rdf.ncbi.nlm.nih.gov/pubchem/source'),
        'concept': ('concept', '*.ttl.gz', 'http://rdf.ncbi.nlm.nih.gov/pubchem/source'),
        'reference': ('reference', '*.ttl.gz', 'http://rdf.ncbi.nlm.nih.gov/pubchem/reference')
    }


def query_compounds() -> str:
    return '''
    SPARQL
    PREFIX sio: <http://semanticscience.org/resource/>
    SELECT *
    FROM <http://rdf.ncbi.nlm.nih.gov/pubchem/compound>
    FROM <http://rdf.ncbi.nlm.nih.gov/pubchem/descriptor/compound>
    WHERE {
        GRAPH <http://rdf.ncbi.nlm.nih.gov/pubchem/compound> { ?compound a [] }
        OPTIONAL { ?compound sio:has-attribute _:1 . _:1 a sio:CHEMINF_000382 ; sio:has-value ?iupac_name . }
        OPTIONAL { ?compound sio:has-attribute _:2 . _:2 a sio:CHEMINF_000396 ; sio:has-value ?iupac_inchi . }
        OPTIONAL { ?compound sio:has-attribute _:3 . _:3 a sio:CHEMINF_000376 ; sio:has-value ?can_smiles . }
        OPTIONAL { ?compound sio:has-attribute _:4 . _:4 a sio:CHEMINF_000379 ; sio:has-value ?iso_smiles . }
        OPTIONAL { ?compound sio:has-attribute _:5 . _:5 a sio:CHEMINF_000337 ; sio:has-value ?monoisotopic_mass . }
        OPTIONAL { ?compound sio:has-attribute _:6 . _:6 a sio:CHEMINF_000335 ; sio:has-value ?molecular_formula . }
    }
    '''


def query_synonyms() -> str:
    return '''
    SPARQL
    PREFIX sio: <http://semanticscience.org/resource/>
    SELECT ?compound ?name ?type
    FROM <http://rdf.ncbi.nlm.nih.gov/pubchem/synonym>
    WHERE {
        _:synonym sio:is-attribute-of ?compound ;
                  sio:has-value ?name ;
                  rdf:type ?type .
    }
    ORDER BY ?compound
    '''


def query_synonym_schema() -> str:
    return '''SPARQL
    SELECT DISTINCT ?type
    FROM <http://rdf.ncbi.nlm.nih.gov/pubchem/synonym>
    WHERE {
        [] a ?type
    }
    '''