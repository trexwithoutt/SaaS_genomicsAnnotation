# Copyright (C) 2011-2018 Vas Vasiliadis
# University of Chicago
__author__ = 'Vas Vasiliadis <vas@uchicago.edu>'

import sys
import time
import driver
import boto3
import os
import json

# A rudimentary timer for coarse-grained profiling
class Timer(object):
    def __init__(self, verbose=False):
        self.verbose = verbose

    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, *args):
        self.end = time.time()
        self.secs = self.end - self.start
        self.msecs = self.secs * 1000  # millisecs
        if self.verbose:
            print("Total runtime: {0:.6f} seconds".format(self.secs))

if __name__ == '__main__':
    # Call the AnnTools pipeline
    if len(sys.argv) > 3:
        input_path = sys.argv[1]
        s3_key = sys.argv[2]
        job_id = sys.argv[3]
        print(input_path)
        print(s3_key)
        print(job_id)
        with Timer() as t:
            driver.run(input_path, 'vcf')
        print("Total runtime: %s seconds" % t.secs)

        result_file_path = (input_path+'.annot').replace('.vcf.annot', '.annot.vcf')
        result_key = (s3_key+'.annot').replace('.vcf.annot', '.annot.vcf')

        log_file_path = input_path+'.count.log'
        log_key = s3_key+'.count.log'

        s3 = boto3.resource('s3', region_name='us-east-1')
        # Upload the results file
        try:
            s3.meta.client.upload_file(result_file_path, 'gas-results', result_key)
            print("result file uploaded")
        except Exception as e:
            print(e.__doc__)
            raise

        # Upload the log file
        try:
            s3.meta.client.upload_file(log_file_path, 'gas-results', log_key)
            print("log file uploaded")
        except Exception as e:
            print(e.__doc__)
            raise

        # Update database
        complete_time = int(time.time())
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        ann_table = dynamodb.Table('rzhou12_annotations')
        try:
            update = {'s3_key_result_file': {
                                          'Value': result_key,
                                          'Action': 'PUT'
                                      },
                     's3_key_log_file': {
                                          'Value': log_key,
                                          'Action': 'PUT'
                                      },
                     'complete_time': {
                                          'Value': complete_time,
                                          'Action': 'PUT'
                                      },
                     'job_status': {
                                          'Value': 'COMPLETED',
                                          'Action': 'PUT'
                                      },
                     's3_results_bucket': {
                                          'Value': 'gas-results',
                                          'Action': 'PUT'
                                      }
                                  }
            expected = {'job_status': {'Value': 'RUNNING','ComparisonOperator': 'EQ'}}
            ann_table.update_item(Key={'job_id': job_id},
                                  AttributeUpdates=update,
                                  Expected=expected)
        except Exception as e:
            print(e.__doc__)
            raise

        # publish a notification to SNS
        sns = boto3.client('sns', region_name='us-east-1')
        temp = ann_table.get_item(Key = {'job_id':job_id})['Item']
        temp['submit_time'], temp['complete_time'] = int(temp['submit_time']), int(temp['complete_time'])
        message = json.dumps(temp)
        #message = json.dumps({"job_id": job_id})
        response = sns.publish(TopicArn="arn:aws:sns:us-east-1:127134666975:rzhou12_job_results", Message=message)
        print('sns has been sent')

        # Clean up (delete) local job files
        
        dir_path = os.path.dirname(input_path)
        os.remove(input_path)
        os.remove(result_file_path)
        os.remove(log_file_path)
        os.rmdir(dir_path)
        print("files removed")

    else:
        print("A valid .vcf file must be provided as input to this program.")
