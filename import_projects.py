"""Importing new projects in Wikibase"""

from datetime import date as dt
from datetime import datetime
import os
from pprint import pprint
import sys

import pandas as pd

import pywikibot
from pywikibot import config2

from IdSparql import IdSparql

family = 'my'
mylang = 'my'
familyfile=os.path.relpath("./config/my_family.py")
if not os.path.isfile(familyfile):
    print ("family file %s is missing" % (familyfile))
config2.register_family_file(family, familyfile)
config2.password_file = "user-password.py"
config2.usernames['my']['my'] = 'DG Regio'

#connecting to the wikibase
wikibase = pywikibot.Site("my", "my")
wikibase_repo = wikibase.data_repository()

# listing existing projects
identifier = "P844"
idSparql = IdSparql("http://query.linkedopendata.eu/bigdata/namespace/wdq/sparql", identifier)
dictionaryIdentifiers = idSparql.load()

# listing categories of intervention
idSparql = IdSparql("http://query.linkedopendata.eu/bigdata/namespace/wdq/sparql", "P869")
dictionaryCategoryIdentifiers = idSparql.load()
#print(dictionaryCategoryIdentifiers)

# listing funds
fund_mapping = {"ERDF": "Q2504369", "R": "Q2504369", "ESF": "Q2504370", "S": "Q2504370", "YEI": "Q2504371"}

# listing programmes
prog_mapping = {"ERDF": "Q2463135", "ESF": "Q2463132"} # values for Denmark!

# defining local language
language = "da"

file_path = sys.argv[1]

df = pd.read_csv(file_path, dtype=str)

for index, row in df.iterrows():
    opid = str(row["Operation_Unique_Identifier"])
    data = {}
    newClaims = []
    if opid in dictionaryIdentifiers:
        print(f"Kohesio ID {opid} already exists, aborting.")
        continue

    print(f"Kohesio ID {opid} was not found in Wikibase, proceeding...")
    data['labels'] = {language: row["Operation_Name_Programme_Language"].lstrip().rstrip()} # English label will be added later by bot
    data['descriptions'] = {"en": "Project in Denmark",
                            language: "Projekt i Danmark"} # temporary descriptions, will be changed below when we know the QID

    # contained in NUTS will be added later by bot

    # instance of Kohesio project
    claim = pywikibot.Claim(wikibase_repo, "P35", datatype='wikibase-item')
    wiki_object = pywikibot.ItemPage(wikibase_repo, "Q9934")
    claim.setTarget(wiki_object)
    newClaims.append(claim.toJSON())

    # financed by the EU
    claim = pywikibot.Claim(wikibase_repo, "P890", datatype='wikibase-item')
    wiki_object = pywikibot.ItemPage(wikibase_repo, "Q1")
    claim.setTarget(wiki_object)
    newClaims.append(claim.toJSON())

    # adding the country
    claim = pywikibot.Claim(wikibase_repo, "P32", datatype='wikibase-item')
    wiki_object = pywikibot.ItemPage(wikibase_repo, "Q12")
    claim.setTarget(wiki_object)
    newClaims.append(claim.toJSON())

    # adding the EU contribution
    contrib = row["EU_Contribution"]
    if contrib:
        # add local amount
        claim = pywikibot.Claim(wikibase_repo, "P835",datatype='quantity')
        wikibase_unit = pywikibot.ItemPage(wikibase_repo, "Q217") # Danish krone
        target = pywikibot.WbQuantity(amount=float(contrib), unit=wikibase_unit, site=wikibase_repo)
        claim.setTarget(target)
        newClaims.append(claim.toJSON())

        # add euro amount
        claim = pywikibot.Claim(wikibase_repo, "P835", datatype='quantity')
        wikibase_unit = pywikibot.ItemPage(wikibase_repo, "Q226") # euro
        target = pywikibot.WbQuantity(amount=float(contrib)*0.13, unit=wikibase_unit, site=wikibase_repo)
        claim.setTarget(target)

        # specify exchange rate
        qualifier1 = pywikibot.Claim(wikibase_repo, "P834", datatype='quantity')
        target = pywikibot.WbQuantity(amount=0.13, unit=wikibase_unit, site=wikibase_repo)
        qualifier1.setTarget(target)
        claim.addQualifier(qualifier1)

        # specify time of the exchange rate
        qualifier2 = pywikibot.Claim(wikibase_repo, "P10", datatype='time')
        exchange_date = dt.today().isoformat() + "T00:00:00Z"
        target = pywikibot.WbTime.fromTimestr(site=wikibase_repo, datetimestr=exchange_date, precision=11)
        qualifier2.setTarget(target)
        claim.addQualifier(qualifier2)

        # use euro amount as preferred rank
        claim.setRank("preferred")
        newClaims.append(claim.toJSON())

    # adding the total budget
    budget = row["Total_Eligible_Expenditure_amount"]
    if budget:
        # add local amount
        claim = pywikibot.Claim(wikibase_repo, "P474",datatype='quantity')
        wikibase_unit = pywikibot.ItemPage(wikibase_repo, "Q217") # Danish krone
        target = pywikibot.WbQuantity(amount=float(budget), unit=wikibase_unit, site=wikibase_repo)
        claim.setTarget(target)
        newClaims.append(claim.toJSON())

        # add euro amount
        claim = pywikibot.Claim(wikibase_repo, "P474", datatype='quantity')
        wikibase_unit = pywikibot.ItemPage(wikibase_repo, "Q226") # euro
        target = pywikibot.WbQuantity(amount=float(budget)*0.13, unit=wikibase_unit, site=wikibase_repo)
        claim.setTarget(target)

        # specify exchange rate
        qualifier1 = pywikibot.Claim(wikibase_repo, "P834", datatype='quantity')
        target = pywikibot.WbQuantity(amount=0.13, unit=wikibase_unit, site=wikibase_repo)
        qualifier1.setTarget(target)
        claim.addQualifier(qualifier1)

        # specify time of the exchange rate
        qualifier2 = pywikibot.Claim(wikibase_repo, "P10", datatype='time')
        exchange_date = dt.today().isoformat() + "T00:00:00Z"
        target = pywikibot.WbTime.fromTimestr(site=wikibase_repo, datetimestr=exchange_date, precision=11)
        qualifier2.setTarget(target)
        claim.addQualifier(qualifier2)

        # use euro amount as preferred rank
        claim.setRank("preferred")
        newClaims.append(claim.toJSON())

    # adding co-financing rate
    rate = row["CoFinancing_Rate"]
    if rate:
        if rate.endswith("%"):
            rate = rate.replace("%","").strip()
        claim = pywikibot.Claim(wikibase_repo, "P837", datatype='quantity')
        wikibase_unit = pywikibot.ItemPage(wikibase_repo, "Q660") # percent
        target = pywikibot.WbQuantity(amount=float(rate), unit=wikibase_unit, site=wikibase_repo)
        claim.setTarget(target)
        newClaims.append(claim.toJSON())

    # adding start time
    start = row["Operation_Start_Date"]
    if start:
        claim = pywikibot.Claim(wikibase_repo, "P20", datatype='time')
        date = datetime.strptime(start, "%d/%m/%Y").isoformat() + "Z"
        target = pywikibot.WbTime.fromTimestr(site=wikibase_repo, datetimestr=date, precision=11)
        claim.setTarget(target)
        newClaims.append(claim.toJSON())

    # adding expected end time P838?

    # adding end time
    end = row["Operation_End_Date"]
    if end:
        claim = pywikibot.Claim(wikibase_repo, "P33", datatype='time')
        date = datetime.strptime(end, "%d/%m/%Y").isoformat() + "Z"
        target = pywikibot.WbTime.fromTimestr(site=wikibase_repo, datetimestr=date, precision=11)
        claim.setTarget(target)
        newClaims.append(claim.toJSON())

    # adding beneficiary name (string)
    benef = row["Beneficiary_Name"]
    if benef:
        benef = benef.replace("\n", "").replace("\t", "").lstrip().rstrip()
        claim = pywikibot.Claim(wikibase_repo, "P841", datatype='string')
        claim.setTarget(benef)
        newClaims.append(claim.toJSON())

    # adding beneficiary entity ?

    # adding category of intervention
    coi = row["Category_Of_Intervention"]
    if coi:
        if len(coi) < 3:
            coi = (3 - len(coi)) * "0" + coi
        if coi in dictionaryCategoryIdentifiers:
            claim = pywikibot.Claim(wikibase_repo, "P888", datatype='wikibase-item')
            coi_qid = dictionaryCategoryIdentifiers[coi]
            wiki_object = pywikibot.ItemPage(wikibase_repo, coi_qid)
            claim.setTarget(wiki_object)
            newClaims.append(claim.toJSON())
        else:
            print(f"Unknown CoI: {coi}, skipping...")

    # adding programme and fund
    fund = row["Fund_Code"]
    if fund:
        claim = pywikibot.Claim(wikibase_repo, "P1368", datatype='wikibase-item') # programme
        prog_qid = prog_mapping[fund]
        wiki_object = pywikibot.ItemPage(wikibase_repo, prog_qid)
        claim.setTarget(wiki_object)
        newClaims.append(claim.toJSON())

        claim = pywikibot.Claim(wikibase_repo, "P1584", datatype='wikibase-item') # fund
        fund_qid = fund_mapping[fund]
        wiki_object = pywikibot.ItemPage(wikibase_repo, fund_qid)
        claim.setTarget(wiki_object)
        newClaims.append(claim.toJSON())

    # coordinate location will be added later by bot

    # adding postal code
    postcode = row["Operation_Postcode"]
    if postcode:
        claim = pywikibot.Claim(wikibase_repo, "P460", datatype='string')
        claim.setTarget(postcode)
        newClaims.append(claim.toJSON())

    # adding summary
    summary = row["Operation_Summary_Programme_Language"]
    if isinstance(summary, str):
        summary = summary.replace("\n", "").replace("\t", "").lstrip().rstrip()
        claim = pywikibot.Claim(wikibase_repo, "P836", datatype='monolingualtext')
        wiki_object = pywikibot.WbMonolingualText(text=summary, language=language)
        claim.setTarget(wiki_object)
        newClaims.append(claim.toJSON())
    # English summary will be added later by bot

    # adding the country-specific identifier
    claim = pywikibot.Claim(wikibase_repo, identifier, datatype='external-id')
    claim.setTarget(opid)
    newClaims.append(claim.toJSON())

    #pprint(newClaims)

    # attaching all new claims to data and writing to wikibase
    data['claims'] = newClaims
    try:
        wikibase_item = pywikibot.ItemPage(wikibase_repo)
        wikibase_item.editEntity(data)
        new_qid = wikibase_item.getID()
        print(f"Created new entity: https://linkedopendata.eu/w/index.php?title=Item:{new_qid}")
        new_data = {}
        new_data['descriptions'] = {"en": f"Project {new_qid} in Denmark",
                                language: f"Projekt {new_qid} i Danmark"}
        wikibase_item.editEntity(new_data)
    except pywikibot.exceptions.OtherPageSaveError as e:
        print(f"Import of project {opid} failed!")

    #sys.exit() # stopping after one project for testing
