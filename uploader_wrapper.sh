#!/bin/bash

export AWS_ACCESS_KEY_ID=""
export AWS_SECRET_ACCESS_KEY=""
export AWS_REGION="eu-south-2"
export S3_BUCKET_NAME=storeyes-bucket
export S3_PREFIX=gcam-recordings

python3 uploader.py