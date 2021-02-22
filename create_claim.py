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
def searchWikiItem(label):
    if label is None:
        return True
    params = {'action': 'wbsearchentities', 'format': 'json',
              'language': 'en', 'type': 'item', 'limit': 1,
              'search': label}
    request = wikibase._simple_request(**params)
    result = request.submit()
    print(result)
    return True if len(result['search']) > 0 else False

# Searches a Item based on its label on Tripple store
def searchWikiItemSparql(label):
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
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    print(results)
    if (len(results['results']['bindings']) > 0):
        return True
    else:
        return False

wikidata_code_property_id=None
def getWikiDataItemtifier():
    query = """
    select ?wikicode
    {
                      ?wikicode rdfs:label ?plabel .
                      FILTER(?plabel = 'Wikidata QID'@en) .
                      FILTER(lang(?plabel)='fr' || lang(?plabel)='en')
                    }
                    limit 1

    
    """
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    # for result in results['results']['bindings']:
    #     print(result)
    if (len(results['results']['bindings']) > 0):
        wikidata_code_property_id = results['results']['bindings'][0]['s']['value'].split("/")[-1]
    return results


#get items with sparql
def getWikiItemSparql(label):
    query=""
    # sparql = SPARQLWrapper("http://localhost:8989/bigdata/namespace/wdq/sparql")
    # query = """
    #      select ?label ?s where
    #             {
    #               ?s ?p ?o.
    #               ?s rdfs:label ?label .
    #               FILTER(lang(?label)='fr' || lang(?label)='en')
    #               FILTER(?label = '""" + label + """'@en)
    #
    #             }
    #      """
    if(wikidata_code_property_id is not None) :
        query = """
             select ?label ?s  where
                    {
                      ?s ?p ?o.
                      ?s rdfs:label ?label .
                      FILTER NOT EXISTS {?s <http://wikibase.svc/prop/"""+wikidata_code_property_id+"""> []}
                      FILTER(lang(?label)='fr' || lang(?label)='en')
                      FILTER(?label = '""" + label + """'@en)
                     
                    }
             """
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
    #
    # """
    # select ?label ?s  ?pitem where
    #         {
    #           ?s ?p ?o.
    #           ?s rdfs:label ?label .
    #
    #           {
    #             select ?pitem{
    #               ?pitem rdfs:label ?plabel .
    #               FILTER(?plabel = 'Wikidata QID'@en) .
    #               FILTER(lang(?plabel)='fr' || lang(?plabel)='en')
    #             }
    #             limit 1
    #           }
    #
    #           FILTER(lang(?label)='fr' || lang(?label)='en')
    #           FILTER(?label = 'equality'@en)
    #           FILTER NOT EXISTS {?s ?pitem []}
    #
    #          }
    # """
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    # for result in results['results']['bindings']:
    #     print(result)
    print(results)
    return results

def getItems():
    pid = "P31"
    params = {'action': 'wbgetentities', 'ids': pid}
    request = wikibase._simple_request(**params)
    result = request.query()
    print (result["entities"][pid]["descriptions"])

def capitaliseFirstLetter(word):
    # new = list(word)
    # new[0] = word[0].upper()
    # captWord=''.join(new)
    return word.capitalize()

def getClaim(item_id) :
    entity = pywikibot.ItemPage(wikibase_repo, item_id)
    claims = entity.get(u'claims')  # Get all the existing claims
    return claims

#connect to wikidata
wikidata = pywikibot.Site("wikidata", "wikidata")
wikidata_repo = wikidata.data_repository()

#import an item
from util.util import changeItem, changeProperty, importProperty
def importWikiDataConcept(qid):
    arg = qid
    wikidata_item = pywikibot.ItemPage(wikidata_repo, arg)
    wikidata_item.get()
    wikibase_item=changeItem(wikidata_item, wikibase_repo, True)
    return wikidata_item;

def linkWikidataItem(subject, qid):
    data={}
    wikidata_item=importWikiDataConcept(qid)
    property=getWikiItemSparql('Has wikidata substitute item')
    property.get();
    claim = pywikibot.Claim(wikibase_repo, property.getID(), datatype=property.getType())
    claim.setTarget(wikidata_item)
    data['claims'] = claim.toJSON()
    subject.editEntity(data)
    return subject;

def createClaim(subject_string, property_string, object_string, claims_hash) :
    # claims_hash={}
    new_item = {}
    newClaims = []
    data = {}
    #GETTING SUBJECT ITEM
    subject_result=getWikiItemSparql(capitaliseFirstLetter(subject_string).rstrip())
    subject_item={}
    subject_id=None
    if(len(subject_result['results']['bindings']) > 0) :
        subject_uri = subject_result['results']['bindings'][0]['s']['value']
        subject_id = subject_uri.split("/")[-1]
        subject_item = pywikibot.ItemPage(wikibase_repo, subject_id)
        subject_item.get()
        print(subject_item.getID())
    else :
        "CREATE SUBJECT"
    # GETTING PROPERTY ITEM
    property_result = getWikiItemSparql(capitaliseFirstLetter(property_string).rstrip())
    property_item = {}
    property_id=None
    if (len(property_result['results']['bindings']) > 0):
        property_uri=property_result['results']['bindings'][0]['s']['value']
        # property_id=property_uri.rsplit('/', 1)[-1]
        property_id=property_uri.split("/")[-1]
        property_item = pywikibot.PropertyPage(wikibase_repo, property_id)
        print(property_item.getType(), property_item.getID())
    else :
        "CREATE PROPERTY"
        return claims_hash

    # GETTING OBJECT ITEM
    object_item={}

    if(property_item.getType()==PropertyDataType.WikiItem.value):
        object_result = getWikiItemSparql(capitaliseFirstLetter(object_string).rstrip())
        if (len(object_result['results']['bindings']) > 0):
            object_uri = object_result['results']['bindings'][0]['s']['value']
            object_id = object_uri.split("/")[-1]
            object_item = pywikibot.ItemPage(wikibase_repo, object_id)
            print( object_item.getID())
        else:
            "CREATE OBJECT"
            return claims_hash
    elif(property_item.getType()==PropertyDataType.String.value):
        object_item=object_string
    elif (property_item.getType() == PropertyDataType.Quantity.value):
        "NEEDS TO MODIFY THIS CASE"
        return claims_hash
        # object_item = row[3].rstrip()

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
        existing_claims=getClaim(subject_id)
        if u''+property_id+'' in existing_claims[u'claims']:
            pywikibot.output(u'Error: Already claim is created')
            return claims_hash

        print(f"inserting statement for {subject_string.rstrip()} ")
        claim = pywikibot.Claim(wikibase_repo, property_item.getID(), datatype=property_item.getType())
        claim.setTarget(object_item)
        newClaims.append(claim.toJSON())
        data['claims'] = newClaims
        subject_item.editEntity(data)
        claims_hash[subject_item.getID()]={property_item.getID(): {'value':object_item, 'datatype':property_item.getType()}}

        # linking wikidata item with property Has wikidata substitute item
        if (property_item.label() == "Has wikidata code"):
            print("IMPORTING WIKIDATA ITEM")
            linkWikidataItem(subject_item,object_item.rstrip())
            print("DONE IMPORTING WIKIDATA ITEM")
        return claims_hash
    except:
        e = sys.exc_info()[0]
        print(f"ERROR : inserting concept {subject_string.rstrip()} , MESSSAGE >> {e}")


# Creating Claims
def readFileAndProcess(file_url) :
    claims_hash = dict()
    with open(file_url) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            if(row[1]== None or row[2]== None or row[3]== None) :
                line_count += 1
                continue
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
                    claims_hash=createClaim(row[1].rstrip(), row[2].rstrip(), object_row, claims_hash)
                    print(claims_hash)
                except:
                    e = sys.exc_info()[0]
                    print(f"ERROR : inserting concept {row[1].rstrip()} , count : {line_count}, MESSSAGE >> {e}")
            line_count += 1



def test():
    print(config.get('wikibase', 'user'))
    test_item=pywikibot.ItemPage(wikibase_repo, "Q1")
    print(test_item)
    claims=getClaim('Q73')
    print(claims)
    test_item_sparql=getWikiItemSparql('Has wikidata code')
    print(test_item_sparql)

readFileAndProcess('data/Triplets-merged.csv')

# test()
exit()


