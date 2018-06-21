import os
import uuid
import subprocess
import botocore.client as bc
import boto3
import json
from botocore.exceptions import ClientError

def annotate():
    data = None
    sqs = boto3.resource('sqs', region_name='us-east-1')
    # Create the queue. This returns an SQS.Queue instance
    queue = sqs.get_queue_by_name(QueueName='rzhou12_job_requests')
    # You can now access identifiers and attributes
    while True:
        print("Asking SQS for 1 message...")
        messages = queue.receive_messages(WaitTimeSeconds=20)

        if messages:
            print("1 message got")
            
            # Extract job parameters from the request body (NOT the URL query string!)
            data = eval(eval(messages[0].body)['Message'])
            job_id    = data['job_id']
            username  = data['user_id']
            file_name = data['input_file_name']
            bucket_name = data['s3_inputs_bucket']
            s3_key      = data['s3_key_input_file']

            # create a unique folder according to the job id
            folderpath = '../data/' + str(username) + '/' + str(job_id)
            file_path = folderpath + "/" + str(file_name)
            try:
                os.makedirs(folderpath)
            except OSError as e:
                print(e)

            # download file
            s3 = boto3.resource('s3', region_name='us-east-1')
            try:
                s3.Bucket(bucket_name).download_file(s3_key, file_path)
            except ClientError as e:
                print(e)
                return

            # annotate file
            print(file_path)
            subprocess.Popen(['python', 'run.py', file_path, s3_key, job_id])

            #update database if current status is 'PENDING'
            try:
                dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
                ann_table = dynamodb.Table('rzhou12_annotations')
                update = {'job_status':{'Value':'RUNNING', 'Action':'PUT'}}
                expected = {'job_status':{'Value': 'PENDING', 'ComparisonOperator': 'EQ'}}
                ann_table.update_item(Key={'job_id':job_id},
                                      AttributeUpdates=update,
                                      Expected=expected)
            except ClientError as e:
                error_info = f'Error happened when connecting the database: {e.__doc__}'
                print(error_info)

            # delete message from the queue
            messages[0].delete()
            print('Message Deleted')
        else:
            print('No Response')

if __name__ == '__main__':
    annotate()

