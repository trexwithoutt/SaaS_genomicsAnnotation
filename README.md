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

- **Browse jobs and download annotation results**

	The GAS will store annotation results for later retrieval. Users may view a list of their jobs. Freeusers may download results up to 30 min after their job has completed; thereafter their results will be archived and only available to them if they convert to a Premium user. Premium users will always have all their data available for download.

## System Components

The GAS will comprise the following components:
	
	- An object store for input files, annotated files, and job log files

	- A key-value store for persisting information on annotation jobs

	- A low cost, highly-durable object store for archiving the data of Free users

	- A relational database for user account information

	- A service that runs AnnTools for annotation

	- A web application for users to interact with the GAS

	- A set of message queues and notification tioics for managing various system activities

The diagram below shows the various GAS components and interactions:

<img src="https://github.com/trexwithoutt/SaaS_genomicsAnnotation/blob/master/config.png">


## GAS Scalability

We anticipate that the GAS will be in very high demand (since it’s a brilliant system developed by brilliant students), and that demand will be variable over the course of any given time period. Hence, the GAS will use elastic compute infrastructure to minimize cost during periods of low demand and to meet expected user service levels during peak demand periods. We will build elasticity into two areas of the GAS:

## Refrences

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

