import uuid
import time
import simplejson as json
from datetime import datetime

import boto3
from botocore.client import Config
from boto3.dynamodb.conditions import Key

from flask import (abort, flash, redirect, render_template, 
  request, session, url_for)


def main():
    result = {}
    count = 0
    while True: 
        count += 1
        print(f'---{count}---')
        # Get bucket name, key, and job ID from the S3 redirect URL
        bucket_name = 'mpcs-students'
        # s3_key = request.args['key']
        # print(s3_key)

        job_id = str(uuid.uuid1())
        user_id = 'test'
        file_name = 'test.vcf'
        s3_key = 'rzhou12/test.vcf'

        # submit_time
        submit_time = int(time.time())

        # Create a job item and persist it to the annotations database
        data = { "job_id":            job_id,
                 "user_id":           user_id,
                 "input_file_name":   file_name,
                 "s3_inputs_bucket":  bucket_name,
                 "s3_key_input_file": s3_key,
                 "submit_time":       submit_time,
                 "job_status":        "PENDING"
                 }

        try:
            dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
            ann_table = dynamodb.Table('rzhou12_annotations')
            ann_table.put_item(Item=data)
        except Exception as e:
            app.make_response(('bad', 500))
            result = {}
            result['code'] = 500
            result['error'] = f'Create Item Error in Database: \n {e.__doc__}'
            return jsonify(result)

        try:
          sns = boto3.client('sns', region_name='us-east-1')
          arn = "arn:aws:sns:us-east-1:127134666975:rzhou12_job_requests"
          message = json.dumps(data)
          sns_response = sns.publish(TopicArn=arn, Message=message)
          print(f'publish sns: {sns_response}')
        except ClientError as e:
          print(e)
          
        time.sleep(10)

if __name__ == '__main__':
    main()

