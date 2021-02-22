"""Linking top 50 beneficiaries"""

import csv
import requests

with open('./data/beneficiaries/top50-france.csv', encoding='utf-8') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    lines = list(csv_reader)
    line_count = 0
    for row in lines:
        line_count = line_count+1
        if line_count > 0:
            print("the row ", row)
            print(row[0])
            PARAMS = {
                'text': row[0],
                'language': 'fr',
                'user': 'open',
                'knowledgebase': 'wikidata',
            }
            response = requests.get("http://localhost:4567/api/link", params=PARAMS)

            # Print the status code of the response.
            print(response.status_code)
            print(response.json())
            if len(response.json()) > 0:
                lines[line_count][4] = response.json()[0]
            else:
                PARAMS = {
                    'text': row[0].lower().replace('region', '').replace('région', ''),
                    'language': 'fr',
                    'user': 'open',
                    'knowledgebase': 'wikidata',
                }
                response = requests.get("http://localhost:4567/api/link", params=PARAMS)

                # Print the status code of the response.
                print(response.status_code)
                print(response.json())
                if len(response.json()) > 0:
                    lines[line_count][4] = response.json()[0]
            # @GetMapping(value = "/link")
            #public ResponseEntity<?> link(
            #@RequestParam(value = "text") final String text,
            #@RequestParam(value = "language") final String language,
            #@RequestParam(value = "user") final String user,
            #@RequestParam(value = "knowledgebase") final String knowledgebase,
            #@RequestParam(value = "query", defaultValue = "", required = false) final String query,
writer = csv.writer(open('./data/beneficiaries/top50-france_linked.csv', 'w'))
writer.writerows(lines)
