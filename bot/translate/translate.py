import re, sys, os
from pprint import pprint
import pywikibot
from SPARQLWrapper import SPARQLWrapper, JSON
from pywikibot import config2
from datetime import datetime
from TranslatorClient import TranslatorClient
import pandas as pd
from collections import defaultdict
from multiprocessing import Pool, cpu_count
import nltk

try:
    from nltk import sent_tokenize, word_tokenize
except:
    nltk.download('punkt')
    from nltk import sent_tokenize, word_tokenize

MULTILINE = re.compile("[\r\n]+")

translated_label_tag = "translated_label"
translated_summary_tag = "translated_summary"

family = 'my'
mylang = 'my'
familyfile = os.path.relpath("./config/my_family.py")
if not os.path.isfile(familyfile):
    print("family file %s is missing" % (familyfile))
config2.register_family_file(family, familyfile)
config2.password_file = "user-password.py"
config2.usernames['my']['my'] = 'DG Regio'

# connect to the wikibase
wikibase = pywikibot.Site("my", "my")
wikibase_repo = wikibase.data_repository()

translator_client = TranslatorClient()

def crop_summary(text, size=5000):
    text = str(text)
    text = MULTILINE.sub(" ", text).strip()
    if len(text) > size:
        crop_text = ""
        for sentence in sent_tokenize(text):
            if len(crop_text) + len(sentence) + 1 < size:
                crop_text += " " + sentence
            else:
                return crop_text.strip()
        return crop_text.strip()
    else:
        return text

def reformat(text):
    text = text.replace(" ,", ",")
    text = text.replace(" .", ".")
    return text

def crop_label(text, size=400):
    text = str(text)
    if len(text) > size:
        crop_text = ""
        for token in word_tokenize(text):
            if len(crop_text) + len(token) + 1 < size:
                crop_text += " " + token
            else:
                return reformat(crop_text.strip())
        return reformat(crop_text.strip())
    else:
        return text

def update_item_translation(item):
    qid = item[0]
    print(qid)
    translations = item[1]

    wikibase_item = pywikibot.ItemPage(wikibase_repo, qid)
    wikibase_item.get()

    # SUMMARY
    for key, value in translations.items():
        if key.strip().upper() == "SUMMARY":
            translated_summary = crop_summary(value, size=5000)
            if translated_summary is not None and translated_summary.strip() != "":
                # Remove EN claims
                for claim in wikibase_item.claims["P836"]:
                    json_claim = claim.toJSON()
                    claim_lang = json_claim.get("mainsnak", {}).get("datavalue", {}).get("value", {}).get("language", None)
                    
                    if claim_lang == "en":
                        target = claim.getTarget()
                        wikibase_item.removeClaims(claim, summary=u'remove_old_english_translation') 
                
                # add translation in claim
                new_claim = pywikibot.Claim(wikibase_repo, "P836", datatype="monolingualtext")
                target = pywikibot.WbMonolingualText(text=translated_summary, language='en')
                new_claim.setTarget(target)

                # add date as a qualifier of claim
                qualifier = pywikibot.Claim(wikibase_repo, "P10")
                now = datetime.now()
                target = pywikibot.WbTime(now.year, now.month, now.day)
                qualifier.setTarget(target)
                new_claim.addQualifier(qualifier)
                
                # Add claim to wiki item
                try:
                    wikibase_item.addClaim(new_claim, summary=translated_summary_tag)
                except pywikibot.exceptions.OtherPageSaveError as e:
                    print(e)

        # LABEL
        elif key.strip().upper() == "LABEL":
            translated_label = crop_label(value)
                
            try:
                wikibase_item.editLabels({"en": translated_label}, summary=translated_label_tag)
                done = True
            except pywikibot.exceptions.OtherPageSaveError as e:
                print(e)
               
           
        else:
            raise Exception(f"{key} is not a known value. Only 'LABEL' or 'SUMMARY' are accepted")


def translate_batch(batch):
    for language, items in batch.items():

        df = pd.DataFrame(items)
        translated_df = translator_client.translate_dataframe(df, language)
        if translated_df is not None:
            # Transformed the dataframe with key = qid and values = translations
            transformed_df = defaultdict(dict)
            for row in translated_df.to_numpy():
                row = row.tolist()
                transformed_df[row[0]][row[1].upper().strip()] = row[2]
            
            return list(transformed_df.items())
        else:
            return []


def translate_database(query, batch_size=100):

    batches = []

    sparql = SPARQLWrapper("http://query.linkedopendata.eu/bigdata/namespace/wdq/sparql")

    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    try:
        results = sparql.query().convert()
    except:
        results = {"results":{"bindings":[]}}

    translation_batch = defaultdict(list)
    print(len(results['results']['bindings']))
    for result in results['results']['bindings']:
        qid = result['project']['value'].replace("https://linkedopendata.eu/entity/", "")
       
        wikibase_item = pywikibot.ItemPage(wikibase_repo, qid)
        wikibase_item.get()
        
        # Double Check if really need to translate 
        translate_summary = True
        to_translate = None
        for claim in wikibase_item.claims.get("P836", []):
            json_claim = claim.toJSON()
            claim_lang = json_claim.get("mainsnak", {}).get("datavalue", {}).get("value", {}).get("language", None)
            text = json_claim.get("mainsnak", {}).get("datavalue", {}).get("value", {}).get("text", "")
            if claim_lang == "en":
                translate_summary = False
            else:
                to_translate = {"claim_lang": claim_lang, "text": text}
        if translate_summary == True and to_translate is not None:
            translation_batch[to_translate["claim_lang"]].append([qid, "SUMMARY", to_translate["text"]])


        if "en" not in wikibase_item.labels:
            for language in wikibase_item.labels:
                if language != "en" and wikibase_item.labels.get(language, "").strip() != "":
                    translation_batch[language].append([qid, "LABEL", wikibase_item.labels[language]])
       
        # Create batches of 10 items
        if sum([len(batch) for batch in translation_batch.values()]) > batch_size:
            batches.append(translation_batch)
            translation_batch = defaultdict(list)

        # Send 10 batchs in parallel to the translation
        if len(batches) == cpu_count():            
            print(f"Send {len(batches)} batches of {batch_size} translations to translation")
            pool = Pool(processes=cpu_count())
            translated_batches = pool.map(translate_batch, batches)
            pool.close()
            pool.join()
            print("Update items")
            for translated_batch in translated_batches:
                # Update batch items (no parallelization)
                if translated_batch is not None:
                    for item in translated_batch:
                        update_item_translation(item)
            print("Items updated")
            batches = []
            
    # Process latest items
    if len(translation_batch.keys()) > 0:
        batches.append(translation_batch)
   
    if len(batches) > 0:
        print(f"Send {len(batches)} batches of translations to translation")
        pool = Pool(processes=cpu_count())
        translated_batches = pool.map(translate_batch, batches)
        pool.close()
        pool.join()
        print("Update items")
        for translated_batch in translated_batches:
            for item in translated_batch:
                update_item_translation(item)


if __name__ == "__main__":

    countries = {
        "Q12": "Denmark",
        "Q2": "Ireland",
        "Q20": "France",
        "Q13": "Poland",
        "Q25": "Czech",
        "Q15": "Italy"
    }

    for country_code, country in countries.items():
        print(f"Processing {country}")

        query = """
        select ?project where {
        ?project <https://linkedopendata.eu/prop/direct/P35> <https://linkedopendata.eu/entity/Q9934> .
        ?project <https://linkedopendata.eu/prop/direct/P32> <https://linkedopendata.eu/entity/%s> .
        OPTIONAL {?project rdfs:label ?label filter(lang(?label) = 'en') }
        OPTIONAL {?project <https://linkedopendata.eu/prop/direct/P836> ?summary filter(lang(?summary) != 'en') }
        OPTIONAL {?project <https://linkedopendata.eu/prop/direct/P836> ?summaryEN filter(lang(?summaryEN) = 'en') }
        FILTER (!bound(?label) || (bound(?summary) && !bound(?summaryEN)))
        }
        """ % country_code
        
        translate_database(query)
        print("OK")

