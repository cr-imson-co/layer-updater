#!/usr/bin/env python
'''
#
# cr.imson.co
#
# Lambda shared functions module
#
# @author Damian Bushong <katana@odios.us>
#
'''

# pylint: disable=C0301,C0330,W0511,R0902,R0913

import json
import logging
import os
import sys

import boto3
from botocore.client import Config

from crimsoncore.lambda_config import LambdaConfig

class LambdaCore:
    '''
    CrimsonCore shared functions.
    '''

    def __init__(self, name, env=None):
        self.script_name = name

        self.config = LambdaConfig(name=self.script_name, env=os.environ if env is None else env)

        # ensure the log directory exists.
        # while we log to /tmp/logs/ in AWS lambda,
        #   other envs such as testbeds may not be as reliable.
        os.makedirs(self.config.get_log_path(), exist_ok=True)

        self._log_handler = None
        self._log_formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
        self._log_stream_handler = logging.StreamHandler(sys.stdout)
        self._log_stream_handler.setFormatter(self._log_formatter)
        self._log_stream_handler.setLevel(self.config.get_log_level())

        self.logger = logging.getLogger(self.script_name)
        self.logger.addHandler(self._log_stream_handler)
        self.change_logfile('bootstrap.log')
        self.logger.setLevel(self.config.get_log_level())

        self.ec2 = None
        self.awslambda = None # had to use awslambda because .lambda is a syntax error
        self.s3 = None # pylint: disable=C0103
        self.sns = None
        self.ssm = None

    def init_ec2(self):
        '''
        Initialize Amazon EC2 API.
        '''

        endpoint_url = None
        aws_region = self.config.get_aws_region()

        if self.config.get_fips_mode():
            self.logger.info('Enabling FIPS compliance mode for AWS EC2')

            endpoint_url = f'https://ec2.{aws_region}.amazonaws.com'

        self.ec2 = boto3.resource(
            'ec2',
            region_name=aws_region,
            endpoint_url=endpoint_url
        )

        self.logger.info('AWS EC2 API initialized')

    def init_ssm(self):
        '''
        Initialize Amazon SSM API.
        '''

        endpoint_url = None
        aws_region = self.config.get_aws_region()

        if self.config.get_fips_mode():
            self.logger.info('Enabling FIPS compliance mode for AWS SSM')

            endpoint_url = f'https://ssm.{aws_region}.amazonaws.com'

        self.ssm = boto3.client(
            'ssm',
            region_name=aws_region,
            endpoint_url=endpoint_url
        )

        self.logger.info('AWS SSM API initialized')

    def init_s3(self):
        '''
        Initialize Amazon S3 API.
        '''

        endpoint_url = None

        if self.config.get_fips_mode():
            self.logger.info('Enabling FIPS compliance mode for AWS S3')

            endpoint_url = f'https://s3-fips.{self.config.get_aws_region()}.amazonaws.com'

        self.s3 = boto3.client( # pylint: disable=C0103
            's3',
            config=Config(signature_version='s3v4'),
            endpoint_url=endpoint_url
        )

        self.logger.info('AWS S3 API initialized')

    def init_sns(self):
        '''
        Initialize Amazon SNS API.
        '''

        endpoint_url = None
        aws_region = self.config.get_aws_region()

        if self.config.get_fips_mode():
            self.logger.info('Enabling FIPS compliance mode for AWS SNS')

            endpoint_url = f'https://sns.{aws_region}.amazonaws.com'

        self.sns = boto3.client(
            'sns',
            region_name=aws_region,
            endpoint_url=endpoint_url
        )

        self.logger.info('AWS SNS API initialized')

    def init_lambda(self):
        '''
        Initialize Amazon Lambda API.
        '''

        endpoint_url = None
        aws_region = self.config.get_aws_region()

        if self.config.get_fips_mode():
            self.logger.info('Enabling FIPS compliance mode for AWS Lambda API')

            endpoint_url = f'https://lambda-fips.{aws_region}.amazonaws.com'

        self.awslambda = boto3.client(
            'lambda',
            region_name=aws_region,
            endpoint_url=endpoint_url
        )

        self.logger.info('AWS Lambda API initialized')

    def get_ssm_parameter(self, name, encrypted=False, include_global_prefix=True, include_application_name=True, include_environment=False, include_stack_name=False, legacy_name=False):
        '''
        Get an AWS Systems Manager system parameter.
        Encryption supported.
        '''

        if legacy_name:
            parameter_name = self.config.build_legacy_ssm_param_name(
                name,
                include_global_prefix=include_global_prefix,
                include_application_name=include_application_name,
                include_environment=include_environment,
                include_stack_name=include_stack_name
            )
        else:
            parameter_name = self.config.build_ssm_param_name(
                name,
                include_global_prefix=include_global_prefix,
                include_application_name=include_application_name,
                include_environment=include_environment,
                include_stack_name=include_stack_name
            )

        ssm_parameter = self.ssm.get_parameter(
            Name=parameter_name,
            WithDecryption=encrypted
        )
        return ssm_parameter['Parameter']['Value']

    def get_ssm_parameters_by_path(self, subpath=None, encrypted=False, include_global_prefix=True, include_application_name=True, include_environment=False, include_stack_name=False):
        '''
        Get multiple AWS Systems Manager system parameters under a specific path.
        Encryption supported.
        '''

        ssm_parameters = self.ssm.get_parameter(
            Name=self.config.build_ssm_param_name(
                subpath,
                include_global_prefix=include_global_prefix,
                include_application_name=include_application_name,
                include_environment=include_environment,
                include_stack_name=include_stack_name
            ),
            WithDecryption=encrypted
        )

        bare_params = {}
        for parameter in ssm_parameters['Parameters']:
            bare_params.update([(parameter['Name'], parameter['Value'])])

        return bare_params

    def change_logfile(self, filename):
        '''
        Switch what file we're logging to.
        '''

        if self._log_handler is not None:
            self._log_handler.close()
            self.logger.removeHandler(self._log_handler)

        self._log_handler = logging.FileHandler(f'{self.config.get_log_path()}/{filename}')
        self._log_handler.setFormatter(self._log_formatter)
        self._log_handler.setLevel(self.config.get_log_level())
        self.logger.addHandler(self._log_handler)

    def archive_log_file(self, filepath, data):
        '''
        Archive a log file to S3.
        '''

        if self.config.get_log_archive_mode() == 's3':
            self.logger.info('Archiving log file to S3 bucket path: %s', filepath)

            self.s3.put_object(
                Bucket=self.config.get_log_bucket_name(),
                Key=filepath,
                Body=data.encode('utf-8'),
                ServerSideEncryption='aws:kms',
                SSEKMSKeyId=self.config.get_log_kms_key_id()
            )
        elif self.config.get_log_archive_mode() == 'stdout':
            pass

    def send_notification(self, notification_type, message):
        '''
        Send an SNS notification to the notification Lambda for chain-dispatch
          to whatever notification service it's configured for.
        '''

        self.sns.publish(
            TargetArn=self.config.get_notification_arn(),
            Message=json.dumps({'default':
                json.dumps({
                    'type': notification_type,
                    'lambda': self.script_name,
                    'message': message
                })
            }),
            MessageStructure='json'
        )
