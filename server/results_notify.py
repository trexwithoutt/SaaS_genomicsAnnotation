import os
import uuid
from gas import db, app
import subprocess
import botocore.client as bc
import boto3
from botocore.exceptions import ClientError
import utils

def annotate():
    sqs = boto3.resource('sqs', region_name=app.config['AWS_REGION_NAME'])
    # Create the queue. This returns an SQS.Queue instance
    queue = sqs.get_queue_by_name(QueueName=app.config['AWS_RESULTS_NAME'])

    while True:
        print("Asking SQS for 1 message...")
        messages = queue.receive_messages(WaitTimeSeconds=20)

        if len(messages) > 0:
            print("1 message got")
            message = messages[0]
            data = None
            gas_url = "https://rzhou12.ucmpcs.org:4433"

            # Extract job parameters from the request body (NOT the URL query string!)
            data      = eval(eval(message.body)['Message'])
            job_id    = data['job_id']
            username  = data['user_id']
            email     = ['rzhou12@uchicago.edu']

            #send a email
            sender = app.config['MAIL_DEFAULT_SENDER']
            recipients = email
            subject = f'Job {job_id} Completed'
            job_url = gas_url + "/annotations/" + job_id
            body = "Hi user %s, \
            \n \
            \n Your Job <%s> has been completed! \n \
            \n \
            The GAS Team" % (username, job_url)

            send_email = utils.send_email_ses(recipients, sender, subject, body)

            # Delete the message from the queue, if job was successfully submitted
            message.delete()
            print('Message deleted')
        else:
            print("No response")

if __name__ == '__main__':
    annotate()

