"""Defining IdSparql class"""

from SPARQLWrapper import SPARQLWrapper, JSON

class IdSparql:
    """This class makes the correspondence between Wikidata entities and entities in the Wikibase using the external identifier for Wikidata"""

    def __init__(self, endpoint, identifier):
        self.map = {}
        self.endpoint = endpoint
        self.identifier = identifier

    def load(self):
        sparql = SPARQLWrapper(self.endpoint)
        query = """
                    select ?item ?id where {
                        ?item <https://linkedopendata.eu/prop/direct/""" + self.identifier + """> ?id
                    }
                """
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        for result in results['results']['bindings']:
            self.map[result['id']['value']] = result['item']['value'].replace("https://linkedopendata.eu/entity/", "")
        return self.map
