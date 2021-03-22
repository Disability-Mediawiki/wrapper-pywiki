# coding=utf-8
import sys, os, traceback
import csv
import pywikibot
from pywikibot import config2
from datetime import datetime
import requests
import json
import csv
from IdSparql import IdSparql
from SPARQLWrapper import SPARQLWrapper, JSON
import time
from Enum.PropertyDatatypeEnum import PropertyDataType
from pywikibot.data import api
# application config
import configparser
import re
from logger import DebugLogger
"""
THIS CLASS HELPS TO CREATE CLAIMS WITH EXISTING ITEMS AND PROPERTIES
"""

config = configparser.ConfigParser()
config.read('config/application.config.ini')

family = 'my'
mylang = 'my'
familyfile = os.path.relpath("./config/my_family.py")
if not os.path.isfile(familyfile):
    print("family file %s is missing" % (familyfile))
config2.register_family_file(family, familyfile)
config2.password_file = "user-password.py"
config2.usernames['my']['my'] = config.get('wikibase', 'user')

# connect to the wikibase
wikibase = pywikibot.Site("my", "my")
sparql = SPARQLWrapper(config.get('wikibase', 'sparqlEndPoint'))
site = pywikibot.Site()

# connect to wikidata
wikidata = pywikibot.Site("wikidata", "wikidata")


class CreateClaim:
    def __init__(self, wikibase,wikidata, sparql):
        self.sparql=sparql
        self.wikibase=wikibase
        self.wikibase_repo=wikibase.data_repository()
        self.wikidata_repo = wikidata.data_repository()


    # Searches a concept based on its label with a API call
    def searchWikiItem(self, label):
        if label is None:
            return True
        params = {'action': 'wbsearchentities', 'format': 'json',
                  'language': 'en', 'type': 'item', 'limit': 1,
                  'search': label}
        request = self.wikibase._simple_request(**params)
        result = request.submit()
        print(result)
        return True if len(result['search']) > 0 else False

    # Searches a Item based on its label on Tripple store
    def searchWikiItemSparql(self, label):
        # sparql = SPARQLWrapper("http://localhost:8989/bigdata/namespace/wdq/sparql")
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
        if (len(results['results']['bindings']) > 0):
            return True
        else:
            return False

    wikidata_code_property_id = None

    def getWikiDataItemtifier(self):
        query = """
        select ?wikicode
        {
          ?wikicode rdfs:label ?plabel .
          FILTER(?plabel = 'Wikidata QID'@en) .
          FILTER(lang(?plabel)='fr' || lang(?plabel)='en')
        }
        limit 1


        """
        self.sparql.setQuery(query)
        self.sparql.setReturnFormat(JSON)
        results = self.sparql.query().convert()
        # for result in results['results']['bindings']:
        #     print(result)
        if (len(results['results']['bindings']) > 0):
            self.wikidata_code_property_id = results['results']['bindings'][0]['wikicode']['value'].split("/")[-1]
        return results

    # GET A ITEM BY GIVING WIKIDATA QID PROPERTY VALUE
    def getItemIdByWikidataQID(self, qid):
        query = """
            select ?s  ?label where
                            {
                            ?s  ?p ?o; 
                             rdfs:label ?label ;
                              wdt:""" + self.wikidata_code_property_id + """  '""" + qid + """' .
                            }
        """
        self.sparql.setQuery(query)
        self.sparql.setReturnFormat(JSON)
        results = self.sparql.query().convert()
        if (len(results['results']['bindings']) > 0):
            return results['results']['bindings'][0]['s']['value'].split("/")[-1]
        else:
            return None

    # GET ITEM WITH SPARQL
    def getWikiItemSparql(self, label):
        query = ""
        if (self.wikidata_code_property_id is not None):
            query = """
                 select ?label ?s  where
                    {
                      ?s ?p ?o.
                      ?s rdfs:label ?label .
                      FILTER NOT EXISTS {?s wdt:""" + self.wikidata_code_property_id + """ []}
                      FILTER(lang(?label)='fr' || lang(?label)='en')
                      FILTER(?label = '""" + label + """'@en)
    
                    }
                 """
        #     <http://wikibase.svc/prop/P21>
        else:
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
        return results

    def getItems(self):
        pid = "P31"
        params = {'action': 'wbgetentities', 'ids': pid}
        request = self.wikibase._simple_request(**params)
        result = request.query()
        print(result["entities"][pid]["descriptions"])

    def capitaliseFirstLetter(self, word):
        # new = list(word)
        # new[0] = word[0].upper()
        # captWord=''.join(new)
        return word.capitalize()

    def getClaim(self, item_id):
        entity = pywikibot.ItemPage(self.wikibase_repo, item_id)
        claims = entity.get(u'claims')  # Get all the existing claims
        return claims



    # import an item
    from util.util import changeItem, changeProperty, importProperty
    def importWikiDataConcept(self, qid):
        arg = qid
        wikidata_item = pywikibot.ItemPage(self.wikidata_repo, arg)
        wikidata_item.get()
        wikibase_item = self.changeItem(wikidata_item, self.wikibase_repo, True)
        return wikibase_item;

    def linkWikidataItem(self, subject, qid):
        data = {}
        newClaims = []
        wikidata_item = None
        existing_item_id = self.getItemIdByWikidataQID(qid)
        if (existing_item_id is not None):
            wikidata_item = pywikibot.ItemPage(self.wikibase_repo, existing_item_id)
            wikidata_item.get()
        else:
            # IMPORT THE WIKIDATA ITEM TO WIKIBASE
            wikidata_item = self.importWikiDataConcept(qid)
        property_result = self.getWikiItemSparql('Has wikidata substitute item')
        property_id = property_result['results']['bindings'][0]['s']['value'].split("/")[-1]
        property = pywikibot.PropertyPage(self.wikibase_repo, property_id)

        # CHECK ALREADY CLAIMS EXIST IN WIKIBASE
        existing_claims = self.getClaim(subject.id)
        if u'' + property_id + '' in existing_claims[u'claims']:
            pywikibot.output(u'Error: Already item has link to wikidata substitute item')
            return subject
        # Creating claim
        claim = pywikibot.Claim(self.wikibase_repo, property.id, datatype=property.type)
        claim.setTarget(wikidata_item)
        newClaims.append(claim.toJSON())
        data['claims'] = newClaims
        subject.editEntity(data)
        return subject;

    def create_claim(self, subject_string, property_string, object_string,qualifier_prop, qualifier_target, claims_hash):
        # claims_hash={}
        new_item = {}
        newClaims = []
        data = {}
        # GETTING SUBJECT ITEM
        subject_result = self.getWikiItemSparql(self.capitaliseFirstLetter(subject_string).rstrip())
        subject_item = {}
        subject_id = None
        if (len(subject_result['results']['bindings']) > 0):
            subject_uri = subject_result['results']['bindings'][0]['s']['value']
            subject_id = subject_uri.split("/")[-1]
            subject_item = pywikibot.ItemPage(self.wikibase_repo, subject_id)
            subject_item.get()
            print(subject_item.id)
        else:
            "CREATE SUBJECT"
        # GETTING PROPERTY ITEM
        property_result = self.getWikiItemSparql(self.capitaliseFirstLetter(property_string).rstrip())
        property_item = {}
        property_id = None
        if (len(property_result['results']['bindings']) > 0):
            property_uri = property_result['results']['bindings'][0]['s']['value']
            # property_id=property_uri.rsplit('/', 1)[-1]
            property_id = property_uri.split("/")[-1]
            property_item = pywikibot.PropertyPage(self.wikibase_repo, property_id)
            property_item.get();
            print(property_item.type, property_item.id)
        else:
            "CREATE PROPERTY"
            return claims_hash

        # GETTING OBJECT ITEM
        object_item = {}
        if (property_item.type == PropertyDataType.WikiItem.value):
            object_result = self.getWikiItemSparql(self.capitaliseFirstLetter(object_string).rstrip())
            if (len(object_result['results']['bindings']) > 0):
                object_uri = object_result['results']['bindings'][0]['s']['value']
                object_id = object_uri.split("/")[-1]
                object_item = pywikibot.ItemPage(self.wikibase_repo, object_id)
                object_item.get();
                print(object_item.id)
            else:
                "CREATE OBJECT"
                return claims_hash
        elif (property_item.type == PropertyDataType.String.value):

            object_item = str(object_string.rstrip().lstrip())
            object_item = object_item.rstrip().replace('\n',' ').replace('\t',' ')
            object_item=re.sub('\ |\/|\;|\:|\]|\[|\{|\}|\?|\*|\&|\@|\<|\>', ' ', object_item)
        elif (property_item.type == PropertyDataType.ExternalId.value):
            object_item = object_string.rstrip()
        elif (property_item.type == PropertyDataType.Quantity.value):
            "NEEDS TO MODIFY THIS CASE"
            return claims_hash

        # CREATE CLAIM AND EDIT SUBJECT ENTITY
        # "CHECK IF ALREADY CLAIM EXIT IN CREATED CLAIMS"
        if (claims_hash is not None and len(claims_hash) > 0):
            if (claims_hash.get(subject_item.id) is not None and claims_hash.get(subject_item.id).get(
                    property_item.id) is not None):
                existing_target = claims_hash[subject_item.id][property_item.id]
                if (existing_target is not None):
                    if (existing_target['datatype'] == PropertyDataType.String.value):
                        if (existing_target['value'] == object_item):
                            return claims_hash
                    elif (existing_target['datatype'] == PropertyDataType.ExternalId.value):
                        if (existing_target['value'] == object_item):
                            return claims_hash
                    elif (existing_target['datatype'] == PropertyDataType.WikiItem.value):
                        if (existing_target['value'].id == object_item.id):
                            return claims_hash
                    elif (existing_target['datatype'] == PropertyDataType.Quantity.value):
                        "NEEDS TO BE DEFINED"
                        return claims_hash

        # CHECK ALREADY CLAIM EXIST IN WIKIBASE
        existing_claims = self.getClaim(subject_id)
        if u'' + property_id + '' in existing_claims[u'claims']:
            if(property_item.type==PropertyDataType.String.value):
                for claim in existing_claims[u'claims'].get(property_id):
                    if(object_item==str(claim.toJSON().get('mainsnak').get('datavalue').get('value'))):
                        pywikibot.output(u'Error: Already claim is created')
                        return claims_hash
            elif(property_item.type==PropertyDataType.WikiItem.value) :
                for claim in existing_claims[u'claims'].get(property_id):
                    if(object_item.id=='Q'+str(claim.toJSON().get('mainsnak').get('datavalue').get('value').get('numeric-id'))):
                        pywikibot.output(u'Error: Already claim is created')
                        return claims_hash
            elif (property_item.type == PropertyDataType.ExternalId.value):
                for claim in existing_claims[u'claims'].get(property_id):
                    if(object_item==str(claim.toJSON().get('mainsnak').get('datavalue').get('value').get('numeric-id'))):
                        pywikibot.output(u'Error: Already claim is created')
                        return claims_hash

        print(f"inserting statement for {subject_string.rstrip()} ")
        claim = pywikibot.Claim(self.wikibase_repo, property_item.id, datatype=property_item.type)
        claim.setTarget(object_item)
        newClaims.append(claim.toJSON())
        data['claims'] = newClaims
        subject_item.editEntity(data)

        if (claims_hash == None):
            claims_hash = {}
        claims_hash[subject_item.id] = {property_item.id: {'value': object_item, 'datatype': property_item.type}}
        return claims_hash


    def create_qualifier(self,item_id, property_id,qualifier_pid, datatype, target ):
        item=pywikibot.ItemPage(self.wikibase_repo, item_id)
        qualifier = pywikibot.Claim(self.wikibase_repo, qualifier_pid)
        # target = pywikibot.ItemPage(self.wikibase_repo, "Q1")
        qualifier.setTarget(target)
        for claim in item.claims[property_id]: #Finds all statements (P131)
            if item_id not in claim.qualifiers: #If not already exist
                claim.addQualifier(qualifier, summary=u'Adding a qualifier.') #Adding q


    # Creating Claims
    def read_file_and_process(self, file_url):
        claims_hash = {}
        self.getWikiDataItemtifier()
        with open(file_url) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_count = 0
            for row in csv_reader:
                if (row[1] == None or row[2] == None or row[3] == None):
                    line_count += 1
                    continue
                if (line_count == 0):
                    line_count += 1
                else:
                    # CREATE CLAIM AND EDIT SUBJECT ENTITY
                    try:
                        print(f"processin : inserting claim. Concept : {row[1].rstrip()} ,>> Property : {row[2].rstrip()}  row count : {line_count}")
                        print(f'line no {line_count}')
                        object_row = ""
                        qualifier_prop=None
                        qualifier_target=None
                        if (row[3].rstrip().isdigit()):
                            object_row = "Crpd article " + str(row[3]) .rstrip().lstrip()
                        else:
                            object_row = row[3].rstrip()

                        if len(row) > 4 :
                            "CREATE CLAIM WITH QUALIFIER"
                            qualifier_prop=row[5].lower().lstrip().rstrip()
                            qualifier_target=row[6].lower().lstrip().rstrip()

                        claims_hash = self.create_claim(row[1].rstrip(), self.capitaliseFirstLetter(row[2].rstrip()),
                                                       object_row,qualifier_prop, qualifier_target, claims_hash)
                        print(claims_hash)
                    except Exception as e:
                        exc_type, exc_obj, exc_tb = sys.exc_info()
                        tb = traceback.extract_tb(exc_tb)[-1]
                        print(f"ERROR >>>: + {exc_type} , {tb[2]} , {tb[1]}")
                        print(f"ERROR : inserting claim. Concept : {row[1].rstrip()} ,>> Property : {row[2].rstrip()}  row count : {line_count}, MESSSAGE >> {e}")
                        err_msg = f"ERROR : CREATE_CLAIM_V2.:{type(self).__name__} Concept : {row[1].rstrip()} ,>> Property : {row[2].rstrip()}  row count : {line_count}, MESSSAGE >> {e}"
                        exc_type, exc_obj, exc_tb = sys.exc_info()
                        tb = traceback.extract_tb(exc_tb)[-1]
                        err_trace = f"ERROR_TRACE >>>: + {exc_type} , method: {tb[2]} , line-no: {tb[1]}"
                        logger = DebugLogger();
                        logger.logError('CREATE_CLAIM_V2', e, exc_type, exc_obj, exc_tb, tb, err_msg)
                line_count += 1


def start():
    createClaim = CreateClaim(wikibase,wikidata, sparql)
    createClaim.read_file_and_process('data/TripletPrepared.csv')



start()
exit()



