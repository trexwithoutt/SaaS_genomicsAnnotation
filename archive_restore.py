import json
import boto3
import time
from botocore.client import Config
from boto3.dynamodb.conditions import Key
import os
from gas import db, app

def main():
    # Get the service resource
    sqs = boto3.resource('sqs', region_name=app.config['AWS_REGION_NAME'])
    # Get the queue. This returns an SQS.Queue instance
    queue = sqs.get_queue_by_name(QueueName='rzhou12_job_retrieval')

    while True:
        print("Asking SQS for 1 message...")
        messages = queue.receive_messages(MaxNumberOfMessages=1, WaitTimeSeconds=10)

        if messages:
            message = messages[0]
            data = eval(eval(message.body)['Message'])

            jobId = data['JobId']

            # get glacier data
            glacier_client = boto3.client('glacier', region_name=app.config['AWS_REGION_NAME'])
            retrieval_response = glacier_clent.get_job_output(valueName=app.config['AWS_GLACIER_VAULE'], jobId=jobId)

            # get data from streamingbody
            file_path = './' + data['ArchiveId']
            with open(file_path, 'w') as f:
                for chunk in iter(lambda: retrieval_response['body'].read(4096), b''):
                    f.write(chunk)
            print('Have File')

            # get upload description
            description = json.loads(retrieval_response['archiveDescription'])

            #find the job information from dynamodb
            dynamodb = boto3.resource('dynamodb', region_name=app.config['AWS_REGION_NAME'])
            table = dynamodb.Table(app.config['AWS_DYNAMODB_ANNOTATIONS_TABLE'])
            try:
                # update remove
                table.update_item(
                    Key={'job_id': description['job_id']},
                    AttributeUpdates={
                        'results_file_archive_id': {'Action': 'REMOVE'}
                    })
            except ClientError as e:
                        error_info = f'Error happened when connecting the database: {e.__doc__}'
                        print(error_info)

            # upload s3
            s3 = boto3.client('s3', region_name=app.config['AWS_REGION_NAME'], config=Config(signature_version='s3v4'))
            response = s3.put_object(
                Key=description['s3_key'],
                Body=retrieval_response['body'].read(),
                Bucket=app.config['AWS_S3_RESULTS_BUCKET']
                )

            # delete message
            message.delete()
            print('Message has been deleted')


if __name__ == '__main__':
    main()
