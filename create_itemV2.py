# coding=utf-8

import configparser
import csv
import sys
import traceback

import pywikibot
from SPARQLWrapper import SPARQLWrapper, JSON

from logger import DebugLogger

config = configparser.ConfigParser()
config.read('config/application.config.ini')

wikibase = pywikibot.Site("my", "my")

class Create_item:
    def __init__(self, wikibase):
        self.wikibase=wikibase
        self.wikibase_repo = wikibase.data_repository()
        self.sparql= SPARQLWrapper(config.get('wikibase', 'sparqlEndPoint'))


    # Searches a concept based on its label with a API call
    def searchWikiItem(self,label):
        if label is None:
            return True
        params = {'action': 'wbsearchentities', 'format': 'json',
                  'language': 'en', 'type': 'item',
                  # 'limit': 1,
                  'search': label}
        request = self.wikibase._simple_request(**params)
        result = request.submit()
        print(result)
        if(len(result['search']) > 0):
            for item in result['search']:
                if (item.get('label')==label) :
                    return True
        return False


    # Searches a concept based on its label on Tripple store
    def searchWikiItemSparql(self,label):
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
        # for result in results['results']['bindings']:
        #     print(result)
        print(results)
        if (len(results['results']['bindings']) > 0):
            return True
        else:
            return False


    def capitaliseFirstLetter(self,word):
        # new = list(word)
        # new[0] = word[0].upper()
        # captWord=''.join(new)
        return word.capitalize()


    # get items with sparql
    def getWikiItemSparql(self,label):
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
        lang_list=[]
        with open(filepath) as fp:
            line = fp.readline()
            while line:
                lang_list.append(line.replace("\n", ""))
                line = fp.readline()
        return lang_list


    def createItem(self,label, description, key, entity_list):
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

            # INSTANCE OF CLAIM
            if "Crpd article" in key:
                document_class_entity = pywikibot.ItemPage(
                    self.wikibase_repo, 'Q1')
                document_class_entity.get()
                instance_of_property = pywikibot.PropertyPage(
                    self.wikibase_repo, 'P29')
                instance_of_property.get()
                instance_claim = pywikibot.Claim(
                    self.wikibase_repo, instance_of_property.id, datatype=instance_of_property.type)
                instance_claim.setTarget(document_class_entity)
                new_item.addClaim(
                    instance_claim, summary=u'Adding claim to CRPD Article')
            else:
                topic_class_entity = pywikibot.ItemPage(
                    self.wikibase_repo, 'Q2')
                topic_class_entity.get()
                instance_of_property = pywikibot.PropertyPage(
                    self.wikibase_repo, 'P29')
                instance_of_property.get()
                instance_claim = pywikibot.Claim(
                    self.wikibase_repo, instance_of_property.id, datatype=instance_of_property.type)
                instance_claim.setTarget(topic_class_entity)
                new_item.addClaim(
                    instance_claim, summary=u'Adding claim to Topic item')


            entity_list[self.capitaliseFirstLetter(key.rstrip())] = new_item.getID()
            return entity_list
        else:
            entity = self.getWikiItemSparql(self.capitaliseFirstLetter(key.rstrip()))
            entity_list[self.capitaliseFirstLetter(key.rstrip())] = entity['results']['bindings'][0]['s']['value'].split("/")[
                -1]
            return entity_list


    def readFileAndProcess(self,filePath):
        entity_list = {}
        with open(filePath) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_count = 0
            for row in csv_reader:
                new_item = {}
                print(f'processing line no {line_count}')
                if (line_count == 0):
                    line_count += 1
                else:
                    try:
                        list = self.read_language_list()
                        data = {}
                        print(f"inserting concept {row[1].rstrip()} , count : {line_count}")


                        labels={}
                        if len(row[1]) >0:
                            label_row = row[1].rstrip().lstrip().split("|")
                            for label in label_row:
                                language=label.rstrip().lstrip().split("-")[0].rstrip().lstrip().replace("/n","")
                                value=label.rstrip().lstrip().split("-")[1].rstrip().lstrip().replace("/n","")
                                if language in list:
                                    labels[language]=value
                        else:
                            labels = {"en": self.capitaliseFirstLetter(row[0].rstrip().lstrip())}
                        if len(row[2]) > 0:
                            description_row = row[2].rstrip().lstrip().split("|")
                            descriptions = {}
                            for description in description_row:
                                language=description.rstrip().lstrip().split("-")[0].rstrip().lstrip().replace("/n","")
                                value=description.rstrip().lstrip().split("-")[1].rstrip().lstrip().replace("/n","")
                                if language in list:
                                    descriptions[language]=value
                        else:
                            descriptions = {"en": self.capitaliseFirstLetter(row[0].rstrip().lstrip()) + " entity"}
                        entity_list = self.createItem(labels, descriptions, row[0].rstrip().lstrip(), entity_list)
                    except Exception as e:
                        err_msg=f"ERROR :Create Concept:  {row[0].rstrip()} Row count: {line_count}"
                        exc_type, exc_obj, exc_tb = sys.exc_info()
                        tb = traceback.extract_tb(exc_tb)[-1]
                        err_trace=f"ERROR_TRACE >>>: + {exc_type} , method: {tb[2]} , line-no: {tb[1]}"
                        logger=DebugLogger();
                        logger.logError('CREATE_ITEM',e, exc_type, exc_obj, exc_tb, tb, err_msg)
                    line_count += 1

    def test(self):
        data = {}
        data['labels'] = {'en': 'TestITEM FROM FLASK',
                          'fr': 'item test france'}
        data['descriptions'] = {'en': 'TestITEM FROM FLASK'}
        new_item = pywikibot.ItemPage(self.wikibase_repo,"Q23")
        new_item.editEntity(data)
        print(new_item.id)


def start():
    create_item=Create_item(wikibase)
    create_item.readFileAndProcess('data/Concepts.csv')
    # create_item.test()

start()
exit()