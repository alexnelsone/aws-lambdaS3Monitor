# This lambda function will be triggered by a schedule and will check
# S3 buckets for Lifecycle policies
# if no policy is defined it will trigger an alert and define the policy 
# for the bucket



from __future__ import print_function
from datetime import datetime, timedelta
import boto3
import logging


# for local testing set profile
# boto3.setup_default_session(profile_name='nelsone')
# boto3.setup_default_session(profile_name='cah-user')
current_session = boto3.session.Session()
current_region = current_session.region_name

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.resource('s3')

# used to evaluate if any returned structures are empty
def is_empty(any_structure):
    if any_structure:
        return False
    else:
        return True
    
    
def list_buckets():
    return s3.buckets.all()

def check_bucket_lifecycle(bucket_name):
    
    try:
        lifecycle = s3.BucketLifecycle(bucket_name)
        if lifecycle.rules:
            return True
    except Exception as e:
        return False

    


def lambda_handler(event, context):
    
    buckets = list_buckets()
    for bucket in buckets:
        print("Checking bucket: " + bucket.name)
        if check_bucket_lifecycle(bucket.name):
            print(bucket.name + " has LifeCycle policy defined.\n\n")
        else:
            print(bucket.name + " does not have LifeCycle policy defined.\n\n")
    
    

    
    

#to test locally
lambda_handler("", "")
