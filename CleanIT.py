"""Cleaning Italian projects"""

import csv
from datetime import datetime
from multiprocessing import Pool
import os

import numpy as np
import pywikibot
from pywikibot import config2
from pywikibot.data import api
import requests
from SPARQLWrapper import SPARQLWrapper, JSON

from IdSparql import IdSparql

family = 'my'
mylang = 'my'
familyfile = os.path.relpath("./config/my_family.py")
if not os.path.isfile(familyfile):
    print("family file %s is missing" % (familyfile))
config2.register_family_file(family, familyfile)
config2.password_file = "user-password.py"
config2.usernames['my']['my'] = 'DG Regio'

#connect to the wikibase
wikibase = pywikibot.Site("my", "my")
wikibase_repo = wikibase.data_repository()

idSparql = IdSparql("http://query.linkedopendata.eu/bigdata/namespace/wdq/sparql", "P1357")
dictionaryIdentifiers = idSparql.load()
print(dictionaryIdentifiers)



# Category of intervention Identifier P869
idSparql = IdSparql("http://query.linkedopendata.eu/bigdata/namespace/wdq/sparql", "P869")
dictionaryCategoryIdentifiers = idSparql.load()

# Beneficiary id P869
idSparql = IdSparql("http://query.linkedopendata.eu/bigdata/namespace/wdq/sparql", "P1358")
dictionaryBeneficiariesIdentifiers = idSparql.load()

print("All queries done")

def get_items(site, item_title, language):
    """
    Requires a site and search term (item_title) and returns the results.
    """
    params = {"action": "wbsearchentities",
              "format": "json",
              "language": language,
              "type": "item",
              "search": item_title}
    request = api.Request(site=site, **params)
    return request.submit()


def find(name, language, min_number, max_number):
    print("min_number ", min_number, ' max_number', max_number)
    mid = min_number + (max_number - min_number) // 2
    print(name+"_"+str(min_number))
    print(mid)
    if len(get_items(wikibase, name+"_"+str(min_number), language)['search']) == 0:
        return min_number
    elif len(get_items(wikibase, name + "_" + str(mid), language)['search']) > 0:
        return find(name, language, mid+1, max_number)
    else:
        return find(name, language, min_number, mid)

# print("here ",find("*individuo*",1,200))

def import_chunk(chunk):
    with open('./data/IT_correct.csv', encoding='utf-8') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            line_count += 1
            if line_count > 1 and line_count in chunk:
                newClaims = []
                # print('----')
                # print(row[1])
                # print(row[2])
                # print("webpage "+row[4])
                # print('eu budget '+row[53])
                # print('totoal budget ' + row[72])
                # print('summary ' + row[3])
                # print('intervention ' + row[20])
                # beneficiary_id = row[155].split(":::")
                # for i in range(0, len(beneficiary_id)):
                #     print(beneficiary_id[i])
                # print('start time ',row[101])
                # print('expected end time ', row[101])
                # print('end time ', row[103])
                print("Identifier", row[1])
                wikibase_item = None
                data = {}
                if not row[1] in dictionaryIdentifiers:
                    print("enter here", row[1])
                    wikibase_item = pywikibot.ItemPage(wikibase_repo)
                    data['labels'] = {"it": row[2][0:400].lstrip().rstrip()}
                    data['descriptions'] = {"en": "Project in Italy financed by DG Regio",
                                            "it": "Progetto in Italia finanziato da DG Regio"}
                    # adding the identifier
                    claim = pywikibot.Claim(wikibase_repo, "P1357", datatype='external-id')
                    claim.setTarget(row[1])
                    newClaims.append(claim.toJSON())

                    # #adding identifier www.opencoesione.gov.it/progetti/4mpi1011a-fsepon-ab-2017-1
                    # claim = pywikibot.Claim(wikibase_repo, "P1359", datatype='external-id')
                    # claim.setTarget(row[4].replace('www.opencoesione.gov.it/progetti/',''))
                    # newClaims.append(claim.toJSON())



                    # else:
                    #     print("is created")
                    #     wikibase_item = pywikibot.ItemPage(wikibase_repo, dictionaryIdentifiers.get(row[1]))
                    #     wikibase_item.get()
                    #     new_id = wikibase_item.getID()
                    #     claimsToRemove = []
                    #     for wikibase_claims in wikibase_item.claims:
                    #        for wikibase_c in wikibase_item.claims.get(wikibase_claims):
                    #            if wikibase_c.toJSON().get('mainsnak').get('property') != "P1357":
                    #             claimsToRemove.append(wikibase_c)
                    #     if len(claimsToRemove)>0:
                    #        wikibase_item.removeClaims(claimsToRemove)

                    # project by DG Regio
                    claim = pywikibot.Claim(wikibase_repo, "P35", datatype='wikibase-item')
                    wiki_object = pywikibot.ItemPage(wikibase_repo, "Q9934")
                    claim.setTarget(wiki_object)
                    newClaims.append(claim.toJSON())

                    # financed by the EU
                    claim = pywikibot.Claim(wikibase_repo, "P890", datatype='wikibase-item')
                    wiki_object = pywikibot.ItemPage(wikibase_repo, "Q1")
                    claim.setTarget(wiki_object)
                    newClaims.append(claim.toJSON())
                    claim = pywikibot.Claim(wikibase_repo, "P890", datatype='wikibase-item')
                    wiki_object = pywikibot.ItemPage(wikibase_repo, "Q8361")
                    claim.setTarget(wiki_object)
                    newClaims.append(claim.toJSON())


                    if row[20] != "":
                        if str(row[20]) in dictionaryCategoryIdentifiers:
                            claim = pywikibot.page.Claim(wikibase_repo, "P888", datatype='wikibase-item')
                            wiki_object = pywikibot.ItemPage(wikibase_repo, dictionaryCategoryIdentifiers.get(str(row[20])))
                            claim.setTarget(wiki_object)
                            newClaims.append(claim.toJSON())
                        elif  "0"+str(row[20]) in dictionaryCategoryIdentifiers:
                            claim = pywikibot.page.Claim(wikibase_repo, "P888", datatype='wikibase-item')
                            wiki_object = pywikibot.ItemPage(wikibase_repo, dictionaryCategoryIdentifiers.get('0'+str(row[20])))
                            claim.setTarget(wiki_object)
                            newClaims.append(claim.toJSON())
                    print(newClaims)

                    # adding the country, i.e. italy
                    claim = pywikibot.Claim(wikibase_repo, "P32", datatype='wikibase-item')
                    wiki_object = pywikibot.ItemPage(wikibase_repo, "Q15")
                    claim.setTarget(wiki_object)
                    newClaims.append(claim.toJSON())

                    if row[53] != "":
                        #adding the budget by the EU
                        claim = pywikibot.page.Claim(wikibase_repo, "P835", datatype='quantity')
                        wikibase_unit = pywikibot.ItemPage(wikibase_repo, "Q226")
                        # 24892,21
                        target = pywikibot.WbQuantity(amount=float(row[53]), unit=wikibase_unit, site=wikibase_repo)
                        claim.setTarget(target)
                        newClaims.append(claim.toJSON())


                    # adding the total budget
                    if row[72] != "":
                        claim = pywikibot.page.Claim(wikibase_repo, "P474", datatype='quantity')
                        wikibase_unit = pywikibot.ItemPage(wikibase_repo, "Q226")
                        # 14,235,902.00
                        target = pywikibot.WbQuantity(amount=float(row[72]), unit=wikibase_unit,
                                                      site=wikibase_repo)
                        claim.setTarget(target)
                        newClaims.append(claim.toJSON())

                    # co-financing rate P671
                    claim = pywikibot.page.Claim(wikibase_repo, "P837", datatype='quantity')
                    wikibase_unit = pywikibot.ItemPage(wikibase_repo, "Q660")
                    target = pywikibot.WbQuantity(amount=(float(row[53])/float(row[72])*100), unit=wikibase_unit,
                                                  site=wikibase_repo)
                    claim.setTarget(target)
                    newClaims.append(claim.toJSON())

                    # adding the postal code
                    print(row[50]+", "+row[48]+", "+row[46])
                    if row[50] != "":
                        # claim = pywikibot.Claim(wikibase_repo, "P460", datatype='string')
                        # claim.setTarget(row[4])
                        # newClaims.append(claim.toJSON())

                        #materialize geo corrdinates
                        #print("http://ec2-18-184-14-117.eu-central-1.compute.amazonaws.com:7070/search/search?postalcode="+row[4].replace(" ","")+"&format=json&addressdetails=1")
                        payload = {'q': row[50]+", "+row[48]+", "+row[46], 'format': 'json', 'addressdetails': '1'}
                        response = requests.get("http://18.196.139.9/search/search", params=payload)
                        print(response)
                        print(response.json())
                        found = False
                        for r in response.json():
                            if (r["address"]["country"] == "Italy" or r["address"]["country"] == "Italia") and not found:
                                found = True
                                claim = pywikibot.page.Claim(wikibase_repo, "P127", datatype='globe-coordinate')
                                target = pywikibot.Coordinate(site=wikibase_repo, lat=float(r["lat"]), lon=float(r["lon"]),
                                                              globe_item="http://www.wikidata.org/entity/Q2",
                                                              precision=0.00001
                                                             )
                                claim.setTarget(target)
                                newClaims.append(claim.toJSON())

                    #start time P20
                    if row[101] != "":
                        claim = pywikibot.Claim(wikibase_repo, "P20", datatype='time')
                        claim = pywikibot.page.Claim(wikibase_repo, "P20",
                                                     datatype='time')
                        #2018-10-01
                        print(row[101])
                        date = datetime.strptime(row[101], "%Y%m%d").isoformat()+"Z"
                        target = pywikibot.WbTime.fromTimestr(site=wikibase_repo, datetimestr=date, precision=11)
                        claim.setTarget(target)
                        newClaims.append(claim.toJSON())

                    # expected end time P838
                    if row[102] != "":
                        claim = pywikibot.page.Claim(wikibase_repo, "P838",
                                                     datatype='time')
                        date = datetime.strptime(row[102], "%Y%m%d").isoformat() + "Z"
                        target = pywikibot.WbTime.fromTimestr(site=wikibase_repo, datetimestr=date, precision=11)
                        claim.setTarget(target)
                        newClaims.append(claim.toJSON())

                    # end time P33
                    if row[103] != "":
                        claim = pywikibot.page.Claim(wikibase_repo, "P33",
                                                     datatype='time')
                        date = datetime.strptime(row[103], "%Y%m%d").isoformat() + "Z"
                        target = pywikibot.WbTime.fromTimestr(site=wikibase_repo, datetimestr=date, precision=11)
                        claim.setTarget(target)
                        newClaims.append(claim.toJSON())

                    # beneficiary P672
                    beneficiary = row[156].split(":::")
                    for i, _ in enumerate(beneficiary):
                        claim = pywikibot.Claim(wikibase_repo, "P841", datatype='string')
                        claim.setTarget(beneficiary[i].replace("\n", "").replace("\t", "").lstrip().rstrip())
                        newClaims.append(claim.toJSON())

                    # attach the beneficiary
                    beneficiary_identifier = row[155].split(":::")
                    for i, _ in enumerate(beneficiary_identifier):
                        if beneficiary_identifier[i] in dictionaryBeneficiariesIdentifiers:
                            claim = pywikibot.page.Claim(wikibase_repo, "P889", datatype='wikibase-item')
                            wiki_object = pywikibot.ItemPage(wikibase_repo, dictionaryBeneficiariesIdentifiers[beneficiary_identifier[i]])
                            claim.setTarget(wiki_object)
                            newClaims.append(claim.toJSON())
                            print(newClaims)

                    # adding the description
                    if row[3].replace("\n", "").replace("\t", "").lstrip().rstrip() != "":
                        claim = pywikibot.Claim(wikibase_repo, "P836", datatype='monolingualtext')
                        wiki_object = pywikibot.WbMonolingualText(text=row[3].replace("\n", "").replace("\t", "").lstrip().rstrip(), language="it")
                        claim.setTarget(wiki_object)
                        newClaims.append(claim.toJSON())

                    data['claims'] = newClaims
                #
                #     # fails when entity with the same title already exists .....
                #     if not line_count in dictionaryIdentifiers:
                    try:
                        wikibase_item.editEntity(data)
                        print("Editing")
                    except pywikibot.exceptions.OtherPageSaveError as e:
                        print(e)
                        fine = False
                        index = find("*individuo*", "it", 1, 10000)
                        try:
                            print(row[0] + "_" + str(i))
                            data['labels'] = {"it": row[2][0:400].lstrip().rstrip() + "_" + str(index)}
                            wikibase_item.editEntity(data)
                            fine = True
                        except pywikibot.exceptions.OtherPageSaveError as e:
                            fine = False


dicExisting = set()
sparql = SPARQLWrapper("http://query.linkedopendata.eu/bigdata/namespace/wdq/sparql")
query = """
              select ?s  where {
 ?s <https://linkedopendata.eu/prop/direct/P1357> ?o .
 FILTER NOT EXISTS {?s <https://linkedopendata.eu/prop/direct/P1360> ?o2 .}
}
        """
sparql.setQuery(query)
sparql.setReturnFormat(JSON)
results = sparql.query().convert()
for result in results['results']['bindings']:
    qid = result['s']['value'].replace("https://linkedopendata.eu/entity/", "")
    dicExisting.add(qid)

def process(chunk):
    line_count = 0
    with open('./data/IT_correct.csv', encoding='utf-8') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for row in csv_reader:
            line_count += 1
            if row[1] in dictionaryIdentifiers and dictionaryIdentifiers[row[1]] in dicExisting and line_count in chunk:
                wikibase_item = pywikibot.ItemPage(wikibase_repo, dictionaryIdentifiers.get(row[1]))
                wikibase_item.get()
                data = {}
                newClaims = []
                # adding the identifier
                claim = pywikibot.Claim(wikibase_repo, "P1360", datatype='external-id')
                claim.setTarget(row[4].replace("www.opencoesione.gov.it/progetti/", ""))
                newClaims.append(claim.toJSON())
                data['claims'] = newClaims
                wikibase_item.editEntity(data)

if __name__ == '__main__':
    it_line_count = 0
    with open('./data/IT_correct.csv', encoding='utf-8') as it_csv_file:
        it_csv_reader = csv.reader(it_csv_file, delimiter=',')
        for _ in it_csv_reader:
            it_line_count += 1
    processes = 8
    lst = range(it_line_count)
    print(lst)
    chunks = np.array_split(lst, processes)
    print(chunks)

    pool = Pool(processes=processes)
    print("starting")
    results = pool.map(process, chunks)
    print(results)

# lst = range(it_line_count)
# import_chunk(lst)
