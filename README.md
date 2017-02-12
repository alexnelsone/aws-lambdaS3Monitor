#lambdaS3Monitor

## Synopsis

lambdaS3Monitor is a function that should be scheduled to run periodically to automate the monitoring of S3 buckets.  If an S3 bucket has tag with the Key of S3MonitorIgnore set to False, this function will
set Versioning to True and configure a lifecycle policy.  If there is no tag or the tag is set to True then the function will ignore the bucket.

The function also creates a WARNING entry in the logs if the bucket was not created by a Cloudformation Stack.  This is to ensure automation of environments.  If you are automating environment builds and
 you a have a manually created bucket that is deemed critical, it will not be automatically you might want to add it to a stack.

## Libraries
No additional libraries other than boto3.


## Returns

The function returns True on proper execution. Otherwise, it returns False.  

## Function List

1. is_empty(any_structure) 
2. list_buckets():
3. check_bucket_lifecycle(bucketName)
4. check_bucket_versioning(bucketName)
5. bucket_enable_versioning(bucketName)
6. get_bucket_tagging(bucketName)
7. determine_bucket_stack_created(tags)
8. determine_skip_bucket(tags)
9. set_bucket_lifecycle(bucketName)


## AWS Role

The lambda role policy for this function is:

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
    

## Motivation

Automation of environment/infrastructure

