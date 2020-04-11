#!/usr/bin/env python
'''
#
# cr.imson.co
#
# Lambda configuration module
#
# @author Damian Bushong <katana@odios.us>
#
'''

# pylint: disable=C0301,W0511,R0902,R0913

import logging
import re

class LambdaConfig:
    ''' Lambda shared configuration '''

    def __init__(self, name, env, overrides=None, lambda_overrides=None):
        self._script_name = name

        self._defaults = {
            'APPLICATION_NAME': '',
            'DEBUG_MODE': 'off',
            'ENVIRONMENT': '',
            'GLOBAL_PREFIX': '',
            'LOG_PATH': '../logs/',
            'LOG_ARCHIVE_MODE': 'stdout',
            'SAFE_MODE': 'off',
            'STACK_NAME': ''
        }

        self._overrides = overrides if overrides is not None else {}

        self._lambda_overrides = lambda_overrides if lambda_overrides is not None else {}

        self._validations = {
            'DEBUG_MODE': ('on', 'off', 'true', 'false', 'yes', 'no'),
            'ENABLE_NOTIFICATIONS': ('on', 'off', 'true', 'false', 'yes', 'no'),
            'FIPS_MODE': ('on', 'off', 'true', 'false', 'yes', 'no'),
            'LOG_ARCHIVE_MODE': ('s3', 'stdout'),
            'SAFE_MODE': ('on', 'off', 'true', 'false', 'yes', 'no')
        }

        self._env = env

        # initialization values
        self.application_name = None

        self.debug_mode = None
        self.log_level = None
        self.log_path = None

        self.safe_mode = None
        self.fips_mode = None
        self.log_archive_mode = None

        self.aws_region = None
        self.log_bucket = None
        self.log_kms_key_id = None

        self.global_prefix = None
        self.environment = None
        self.stack_name = None

        self.notification_arn = None

    def _get_val(self, name, default_override=None):
        '''
        Get a particular configuration value.
        '''
        if self._script_name in self._lambda_overrides:
            overrides = self._lambda_overrides.get(self._script_name)
            if name in overrides:
                return overrides.get(name)

        if name in self._overrides:
            return self._overrides.get(name)

        if name in self._env:
            return self._env.get(name)

        if name in self._defaults:
            return self._defaults.get(name)

        if default_override is not None:
            return default_override

        raise ValueError(f'Configuration value for "{name}" was not specified')

    def _validate_val(self, name, value):
        '''
        Validate a particular value.
        '''

        if name in self._validations:
            validations = self._validations.get(name)
            if value not in validations:
                raise ValueError(f'Unknown {name} value specified; expected values [{str(validations)[1:-1]}]')

    def val(self, name, to_lower=False, bool_coerce=False, default_override=None):
        '''
        Get a particular configuration value (and validate it if necessary).
        '''
        value = self._get_val(name, default_override)

        if to_lower or bool_coerce:
            value = value.lower()

        if name in self._validations:
            self._validate_val(name, value)

        if bool_coerce:
            value = bool(value in ('on', 'true', 'yes'))

        return value

    def get_application_name(self):
        '''
        Get the application's name.
        '''
        if self.application_name is None:
            self.application_name = self.val('APPLICATION_NAME', to_lower=True)

        return self.application_name

    def get_debug_mode(self):
        '''
        Check to see if debug mode is enabled.
        '''
        if self.debug_mode is None:
            self.debug_mode = self.val('DEBUG_MODE', bool_coerce=True)

        return self.debug_mode

    def get_log_level(self):
        '''
        Get what log level we should be using.
        '''

        if self.log_level is None:
            self.log_level = logging.DEBUG if self.get_debug_mode() else logging.INFO

        return self.log_level

    def get_log_path(self):
        '''
        Get the log path we should be writing logs to (even if temporarily, in Lambda).
        '''

        if self.log_path is None:
            self.log_path = self.val('LOG_PATH')

        return self.log_path

    def get_safe_mode(self):
        '''
        Check to see if safe mode is enabled.
        Useful for configuring things to execute in a "dry run" state.
        Great for use as a conditional for disabling destructive actions with.
        '''

        if self.safe_mode is None:
            self.safe_mode = self.val('SAFE_MODE', bool_coerce=True)

        return self.safe_mode

    def get_aws_region(self):
        '''
        Get the AWS region we're running in.
        '''
        if self.aws_region is None:
            self.aws_region = self.val('AWS_REGION', to_lower=True)

        return self.aws_region

    def get_fips_mode(self):
        '''
        Check to see if FIPS mode should be enabled.
        FIPS compliance requires that we only leverage AWS FIPS-compliant endpoints.
        '''

        if self.fips_mode is None:
            # it's fine if FIPS_MODE was not defined externally.
            # we'll just automatically identify if we're in FIPS mode on our own.

            aws_region = self.get_aws_region()
            in_gov_cloud = isinstance(aws_region, str) and re.search('^us-gov-(?:west|east)-[\\d]+$', aws_region)
            # but wait - what about using FIPS mode for AWS Canada?
            #
            # ...eh.  ¯\_(ツ)_/¯

            self.fips_mode = self.val('FIPS_MODE', bool_coerce=True, default_override=('on' if in_gov_cloud else 'off'))

        return self.fips_mode

    def get_global_prefix(self):
        '''
        Get the global prefix for Lambda configuration.
        Used for things like S3 bucket names, SSM parameter names.
        '''

        if self.global_prefix is None:
            self.global_prefix = self.val('GLOBAL_PREFIX', to_lower=True)

        return self.global_prefix

    def get_environment(self):
        '''
        Get the environment type.
        Used for things like discerning between multiple environments in the same account (e.g. dev, test, prod...)
        '''

        if self.environment is None:
            self.environment = self.val('ENVIRONMENT', to_lower=True)

        return self.environment

    def get_stack_name(self):
        '''
        Get the stack name for the Lambda configuration.
        Used for things like multiple server stacks in a single AWS account - affects SSM parameter names.
        '''

        if self.stack_name is None:
            self.stack_name = self.val('STACK_NAME', to_lower=True)

        return self.stack_name

    def get_log_archive_mode(self):
        '''
        Get the log archive mode.
        '''

        if self.log_archive_mode is None:
            self.log_archive_mode = self.val('LOG_ARCHIVE_MODE', to_lower=True)

        return self.log_archive_mode

    def get_log_kms_key_id(self):
        '''
        Get the AWS KMS Encryption Key ID to use when uploading logs to an AWS Bucket.
        '''

        if self.log_kms_key_id is None:
            if self.get_log_archive_mode() != 's3':
                raise ValueError('log_kms_key_id cannot be used when log_archive_mode is not "s3"')

            self.log_kms_key_id = self.val('LOG_KMS_KEY_ID')

        return self.log_kms_key_id

    def get_notification_arn(self):
        '''
        Get the ARN for the SNS notification to be dispatched to.
        '''

        if self.notification_arn is None:
            self.notification_arn = self.val('NOTIFICATION_ARN')

        return self.notification_arn

    def get_log_bucket_name(self):
        '''
        Get the name of the bucket to store critical error logs in.
        '''

        if self.log_bucket is None:
            self.log_bucket = self.val('LOG_BUCKET_NAME', to_lower=True, default_override=self.build_bucket_name('logs'))

        return self.log_bucket

    def build_legacy_ssm_param_name(self, name, include_global_prefix=False, include_application_name=False, include_environment=False, include_stack_name=False):
        '''
        Build the correct name for an SSM parameter.
        Legacy behavior for AWS accounts that are not compliant with AWS SSM Parameter Hierarchy Standards.
        '''

        name_chunks = []
        if include_global_prefix and len(self.get_global_prefix()) > 0:
            name_chunks.append(self.get_global_prefix())

        if include_application_name and len(self.get_application_name()) > 0:
            name_chunks.append(self.get_application_name())

        if include_environment and len(self.get_environment()) > 0:
            name_chunks.append(self.get_environment())

        if include_stack_name and len(self.get_stack_name()) > 0:
            name_chunks.append(self.get_stack_name())

        name_chunks.append('ssm')
        name_chunks.append(name)

        return '-'.join(name_chunks)

    def build_ssm_param_name(self, name=None, include_global_prefix=False, include_application_name=False, include_environment=False, include_stack_name=False):
        '''
        Build the correct name for an SSM parameter.
        (ssm_param_names returned should alwyas contain always leading slash)

        Rough structure for resulting SSM parameter names is as follows (assuming the appropriate include vars are set to True):
        /{prefix}/{appname}/{environment}/{stack_name}/ssm/{parameter_name}

        example:
        { # environment
            'GLOBAL_PREFIX'='codebite',
            'APPLICATION_NAME'='notifications',
            'ENVIRONMENT'='prod',
            'STACK_NAME'='primary',
        }
        { # args
            name='webhook_url',
            include_global_prefix=True,
            include_application_name=True,
            include_environment=True,
            include_stack_name=True
        }

        result:
        /codebite/notifications/prod/primary/ssm/webhook_url
        '''

        name_chunks = ['']
        if include_global_prefix and len(self.get_global_prefix()) > 0:
            name_chunks.append(self.get_global_prefix())

        if include_application_name and len(self.get_application_name()) > 0:
            name_chunks.append(self.get_application_name())

        if include_environment and len(self.get_environment()) > 0:
            name_chunks.append(self.get_environment())

        if include_stack_name and len(self.get_stack_name()) > 0:
            name_chunks.append(self.get_stack_name())

        # note: name is conditional and not included here if None in order to support get_parameters_by_path ssm parameter name structures
        if name is not None:
            name_chunks.append('ssm')
            name_chunks.append(name)
        else:
            name_chunks.append('')

        return '/'.join(name_chunks)

    def build_bucket_name(self, name, include_global_prefix=True, include_application_name=True, include_environment=False):
        '''
        Build the correct name for an S3 bucket.
        '''

        name_chunks = []
        if include_global_prefix and len(self.get_global_prefix()) > 0:
            name_chunks.append(self.get_global_prefix())

        if include_application_name and len(self.get_application_name()) > 0:
            name_chunks.append(self.get_application_name())

        if include_environment and len(self.get_environment()) > 0:
            name_chunks.append(self.get_environment())

        name_chunks.append(name)

        return '-'.join(name_chunks)
