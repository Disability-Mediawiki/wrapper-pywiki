# coding=utf-8
import os
import csv
import sys
import pywikibot
from pywikibot import config2
from datetime import datetime
import requests
import json
import csv
from IdSparql import IdSparql
from SPARQLWrapper import SPARQLWrapper, JSON
import time
from Enum.PropertyDatatypeEnum  import PropertyDataType
from pywikibot.data import api
# application config
import configparser


"""
THIS CLASS HELPS TO CREATE CLAIMS WITH EXISTING ITEMS AND PROPERTIES
"""
class CreateClaim :

    config = configparser.ConfigParser()
    config.read('config/application.config.ini')


    family = 'my'
    mylang = 'my'
    familyfile = os.path.relpath("./config/my_family.py")
    if not os.path.isfile(familyfile):
        print("family file %s is missing" % (familyfile))
    config2.register_family_file(family, familyfile)
    config2.password_file = "user-password.py"
    # config2.usernames['my']['my'] = 'DG Regio'
    # config2.usernames['my']['my'] = 'WikibaseAdmin'
    config2.usernames['my']['my'] = config.get('wikibase','user')

    # connect to the wikibase
    wikibase = pywikibot.Site("my", "my")
    wikibase_repo = wikibase.data_repository()

    sparql = SPARQLWrapper(config.get('wikibase','sparqlEndPoint'))
    site = pywikibot.Site()

    # Searches a concept based on its label with a API call
    def searchWikiItem(self,label):
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
    def searchWikiItemSparql(self,label):
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

    wikidata_code_property_id=None
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


    def getItemIdByWikidataQID(self, qid):
        query="""
            select ?s  ?label where
                            {
                            ?s  ?p ?o; 
                             rdfs:label ?label ;
                              wdt:"""+self.wikidata_code_property_id+"""  '"""+qid+"""' .
                            }
        """
        self.sparql.setQuery(query)
        self.sparql.setReturnFormat(JSON)
        results = self.sparql.query().convert()
        if (len(results['results']['bindings']) > 0):
            return  results['results']['bindings'][0]['s']['value'].split("/")[-1]
        else:
            return None

    #get items with sparql
    def getWikiItemSparql(self,label):
        query=""
        if(self.wikidata_code_property_id is not None) :
            query = """
                 select ?label ?s  where
                        {
                          ?s ?p ?o.
                          ?s rdfs:label ?label .
                          FILTER NOT EXISTS {?s wdt:"""+self.wikidata_code_property_id+""" []}
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
        print (result["entities"][pid]["descriptions"])

    def capitaliseFirstLetter(self,word):
        # new = list(word)
        # new[0] = word[0].upper()
        # captWord=''.join(new)
        return word.capitalize()

    def getClaim(self,item_id) :
        entity = pywikibot.ItemPage(self.wikibase_repo, item_id)
        claims = entity.get(u'claims')  # Get all the existing claims
        return claims

    #connect to wikidata
    wikidata = pywikibot.Site("wikidata", "wikidata")
    wikidata_repo = wikidata.data_repository()

    #import an item
    from util.util import changeItem, changeProperty, importProperty
    def importWikiDataConcept(self,qid):
        arg = qid
        wikidata_item = pywikibot.ItemPage(self.wikidata_repo, arg)
        wikidata_item.get()
        wikibase_item=self.changeItem(wikidata_item, self.wikibase_repo, True)
        return wikidata_item;

    def linkWikidataItem(self, subject, qid):
        data={}
        newClaims = []
        wikidata_item=None
        existing_item_id=self.getItemIdByWikidataQID(qid)
        if(existing_item_id is not None) :
            wikidata_item = pywikibot.ItemPage(self.wikibase_repo, existing_item_id)
            wikidata_item.get()
        else:
            wikidata_item=self.importWikiDataConcept(qid)
        property_result=self.getWikiItemSparql('Has wikidata substitute item')
        property_id = property_result['results']['bindings'][0]['s']['value'].split("/")[-1]
        property = pywikibot.PropertyPage(self.wikibase_repo, property_id)

        # CHECK ALREADY CLAIMS EXIST IN WIKIBASE
        existing_claims = self.getClaim(subject.getID())
        if u'' + property_id + '' in existing_claims[u'claims']:
            pywikibot.output(u'Error: Already item has link to wikidata substitute item')
            return subject
        # Creating claim
        claim = pywikibot.Claim(self.wikibase_repo, property.getID(), datatype=property.getType())
        claim.setTarget(wikidata_item)
        newClaims.append(claim.toJSON())
        data['claims'] = newClaims
        subject.editEntity(data)
        return subject;

    def createClaim(self, subject_string, property_string, object_string, claims_hash) :
        # claims_hash={}
        new_item = {}
        newClaims = []
        data = {}
        #GETTING SUBJECT ITEM
        subject_result=self.getWikiItemSparql(self.capitaliseFirstLetter(subject_string).rstrip())
        subject_item={}
        subject_id=None
        if(len(subject_result['results']['bindings']) > 0) :
            subject_uri = subject_result['results']['bindings'][0]['s']['value']
            subject_id = subject_uri.split("/")[-1]
            subject_item = pywikibot.ItemPage(self.wikibase_repo, subject_id)
            subject_item.get()
            print(subject_item.getID())
        else :
            "CREATE SUBJECT"
        # GETTING PROPERTY ITEM
        property_result = self.getWikiItemSparql(self.capitaliseFirstLetter(property_string).rstrip())
        property_item = {}
        property_id=None
        if (len(property_result['results']['bindings']) > 0):
            property_uri=property_result['results']['bindings'][0]['s']['value']
            # property_id=property_uri.rsplit('/', 1)[-1]
            property_id=property_uri.split("/")[-1]
            property_item = pywikibot.PropertyPage(self.wikibase_repo, property_id)
            print(property_item.getType(), property_item.getID())
        else :
            "CREATE PROPERTY"
            return claims_hash

        # GETTING OBJECT ITEM
        object_item={}
        if(property_item.type==PropertyDataType.WikiItem.value):
            object_result = self.getWikiItemSparql(self.capitaliseFirstLetter(object_string).rstrip())
            if (len(object_result['results']['bindings']) > 0):
                object_uri = object_result['results']['bindings'][0]['s']['value']
                object_id = object_uri.split("/")[-1]
                object_item = pywikibot.ItemPage(self.wikibase_repo, object_id)
                print( object_item.getID())
            else:
                "CREATE OBJECT"
                return claims_hash
        elif(property_item.type==PropertyDataType.String.value):
            object_item=object_string.rstrip()
        elif(property_item.type==PropertyDataType.ExternalId.value):
            object_item=object_string.rstrip()
        elif (property_item.type == PropertyDataType.Quantity.value):
            "NEEDS TO MODIFY THIS CASE"
            return claims_hash
            # object_item = row[3].rstrip()

        # # TEST PURPOSE
        # if (property_item.get('labels')['labels']['en'] == "Has wikidata code"):
        #     print("IMPORTING WIKIDATA ITEM")
        #     self.linkWikidataItem(subject_item, object_item.rstrip())
        #     print("DONE IMPORTING WIKIDATA ITEM")
        # # TEST PURPOSE

        # CREATE CLAIM AND EDIT SUBJECT ENTITY
        try:
            # "CHECK IF ALREADY CLAIM EXIT IN CREATED CLAIMS"
            if(claims_hash is not None and len(claims_hash)>0) :
                existing_target=claims_hash[subject_item.getID()][property_item.getID()]
                if(existing_target is not None) :
                    if(existing_target['datatype']==PropertyDataType.String.value) :
                        if(existing_target['value'] == object_item) :
                            return claims_hash
                    elif(existing_target['datatype']==PropertyDataType.WikiItem.value) :
                        if(existing_target['value'].getID() == object_item.getID()) :
                            return claims_hash
                    elif (existing_target['datatype'] == PropertyDataType.Quantity.value):
                        "NEEDS TO BE DEFINED"
                        return claims_hash

            #CHECK ALREADY CLAIMS EXIST IN WIKIBASE
            existing_claims=self.getClaim(subject_id)
            if u''+property_id+'' in existing_claims[u'claims']:
                pywikibot.output(u'Error: Already claim is created')
                return claims_hash

            print(f"inserting statement for {subject_string.rstrip()} ")
            claim = pywikibot.Claim(self.wikibase_repo, property_item.getID(), datatype=property_item.getType())
            claim.setTarget(object_item)
            newClaims.append(claim.toJSON())
            data['claims'] = newClaims
            subject_item.editEntity(data)
            claims_hash[subject_item.getID()]={property_item.getID(): {'value':object_item, 'datatype':property_item.getType()}}

            # linking wikidata item with property Has wikidata substitute item
            if (property_item.get('labels')['labels']['en'] == "Has wikidata code"):
                print("ATTEMPTING TO LINK WIKIDATA ITEM")
                try:
                    self.linkWikidataItem(subject_item,object_item.rstrip())
                    print("DONE LINKING WIKIDATA ITEM")
                except:
                    e = sys.exc_info()[0]
                    print(f"ERROR : LINKING WIKIDATA ITEM {subject_string.rstrip()} , MESSSAGE >> {e}")
            return claims_hash
        except:
            e = sys.exc_info()[0]
            print(f"ERROR : inserting concept {subject_string.rstrip()} , MESSSAGE >> {e}")


    # Creating Claims
    def readFileAndProcess(self, file_url) :
        claims_hash = dict()
        self.getWikiDataItemtifier()
        with open(file_url) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_count = 0
            for row in csv_reader:
                if(row[1]== None or row[2]== None or row[3]== None) :
                    line_count += 1
                    continue
                if (self.capitaliseFirstLetter(row[2].rstrip()) == 'Has wikidata code'):  # Skipping heading row
                    print("asd")
                if (line_count == 0): #Skipping heading row
                    line_count += 1
                else:
                    # CREATE CLAIM AND EDIT SUBJECT ENTITY
                    try:
                        print(f'processing {row[1].rstrip()} on  line no {line_count}')
                        object_row=""
                        if(row[3].rstrip().isdigit()):
                            object_row="Article "+row[3].rstrip()
                        else:
                            object_row = row[3].rstrip()
                        claims_hash=self.createClaim(row[1].rstrip(), row[2].rstrip(), object_row, claims_hash)
                        print(claims_hash)
                    except:
                        e = sys.exc_info()[0]
                        print(f"ERROR : inserting concept {row[1].rstrip()} , count : {line_count}, MESSSAGE >> {e}")
                line_count += 1



def test():
    test=CreateClaim()
    property=pywikibot.PropertyPage(test.wikibase_repo, 'P7')
    print(property)

    claim_hash={}
    claim_hash= test.createClaim("Health", "Has wikidata code", "Q37115910", claim_hash)
    print(claim_hash)
    # test_item_sparql=getWikiItemSparql('Has wikidata code')
    # print(test_item_sparql)

# readFileAndProcess('data/Triplets-merged.csv')
def start():
    createClaim=CreateClaim()
    createClaim.readFileAndProcess('data/Triplets.csv')

start()
# test()
exit()



