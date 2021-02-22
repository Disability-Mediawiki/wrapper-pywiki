"""Linking all beneficiaries"""

import requests

# Program identifiers
from SPARQLWrapper import SPARQLWrapper, JSON

sparql = SPARQLWrapper("http://query.linkedopendata.eu/bigdata/namespace/wdq/sparql")
query = """
select distinct ?beneficiary where {
?s <https://linkedopendata.eu/prop/direct/P841> ?beneficiary .
?s <https://linkedopendata.eu/prop/direct/P32> <https://linkedopendata.eu/entity/Q15> .
}
                """
sparql.setQuery(query)
sparql.setReturnFormat(JSON)
results = sparql.query().convert()
link = {}
for result in results['results']['bindings']:
    PARAMS = {
        'text':  result['beneficiary']['value'],
        'language': 'it,en',
        'user': 'open',
        'knowledgebase': 'wikidata',
    }
    #response = requests.get("https://qanswer-core1.univ-st-etienne.fr/api/link", params=PARAMS)
    response = requests.get("http://localhost:4567/api/link", params=PARAMS)

    # Print the status code of the response.
    print(result['beneficiary']['value'])
    print(response.json())
    if len(response.json()) == 1:
        link[result['beneficiary']['value']] = response.json()
    else:
        link[result['beneficiary']['value']] = []



f = open('./data/beneficiaries/italy_linked_top1.csv', "w")
beneficiary_writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
for k in link:
    beneficiary_writer.writerow([k, str(link[k])])
f.close()

# link = {}
# with open('./data/beneficiaries/italy_linked_top1.csv') as csv_file:
#     csv_reader = csv.reader(csv_file, delimiter=',', quotechar='"')
#     for row in csv_reader:
#         if "COMUNE DI" in row[0]:
#             print(row[0])
#             PARAMS = {
#                     'text':  row[0].replace("COMUNE DI",""),
#                     'language': 'it,en',
#                     'user': 'open',
#                     'knowledgebase': 'wikidata',
#                     'conceptMust': 'http://www.wikidata.org/entity/Q747074'
#                 }
#             #response = requests.get("https://qanswer-core1.univ-st-etienne.fr/api/link", params=PARAMS)
#             response = requests.get("http://localhost:4567/api/link", params=PARAMS)
#             print(response.json())
#             if len(response.json()) == 1:
#                 link[row[0]]=response.json()
#             else:
#                 link[row[0]] = []
#         else:
#             link[row[0]]=row[1]
#
# f = open('./data/beneficiaries/italy_linked_top1_communes.csv', "w")
# beneficiary_writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
# for k in link:
#     beneficiary_writer.writerow([k, str(link[k])])
# f.close()