"""Name: lambdaS3Monitor
    
   Description:  This function queries all S3 buckets and verifies:
                   1. If bucket has Versioning enabled
                   2. If bucket has a lifecycle policy defined
                   3. If bucket was created by a stack
                 If the bucket has a tag with a key of S3BucketMonitor set to True
                 the function will enable versioning if it is not and set a default lifecycle.
                 If the tag does not exists or is set to False, the bucket will be ignored.
       
 Trust Relationship:
 {
   "Version": "2012-10-17",
   "Statement": [
     {
       "Effect": "Allow",
       "Principal": {
         "Service": "ec2.amazonaws.com"
       },
       "Action": "sts:AssumeRole"
     }
   ]
 }
 
 Policy doc - need to make more explicit
 {
   "Version": "2012-10-17",
   "Statement": [
     {
       "Effect": "Allow",
       "Action": "s3:*",
       "Resource": "*"
     }
   ]
 }
  
 std-bucket-lifecycle Bucket LifeCycle
 {
     "Rules": [
         {
             "Status": "Enabled", 
             "Prefix": "", 
             "Transitions": [
                 {
                     "Days": 30, 
                     "StorageClass": "STANDARD_IA"
                 }, 
                 {
                     "Days": 180, 
                     "StorageClass": "GLACIER"
                 }
             ], 
            "NoncurrentVersionExpiration": {
                 "NoncurrentDays": 30
             }, 
             "ID": "LC"
         }
     ]
 }
"""

import boto3
import logging

# for local testing set profile
# boto3.setup_default_session(profile_name='nelsone')
# boto3.setup_default_session(profile_name='cah-user')
current_session = boto3.session.Session()
current_region = current_session.region_name

logging.basicConfig()
logger = logging.getLogger()

s3resource = boto3.resource('s3')

#Set lifecycle Policy
lifecycleID = "std-bucket-lifecycle"
STANDARD_IA_Days = 30
GLACIER_Days = 180
NoncurrentDays_Days = 90

# used to evaluate if any returned structures are empty
def isEmpty(any_structure):
    if any_structure:
        return False
    else:
        return True
    
    
def list_buckets():
    """Returns a list of buckets
       Expects no arguments     """
    return s3resource.buckets.all()


def check_bucket_lifecycle(bucketName):
    """Checks to see if a lifecycle is applied to a bucket.
        :param bucketName: a string of the bucketName
    """
    try:
        lifecycle = s3resource.BucketLifecycle(bucketName)
        if lifecycle.rules is not None:
            #Used to print the lifecycle to logs
            return str(lifecycle.rules)
    except Exception as e:
        #If there is no lifecycle an error is thrown
        if (e.response['Error']['Code'] == 'NoSuchLifecycleConfiguration'):
            #In this case we'll just return the string None to print to the logs
            return "None"
        else:
            logger.warn("check_bucket_lifecycle err: " + str(e))
    

def check_bucket_versioning(bucketName):
    """ Checks to see if versioining is enabled on a bucket.
         :param bucketName: a string of the bucket name.
    """
    try: 
        versioning = s3resource.BucketVersioning(bucketName)
        #If versioning isn't returned it is not enabled.
        if versioning.status is None:
            #logger.warn(bucketName + " Versioining: Not Enabled")
            return "Not Enabled"
        else:
            return versioning.status
    except Exception as e:
        logger.warn("check_bucket_version err: " + str(e))
        
def bucket_enable_versioning(bucketName):
    """ Sets bucket versioning to Enabled.
        :param bucketName: a string of the bucket name to perform the action against.
    """
    versioning = s3resource.BucketVersioning(bucketName)
    #versioning status can be Enabled or Suspended
    if versioning.status != "Enabled":
        #print("Setting " + bucketName + " versioining to Enabled.")
        #logger.info("Setting " + bucketName + " Versioining to 'Enabled'.")
        versioning.enable()
        return True
    else:
        return False

def get_bucket_tagging(bucketName):
    """ Gets the tags associated with a bucket
        :param bucketName: a string of the bucket name
    """
    try:
        bucketTags = s3resource.BucketTagging(bucketName)
        return bucketTags.tag_set
    except Exception as e:
        if (e.response['Error']['Code'] == 'NoSuchTagSet'):
            return "None"
        else:
            logger.warning("get_bucket_tagging err: " + str(e))

def determine_bucket_stack_created(tags):
    """ Loops through tags looking for cloudformation stack-name tag
        :param tags: a list of dict tags 
    """
    if len(tags) > 0:
        for tag in tags:
            if tag['Key'] == "aws:cloudformation:stack-name":
                return True
    else:
        return False


def determine_skip_bucket(tags):
    """ checks the tags of a bucket to determine if action needs to be performed against bucket.
        :param tags: a list of dict tags
    """
    if len(tags) > 0:
        for tag in tags:
            if tag['Key'] == "S3MonitorIgnore":
                if tag['Value'] == "True":
                    return True    
    else:
        return False
    
def set_bucket_lifecycle(bucketName):
    """Sets the lifecycle on a bucket to a std bucket lifecycle
        :param bucketName: a string with the name of the bucket to perform the action against.
    """
    lifeCycleConfig = {"Rules": [{"Status": "Enabled", "Prefix": "", "Transitions": [{"Days": STANDARD_IA_Days, "StorageClass": "STANDARD_IA"}, {"Days": GLACIER_Days, "StorageClass": "GLACIER"}], "NoncurrentVersionExpiration": {"NoncurrentDays": NoncurrentDays_Days}, "ID": lifecycleID }]}
    logger.info("Setting policy on " + bucketName + " to " + str(lifeCycleConfig))
    
    try:
        client = boto3.client('s3')
        client.put_bucket_lifecycle_configuration(Bucket=bucketName, LifecycleConfiguration=lifeCycleConfig)
        return True
    except Exception as e:
        logger.warn("Error in set_bucket_lifecycle: " + str(e))
        return False

        


def lambda_handler(event, context):
    
    #get all the buckets in instance
    buckets = list_buckets()
    
    #See how many buckets were found
    number_of_buckets = sum(1 for _ in buckets)
    print("Found " + str(number_of_buckets) + " S3 Buckets." )
    
    if number_of_buckets > 0:
        for bucket in buckets: 
            
            versioningStatus = check_bucket_versioning(bucket.name)
            print(bucket.name + " Versioning: " + versioningStatus)
            print(bucket.name + " Lifecycle: " + check_bucket_lifecycle(bucket.name))
            
            #fetch the tags on the bucket
            bucketTags = get_bucket_tagging(bucket.name)
            
            #if there are tags we need to check them, if not we don't do anything on the bucket.
            #but will trigger a warning to the logs
            if bucketTags != "None":
                
                #Figure out if the bucket was created by a stack.  We want to make sure
                #we can build out our environment programmatically.  If a bucket was not
                #created by a stack then we can't automatically rebuild it.
                if determine_bucket_stack_created(bucketTags):
                    print(bucket.name + " created by stack: True")
                else:
                    #we want to create a warning in the logs.  if we are monitoring the logs
                    #and triggering alarms based on warnings we will know that we either need
                    #to add this bucket to a stack or set the S3MonitorIgnore flag
                    logger.warn(bucket.name + " created by stack: False")
                
                #determine if we should skip making any changes to the bucket. 
                #if the S3MonitorIgnore tag is set to True, we don't do anything to the bucket.    
                if determine_skip_bucket(bucketTags):
                    # We are ignoring this bucket.
                    logger.warn(bucket.name + " S3MonitorIgnore: True")       
                else:
                    # This bucket is set to be monitored
                    print(bucket.name + " S3MonitorIgnore: False")
                    print(bucket.name + " will be evaluated against bucket lifecycle policies.")
                    
                    #make sure the versioning is enabled
                    if bucket_enable_versioning(bucket.name):
                        #warn that we changed something
                        logger.warn(bucket.name + " Versioning has been enabled.")
                        
                    if set_bucket_lifecycle(bucket.name):
                        print(bucket.name + " lifecycle has been updated.")
                    
            else:
                logger.warning(bucket.name + " created by stack: False")
                logger.warning(bucket.name + " tags: None")
                logger.warning(bucket.name + " S3MonitorIgnore: Not Configured")
                    
    
        return True
    

#to test locally
lambda_handler("", "")
