"""Translating labels with eTranslation"""

import os

import pywikibot
from pywikibot import config2
from SPARQLWrapper import SPARQLWrapper, JSON

import etranslation as et
translate_client = et.Client()

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

sparql = SPARQLWrapper("http://query.linkedopendata.eu/bigdata/namespace/wdq/sparql")
query = """
            select ?item where {
                ?item <https://linkedopendata.eu/prop/direct/P35> <https://linkedopendata.eu/entity/Q9934>
            } limit 100
        """
sparql.setQuery(query)
sparql.setReturnFormat(JSON)
results = sparql.query().convert()
for result in results['results']['bindings']:
    qid = result['item']['value'].replace("https://linkedopendata.eu/entity/", "")
    wikibase_item = pywikibot.ItemPage(wikibase_repo, qid)
    wikibase_item.get()
    for language in wikibase_item.labels:
        if language != "en":
            print(language, "--", wikibase_item.labels.get(language))
            old_label = wikibase_item.labels.get(language)
            new_label = translate_client.translate(old_label, source_language=language, format_='txt')
    print("en", "--", new_label)
    new_label_data = {'en': new_label}
    try:
        wikibase_item.editLabels(new_label_data, summary=u'Label in wikibase changed')
    except pywikibot.exceptions.OtherPageSaveError as e:
        raise Exception('This should not happen!')
