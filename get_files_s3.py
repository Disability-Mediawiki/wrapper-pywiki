"""Retrieving Excel files from AWS S3 bucket"""

import os
import boto3

s3 = boto3.resource('s3')

bucket = s3.Bucket('regio-kohesio')

for s3_object in bucket.objects.all():
    path, filename = os.path.split(s3_object.key)
    bucket.download_file(s3_object.key, f"data/{filename}")
