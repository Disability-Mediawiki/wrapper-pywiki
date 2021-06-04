# coding=utf-8

import configparser
import csv
import sys
import traceback
import pywikibot
from SPARQLWrapper import SPARQLWrapper, JSON
from logger import DebugLogger
import json
from Enum.SchemaKeysEnum import Schema_key
config = configparser.ConfigParser()
config.read('config/application.config.ini')

wikibase = pywikibot.Site("my", "my")
wikidata = pywikibot.Site("wikidata", "wikidata")


class Csv_to_triplet:
    def __init__(self, wikibase, wikidata):
        self.wikibase = wikibase
        self.wikidata = wikidata
        self.wikibase_repo = wikibase.data_repository()
        self.wikidata_repo = wikidata.data_repository()
        self.sparql = SPARQLWrapper(config.get('wikibase', 'sparqlEndPoint'))

    def load_schema(self, schema_path):
        with open(schema_path) as json_file:
            data = json.load(json_file)
            return data

    def capitaliseFirstLetter(self, word):
        # new = list(word)
        # new[0] = word[0].upper()
        # captWord=''.join(new)
        return word.capitalize()

    # get items with sparql
    def getWikiItemSparql(self, label):
        query = """
             select ?label ?s where
                    {
                      ?s ?p ?o.
                      ?s rdfs:label ?label .
                      FILTER(lang(?label)='fr' || lang(?label)='en')
                      FILTER(?label = '""" + label + """'@en)

                    }
             """
        self.sparql.setQuery(query)
        self.sparql.setReturnFormat(JSON)
        results = self.sparql.query().convert()
        print(results)
        return results

    def read_language_list(self):
        filepath = 'util\language_list'
        lang_list = []
        with open(filepath) as fp:
            line = fp.readline()
            while line:
                lang_list.append(line.replace("\n", ""))
                line = fp.readline()
        return lang_list

    def createItem(self, label, description, key, entity_list):
        # check whether concept already inserted
        if (self.capitaliseFirstLetter(key.rstrip()) in entity_list):
            return entity_list
        entity = self.getWikiItemSparql(self.capitaliseFirstLetter(key.rstrip()))
        isExistAPI = self.searchWikiItem(self.capitaliseFirstLetter(key.rstrip()))
        if (len(entity['results']['bindings']) == 0 and not isExistAPI):
            data = {}
            print(f"inserting concept {key.rstrip()} ")
            data['labels'] = label
            data['descriptions'] = description
            new_item = pywikibot.ItemPage(self.wikibase_repo)
            new_item.editEntity(data)
            entity_list[self.capitaliseFirstLetter(key.rstrip())] = new_item.getID()
            return entity_list
        else:
            entity = self.getWikiItemSparql(self.capitaliseFirstLetter(key.rstrip()))
            entity_list[self.capitaliseFirstLetter(key.rstrip())] = \
            entity['results']['bindings'][0]['s']['value'].split("/")[
                -1]
            return entity_list

    def readFileAndProcess(self, filePath, schema_path):
        schema_data=self.load_schema(schema_path)
        entities = schema_data.get(Schema_key.Entity.value, {})
        relations = schema_data.get(Schema_key.Relation.value, {})
        predicates = schema_data.get(Schema_key.Predicate.value, {})
        ignores = schema_data.get(Schema_key.Ignore.value, {})

        title_index={}
        entity_list = {}
        with open(filePath) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_count = 0
            for row in csv_reader:
                if (line_count == 0):
                    for index in range(len(row)):
                        title_index[row[index]]=index
                    line_count += 1
                else:
                    try:
                        for ignore in ignores:
                            if(row[title_index.get(ignore['column'])]==ignore['value']):
                                line_count+=1
                                continue;
                    except Exception as e:
                        err_msg = f"ERROR :Create Concept:  {row[0].rstrip()} Row count: {line_count}"
                        exc_type, exc_obj, exc_tb = sys.exc_info()
                        tb = traceback.extract_tb(exc_tb)[-1]
                        err_trace = f"ERROR_TRACE >>>: + {exc_type} , method: {tb[2]} , line-no: {tb[1]}"
                        logger = DebugLogger();
                        logger.logError('CREATE_ITEM', e, exc_type, exc_obj, exc_tb, tb, err_msg)
                    line_count += 1


def start():
    create_item = Csv_to_triplet(wikibase, wikidata)
    create_item.readFileAndProcess('data/employment_disable.csv', "data/schema.json")
    # create_item.load_schema('data/schema.json')

start()
exit()