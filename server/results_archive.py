import os
from gas import db, app
import botocore.client as bc
import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key
from botocore.client import Config
import json
import time

def main():
    sqs = boto3.resource('sqs', region_name=app.config['AWS_REGION_NAME'])
    # Create the queue. This returns an SQS.Queue instance
    queue = sqs.get_queue_by_name(QueueName='rzhou12_job_glacier')
    cancel_jobs = []
    while True:
        print("Asking SQS for 1 message...")
        try:
            messages = queue.receive_messages(WaitTimeSeconds=10)

            if messages:
                message = messages[0]
                data = eval(eval(message.body)['Message'])

                #parse parameters
                job_id    = data['job_id']
                username  = data['user_id']
                # KEY = data['s3_key_input_file'].split('/')[-1].replace('.vcf', '.annot.vcf')

                # refrence to hamad
                if 'cancel' in data:
                    cancel_jobs.append(data['cancel'])
                    message.delete()
                    print('Delete the message')
                    continue
                # upgrade to premium
                if job_id in cancel_jobs:
                    cancel_jobs.remove(job_id)
                    message.delete()
                    print('Cancel moving job to Glacier')
                    continue

                print(job_id)
                dynamodb = boto3.resource('dynamodb', region_name=app.config['AWS_REGION_NAME'])
                table = dynamodb.Table(app.config['AWS_DYNAMODB_ANNOTATIONS_TABLE'])
                responses = table.query(Select='ALL_ATTRIBUTES', KeyConditionExpression=Key('job_id').eq(job_id))

                print(responses)
                response = responses['Items'][0]
                KEY = response['s3_key_result_file']

                s3_resource = boto3.resource('s3', region_name=app.config['AWS_REGION_NAME'])
                bucket = s3_resource.Bucket(app.config['AWS_S3_RESULTS_BUCKET'])

                s3 = boto3.client('s3', region_name=app.config['AWS_REGION_NAME'],config=Config(signature_version='s3v4'))

                if 'complete_time' in response:
                    avaliable_time = time.time() - float(response['complete_time'])
                    if avaliable_time >= 1800:
                        print('Avaliable time over 30 mins')
                        obj = bucket.Object(KEY)
                        result_text = obj.get()['Body'].read()
                        print(f'Object: {obj}')
                        glacier =  boto3.client('glacier', region_name=app.config['AWS_REGION_NAME'])

                        glacier_response = glacier.upload_archive(vaultName=app.config['AWS_GLACIER_VAULT'],
                        archiveDescription='result file for ' + job_id,
                        body=result_text)

                        glacier_id = glacier_response['archiveId']
                        glacier_loc = glacier_response['location']
                        glacier_cksum = glacier_response['checksum']

                        del_response = s3.delete_object(Bucket=app.config['AWS_S3_RESULTS_BUCKET'], Key=KEY)

                        try:
                            update = {'results_file_archive_id': {'Value': glacier_id, 'Action': 'PUT'}}
                            table.update_item(Key={'job_id': job_id}, AttributeUpdates=update)
                        except ClientError as e:
                            error_info = f'Error happened when connecting the database: {e.__doc__}'
                            print(error_info)

                        # delete the SQS message
                        message.delete()
                        print('Delete the handled message')
                    else:
                        continue

        except Exception as e:
            raise e


if __name__ == '__main__':
    main()




