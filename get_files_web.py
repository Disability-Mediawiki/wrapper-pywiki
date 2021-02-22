"""Retrieving Excel files from MS websites"""

from io import BytesIO
import os.path
from pathlib import Path
from zipfile import ZipFile

import pandas as pd
import requests

Path("data/").mkdir(parents=True, exist_ok=True)
filelist = open("file_list.csv").readlines()
output_dir = "data/"
for line in filelist:
    country, url = line.strip().split(",")
    output_filename = f"{output_dir}{country}.csv"
    if not os.path.isfile(output_filename):
        r = requests.get(url, allow_redirects=True)
        filename = url.split("/")[-1]
        if filename.endswith(".zip"):
            file_content = r.content
            with ZipFile(BytesIO(file_content), 'r') as zipdata:
                zipinfos = zipdata.infolist()
                for zipinfo in zipinfos:
                    zipinfo.filename = f"{output_dir}{country}.csv"
                    zipdata.extract(zipinfo)
            print(f"{country} imported successfully")
        elif filename.endswith(".csv"):
            file_content = r.content.decode(r.apparent_encoding)
            open(output_filename, 'w').write(file_content)
            print(f"{country} imported successfully")
        elif filename.endswith(".xls") or filename.endswith(".xlsx"):
            file_content = r.content
            data_xls = pd.read_excel(BytesIO(file_content), index_col=None)
            data_xls.to_csv(output_filename, encoding='utf-8', index=False)
            print(f"{country} imported successfully")
        else:
            print(f"{filename} is not supported yet!")
