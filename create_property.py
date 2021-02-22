# coding=utf-8
import os
import csv
import pywikibot
from pywikibot import config2
from datetime import datetime
import requests
import json
import csv
from IdSparql import IdSparql

# application config
import configparser
config = configparser.ConfigParser()
config.read('config/application.config.ini')

family = 'my'
mylang = 'my'
familyfile=os.path.relpath("./config/my_family.py")
if not os.path.isfile(familyfile):
  print ("family file %s is missing" % (familyfile))
config2.register_family_file(family, familyfile)
config2.password_file = "user-password.py"
# config2.usernames['my']['my'] = 'DG Regio'
# config2.usernames['my']['my'] = 'WikibaseAdmin'
config2.usernames['my']['my'] = config.get('wikibase','user')

#connect to the wikibase
wikibase = pywikibot.Site("my", "my")
wikibase_repo = wikibase.data_repository()

#Reading CSV
with open('data/Predicates.csv') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    line_count = 0
    for row in csv_reader:
        print(f'Processing line number of {line_count}.')
        if line_count ==0:
            print(f'Column Headings are {", ".join(row)}')
            line_count += 1
        else:
            if not row[2] :
                data = {
                     'datatype': row[1],  # mandatory
                     'descriptions': {
                         'en': {
                             'language': 'en',
                             'value': row[0]+" en"
                         }
                     },
                     'labels': {
                         'en': {
                             'language': 'en',
                             'value': row[0]
                         }
                     }
                }
                params = {
                     'action': 'wbeditentity',
                     'new': 'property',
                     'data': json.dumps(data),
                     'summary': 'creating properties from scripts',
                     'token': wikibase.tokens['edit']
                }
                req = wikibase._simple_request(**params)
                print(req.submit())
            else :
                data = {
                    'datatype': row[1],  # mandatory
                    'descriptions': {
                        'en': {
                            'language': 'en',
                            'value': row[2]
                        }
                    },
                    'labels': {
                        'en': {
                            'language': 'en',
                            'value': row[0]
                        }
                    }
                }
                params = {
                    'action': 'wbeditentity',
                    'new': 'property',
                    'data': json.dumps(data),
                    'summary': 'creating properties from scripts',
                    'token': wikibase.tokens['edit']
                }
                req = wikibase._simple_request(**params)
                print(req.submit())
            line_count += 1
    print(f'Completed Creating Properties total of {line_count}.')

exit()