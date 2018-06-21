# Capstone

(`server` file is the `gas` file)

### Name
Ruizhe(Rex) Zhou

### Server

https://rzhou12.ucmpcs.org/


### Coment & Introduction

#### Problem 7 Description

I accomplished this task corresponding to SQS. The queue will listen to the job_result SNS topic. When
a job is completed, the notification message will be sent to the queue. A `results_archive` script keeping polling the queue
will run in the `util` instance. 

Steps:

	1. If the user is a premium user, it will delete the message

	2. If the user role is free user, it will query the DynamoDB to check the completed time of the job

		a. If the job is completed within 30 min, do nothing

		b. If the job has been completed for more than 30 min, archive the result file to glacier vault

I chose this method since it is easy to implement, and it doesn't waste resources to scan the
DynamoDB.

#### Problem 9 Description

I initiate glacier archive retrieval job corresponding to these jobs with a certain
SNS topic called rzhou12_job_retrieval, and created a SQS queue to listen to this topic. Once a
job is successfully initiated, a message will be sent to the queue. A python script keeping polling the queue runs on the `util` instance. It  When it receives a message, restore the data to S3, and delete the message.

#### Problem 13 Description

Screen shots on testing process

Having 200 users on locust

<img src="https://github.com/mpcs-cc/cp-trexwithoutt/blob/master/screenshots/0.png" width="600">

the initial number of instances in auto scaling group is 2

<img src="https://github.com/mpcs-cc/cp-trexwithoutt/blob/master/screenshots/1.png" width="600">

and it later changed to be 5 in 10 mins

<img src="https://github.com/mpcs-cc/cp-trexwithoutt/blob/master/screenshots/2.png" width="600">

observe shrank in cloudwatch

<img src="https://github.com/mpcs-cc/cp-trexwithoutt/blob/master/screenshots/3.png" width="600">

finished in 300 users on locust.

<img src="https://github.com/mpcs-cc/cp-trexwithoutt/blob/master/screenshots/4.png" width="600">

Activity observed on the instance

<img src="https://github.com/mpcs-cc/cp-trexwithoutt/blob/master/screenshots/5.png" width="600">

<img src="https://github.com/mpcs-cc/cp-trexwithoutt/blob/master/screenshots/6.png" width="600">

#### Prob 14 Description

The auto job request script has been created, and it will send job every 5 sec.

It's very hard to observe instance increase even though job completes successfully fast and right. (solved, I set `average` for scale-out alarm)

The number of instances increased.

<img src="https://github.com/mpcs-cc/cp-trexwithoutt/blob/master/screenshots/7.png" width="600">

Activity observation scale out

<img src="https://github.com/mpcs-cc/cp-trexwithoutt/blob/master/screenshots/8.png" width="600">

After killing the job sending 

<img src="https://github.com/mpcs-cc/cp-trexwithoutt/blob/master/screenshots/9.png" width="600">

Activity observation scale in

<img src="https://github.com/mpcs-cc/cp-trexwithoutt/blob/master/screenshots/10.png" width="600">

#### Issues

**(Has been solved)** I noticed an issue that might effect the project, that i modified user data file which may influence the autoscaling group processing. There no much of time to recover it after I reminded this issue might occur. (I know how to make it surely complete, but there no much of time.....) 

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

