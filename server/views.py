# views.py
#
# Copyright (C) 2011-2018 Vas Vasiliadis
# University of Chicago
#
# Application logic for the GAS
#
##
__author__ = 'Vas Vasiliadis <vas@uchicago.edu>'

import uuid
import time
import json
from datetime import datetime

import boto3
from botocore.client import Config
from boto3.dynamodb.conditions import Key

from flask import (abort, flash, redirect, render_template, 
  request, session, url_for)

from gas import app, db
from decorators import authenticated, is_premium
from auth import get_profile, update_profile


"""Start annotation request
Create the required AWS S3 policy document and render a form for
uploading an annotation input file using the policy document
"""
@app.route('/annotate', methods=['GET'])
@authenticated
def annotate():
  # Open a connection to the S3 service
  s3 = boto3.client('s3', 
    region_name=app.config['AWS_REGION_NAME'], 
    config=Config(signature_version='s3v4'))

  bucket_name = app.config['AWS_S3_INPUTS_BUCKET']
  user_id = session['primary_identity']

  # Generate unique ID to be used as S3 key (name)
  key_name = app.config['AWS_S3_KEY_PREFIX'] + user_id + '/' + str(uuid.uuid4()) + '~${filename}'

  # Redirect to a route that will call the annotator
  redirect_url = str(request.url) + "/job"

  # Define policy conditions
  # NOTE: We also must inlcude "x-amz-security-token" since we're
  # using temporary credentials via instance roles
  encryption = app.config['AWS_S3_ENCRYPTION']
  acl = app.config['AWS_S3_ACL']
  expires_in = app.config['AWS_SIGNED_REQUEST_EXPIRATION']
  fields = {
    "success_action_redirect": redirect_url,
    "x-amz-server-side-encryption": encryption,
    "acl": acl
  }
  conditions = [
    ["starts-with", "$success_action_redirect", redirect_url],
    {"x-amz-server-side-encryption": encryption},
    {"acl": acl}
  ]
  
  # check user role, and limit content size 15kb
  role = get_profile(identity_id=user_id)
  if role == 'free_user':
    conditions.append(['content-length', 0, 153600])

  # Generate the presigned POST call
  presigned_post = s3.generate_presigned_post(Bucket=bucket_name, 
    Key=key_name, Fields=fields, Conditions=conditions, ExpiresIn=expires_in)

  # Render the upload form which will parse/submit the presigned POST
  return render_template('annotate.html', s3_post=presigned_post)


"""Fires off an annotation job
Accepts the S3 redirect GET request, parses it to extract 
required info, saves a job item to the database, and then
publishes a notification for the annotator service.
"""

@app.route('/annotate/job', methods=['GET'])
@authenticated
def create_annotation_job_request():
  # Parse redirect URL query parameters for S3 object info
  bucket_name = request.args.get('bucket')
  key_name = request.args.get('key')

  jobid_and_file = key_name.split('/')[-1]
  user_id = key_name.split('/')[1]
  job_id = jobid_and_file.split('~')[0]
  file_name = jobid_and_file.split('~')[-1]

  # Persist job to database
  submit_time = int(time.time())
  # Create a job item and persist it to the annotations database
  data = {"job_id": job_id,
          "user_id": user_id,
          "input_file_name": file_name,
          "s3_inputs_bucket": bucket_name,
          "s3_key_input_file": key_name,
          "submit_time": int(submit_time),
          "job_status": "PENDING"
          }

  dynamodb = boto3.resource('dynamodb', region_name=app.config['AWS_REGION_NAME'])
  ann_table = dynamodb.Table(app.config['AWS_DYNAMODB_ANNOTATIONS_TABLE'])
  ann_table.put_item(Item=data)

  # Send message to request queue
  sns = boto3.client('sns', region_name=app.config['AWS_REGION_NAME'])
  response = sns.publish(TopicArn=app.config['AWS_SNS_JOB_REQUEST_TOPIC'], Message=json.dumps(data))

  #Glacier
  if get_profile(identity_id=user_id).role == 'free_user':
    data = {"job_id": job_id,
            "user_id": user_id,
            "input_file_name": file_name,
            "s3_inputs_bucket": bucket_name,
            "s3_key_input_file": key_name
          }
    sns_glacier = sns.publish(TopicArn=app.config['AWS_SNS_JOB_GLACIER_TOPIC'], Message=json.dumps(data))
    print(f'Glacier works:{sns_glacier}')
  return render_template('annotate_confirm.html', job_id=job_id)


"""List all annotations for the user
"""
@app.route('/annotations', methods=['GET'])
@authenticated
def annotations_list():
  dynamodb = boto3.resource('dynamodb', region_name=app.config['AWS_REGION_NAME'])
  ann_table = dynamodb.Table(app.config['AWS_DYNAMODB_ANNOTATIONS_TABLE'])
  response = ann_table.query(IndexName='user_id-index',KeyConditionExpression=Key('user_id').eq(session['primary_identity']))#,Select='SPECIFIC_ATTRIBUTES', ProjectionExpression='job_id, submit_time, input_file_name, job_status')
  
  for item in response['Items']:
    item['submit_time'] = datetime.fromtimestamp(int(item['submit_time'])).strftime('%Y-%m-%d %H:%M')
  items = response['Items']
  return render_template('annotations.html', annotations=items)



"""Display details of a specific annotation job
"""
@app.route('/annotations/<id>', methods=['GET'])
@authenticated
def annotation_details(id):
  dynamodb = boto3.resource('dynamodb', region_name=app.config['AWS_REGION_NAME'])
  table = dynamodb.Table(app.config['AWS_DYNAMODB_ANNOTATIONS_TABLE'])

  # get the items
  response = table.query(Select='ALL_ATTRIBUTES', KeyConditionExpression=Key('job_id').eq(id))

  response = response['Items'][0]

  if response['user_id'] != session['primary_identity']:
    return forbidden()

  else:
    submit_time = datetime.fromtimestamp(int(response['submit_time'])).strftime('%Y-%m-%d %H:%M')
    response['submit_time'] = submit_time

  result_url = input_url = None

  if 'complete_time' in response:
    # user role
    role = get_profile(identity_id=session['primary_identity']).role

    complete = float(response['complete_time'])
    complete_time = datetime.fromtimestamp(int(response['complete_time'])).strftime('%Y-%m-%d %H:%M')
    response['complete_time'] = complete_time

    # Bucket
    s3 = boto3.client('s3', region_name=app.config['AWS_REGION_NAME'], config=Config(signature_version='s3v4'))
    input_bucket = app.config['AWS_S3_INPUTS_BUCKET']
    result_bucket = app.config['AWS_S3_RESULTS_BUCKET']
    user_id = session['primary_identity']
    key_name = app.config['AWS_S3_KEY_PREFIX'] + str(user_id) + '/' + str(id)

    # input_url
    input_file_key = key_name + '~' + response['input_file_name']
    input_url = s3.generate_presigned_url(ClientMethod='get_object', Params={'Bucket': input_bucket,'Key': input_file_key}, 
                                        ExpiresIn=60000)
    # download conditions
    if (time.time() - complete >= 1800 and role == 'free_user'):
      result_url = 'upgrade'
    else:
      result_file_key = key_name + '~' + response['input_file_name'].replace('.', '.annot.')
      result_url = s3.generate_presigned_url(
        ClientMethod='get_object',
        Params={'Bucket': result_bucket,'Key': result_file_key},
        ExpiresIn=60000)


  return render_template('job_details.html',response=response, input_url=input_url, result_url=result_url)



"""Display the log file for an annotation job
"""
@app.route('/annotations/<id>/log', methods=['GET'])
@authenticated
def annotation_log(id):
  # Get Table
  dynamodb = boto3.resource('dynamodb', region_name=app.config['AWS_REGION_NAME'])
  ann_table = dynamodb.Table(app.config['AWS_DYNAMODB_ANNOTATIONS_TABLE'])
  response = ann_table.query(Select='ALL_ATTRIBUTES',KeyConditionExpression=Key('job_id').eq(id))

  # Get file name
  file_name = response['Items'][0]['input_file_name'] + '.count.log'

  # Read the object from s3
  s3 = boto3.client('s3', region_name=app.config['AWS_REGION_NAME'], config=Config(signature_version='s3v4'))

  result_bucket = app.config['AWS_S3_RESULTS_BUCKET']

  KEY = app.config['AWS_S3_KEY_PREFIX'] + session['primary_identity'] + '/' + str(id) + '~' + file_name
  obj = s3.get_object(Bucket=result_bucket , Key=KEY)

  return render_template('files_log.html', log=obj)


"""Subscription management handler
"""
import stripe

@app.route('/subscribe', methods=['GET', 'POST'])
@authenticated
def subscribe():
  # Extract user id
  user_id = session['primary_identity']

  # Mehtod GET
  if request.method == 'GET':
    role = get_profile(identity_id=user_id).role
    if role == 'free_user':
      return render_template('subscribe.html', success=True)
    else:
      return render_template('subscribe.html', success=False)

  # Method POST
  else:
    stripe.api_key = app.config['STRIPE_SECRET_KEY']
    stripe_token = request.form.get('stripe_token')
    username = get_profile(identity_id=user_id).name
    stripe_response = stripe.Customer.create(
      email=get_profile(identity_id=user_id).email,
      source=stripe_token,
      description= username
      )

    update_profile(identity_id=user_id, role='premium_user')


    dynamodb = boto3.resource('dynamodb', region_name=app.config['AWS_REGION_NAME'])
    ann_table = dynamodb.Table(app.config['AWS_DYNAMODB_ANNOTATIONS_TABLE'])
    response = ann_table.query(IndexName='user_id-index',KeyConditionExpression=Key('user_id').eq(session['primary_identity']))#,Select='SPECIFIC_ATTRIBUTES', ProjectionExpression='job_id, submit_time, input_file_name, job_status')

    items = response['Items']

    # Access Glacier
    glacier = boto3.client('glacier', region_name=app.config['AWS_REGION_NAME'])

    for item in items:
      if 'results_file_archiveId' in item:
        archiveId = item['results_file_archiveId']
        init_response = glacier.initiate_job(
          accountId='-',
          jobParameters={
          'SNSTopic': app.config['AWS_SNS_JOB_RETRIEVAL_TOPIC'],
          'Tier': 'Expedited',
          'Type': 'archive-retrieval',
          'ArchiveId': archiveId
          },
          vaultName=app.config['AWS_GLACIER_VAULT'])
        print(f'Initial Job: {init_response}')
      elif 'complete_time' in item:
        if time.time() - float(item['complete_time']) <= 180:
          sns = boto3.client('sns', region_name=app.config['AWS_REGION_NAME'])
          message = json.dumps({'cancel': item['job_id']})
          response = sns.publish(TopicArn=app.config['AWS_SNS_JOB_GLACIER_TOPIC'], Message=message)

    return render_template('subscribe_confirm.html', stripe_id=stripe_response['id'])

@app.route('/cancel', methods=['GET'])
@authenticated
def cancel_premium():
  role = get_profile(identity_id=session['primary_identity']).role
  if role == 'premium_user':
    update_profile(identity_id=session['primary_identity'], role="free_user")
  return render_template('cancel.html')



"""DO NOT CHANGE CODE BELOW THIS LINE
*******************************************************************************
"""

"""Home page
"""
@app.route('/', methods=['GET'])
def home():
  return render_template('home.html')

"""Login page; send user to Globus Auth
"""
@app.route('/login', methods=['GET'])
def login():
  app.logger.info('Login attempted from IP {0}'.format(request.remote_addr))
  # If user requested a specific page, save it to session for redirect after authentication
  if (request.args.get('next')):
    session['next'] = request.args.get('next')
  return redirect(url_for('authcallback'))

"""404 error handler
"""
@app.errorhandler(404)
def page_not_found(e):
  return render_template('error.html', 
    title='Page not found', alert_level='warning',
    message="The page you tried to reach does not exist. Please check the URL and try again."), 404

"""403 error handler
"""
@app.errorhandler(403)
def forbidden(e):
  return render_template('error.html',
    title='Not authorized', alert_level='danger',
    message="You are not authorized to access this page. If you think you deserve to be granted access, please contact the supreme leader of the mutating genome revolutionary party."), 403

"""405 error handler
"""
@app.errorhandler(405)
def not_allowed(e):
  return render_template('error.html',
    title='Not allowed', alert_level='warning',
    message="You attempted an operation that's not allowed; get your act together, hacker!"), 405

"""500 error handler
"""
@app.errorhandler(500)
def internal_error(error):
  return render_template('error.html',
    title='Server error', alert_level='danger',
    message="The server encountered an error and could not process your request."), 500

### EOF