# Genomic Annotation Service

## Introduction

Make use of various clouds services running on Amazon Web Services.

## Key Functions

- **Log in** (via Globus Auth)

	Some aspects of the service are avaliable only to registered users. Two classes of users will be supported: *Free* and *Premium*. 
	Premium users will have access to additional functionality, beyond that avaliable to Free users

- **Convert from a Free to a Premium user**

	Premium users will be required to provide a credit card for payment of the service subscription. The GAS will integrate with Stripe (www.stripe.com) for credit card payment processing. No real credit cards are required for the project. 

- **Submit an annotation job**
	
	Free users may only submit jobs of up to a certain size. Premium users may submit any size job. If a Free user submits an oversized job, the system will refuse it and will prompt to the user to convert to a Premium user.

- **Receive notifications when annotation jobs finish**

	When their annotation request is complete, the GAS will send users an email that includes a link where they can view/download the result/log files

- 


### Refrences

http://boto3.readthedocs.io/en/latest/reference/services/glacier.html#Glacier.Client.initiate_job

https://docs.aws.amazon.com/zh_cn/elasticloadbalancing/latest/userguide/what-is-load-balancing.html

https://aws.amazon.com/about-aws/whats-new/2014/12/08/delete-all-messages-in-an-amazon-sqs-queue/

https://docs.aws.amazon.com/zh_cn/autoscaling/ec2/userguide/what-is-amazon-ec2-auto-scaling.html

http://boto3.readthedocs.io/en/latest/reference/services/ses.html#ses

https://stackoverflow.com/questions/19379120/how-to-read-a-config-file-using-python

https://stackoverflow.com/questions/34570226/how-to-use-botocore-response-streamingbody-as-stdin-pipe

https://stackoverflow.com/questions/29378763/how-to-save-s3-object-to-a-file-using-boto3

http://boto3.readthedocs.io/en/latest/reference/services/s3.html#S3.Client.upload_file

https://stackoverflow.com/questions/19379120/how-to-read-a-config-file-using-python

https://www.tutorialspoint.com/python/python_database_access.html

https://stripe.com/docs/api#intro

https://stripe.com/docs/api#create_customer

http://boto3.readthedocs.io/en/latest/reference/services/glacier.html#Glacier.Client.initiate_job

https://stackoverflow.com/questions/33639642/avoiding-insufficient-data-in-cloudwatch

https://stackoverflow.com/questions/46635895/aws-boto3-s3-python-an-error-occurred-404-when-calling-the-headobject-operat

https://docs.aws.amazon.com/zh_cn/AmazonCloudWatch/latest/monitoring/WhatIsCloudWatch.html

https://stackoverflow.com/questions/510348/how-can-i-make-a-time-delay-in-python

