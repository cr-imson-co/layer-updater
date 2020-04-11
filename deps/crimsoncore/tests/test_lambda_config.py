#!/usr/bin/env python

import unittest
from crimsoncore import LambdaConfig

import logging

class LambdaConfigTestCase(unittest.TestCase):
    def test_application_name(self):
        config = LambdaConfig('test', {'APPLICATION_NAME': 'test'})
        self.assertEqual(config.get_application_name(), 'test')

    def test_debug_mode_on(self):
        values = ('on', 'true', 'yes', 'ON')
        for value in values:
            with self.subTest(value=value):
                config = LambdaConfig('test', {'DEBUG_MODE': value})

                self.assertIs(config.get_debug_mode(), True)

    def test_debug_mode_off(self):
        values = ('off', 'false', 'no', 'OFF')
        for value in values:
            with self.subTest(value=value):
                config = LambdaConfig('test', {'DEBUG_MODE': value})

                self.assertIs(config.get_debug_mode(), False)

    def test_bad_debug_mode(self):
        config = LambdaConfig('test', {'DEBUG_MODE': 'nonsense'})

        self.assertRaises(ValueError, config.get_debug_mode)

    def test_log_level_debug(self):
        config = LambdaConfig('test', {'DEBUG_MODE': 'on'})

        self.assertIs(config.get_log_level(), logging.DEBUG)

    def test_log_level_normal(self):
        config = LambdaConfig('test', {'DEBUG_MODE': 'off'})

        self.assertIs(config.get_log_level(), logging.INFO)

    def test_safe_mode_on(self):
        values = ('on', 'true', 'yes', 'ON')
        for value in values:
            with self.subTest(value=value):
                config = LambdaConfig('test', {'SAFE_MODE': value})

                self.assertIs(config.get_safe_mode(), True)

    def test_safe_mode_off(self):
        values = ('off', 'false', 'no', 'OFF')
        for value in values:
            with self.subTest(value=value):
                config = LambdaConfig('test', {'SAFE_MODE': value})

                self.assertIs(config.get_safe_mode(), False)

    def test_bad_safe_mode(self):
        config = LambdaConfig('test', {'SAFE_MODE': 'nonsense'})

        self.assertRaises(ValueError, config.get_safe_mode)

    def test_aws_region(self):
        regions = ('us-east-1', 'US-EAST-1')
        for region in regions:
            with self.subTest(region=region):
                config = LambdaConfig('test', {'AWS_REGION': region})

                self.assertEqual(config.get_aws_region(), region.lower())

    def test_bad_aws_region(self):
        config = LambdaConfig('test', {})

        self.assertRaises(ValueError, config.get_aws_region)

    def test_fips_mode_on(self):
        values = ('on', 'true', 'yes', 'ON')
        for value in values:
            with self.subTest(value=value):
                config = LambdaConfig('test', {
                    'AWS_REGION': 'us-east-1',
                    'FIPS_MODE': value
                })

                self.assertIs(config.get_fips_mode(), True)

    def test_fips_mode_off(self):
        values = ('off', 'false', 'no', 'OFF')
        for value in values:
            with self.subTest(value=value):
                config = LambdaConfig('test', {
                    'AWS_REGION': 'us-east-1',
                    'FIPS_MODE': value
                })

                self.assertIs(config.get_fips_mode(), False)

    def test_fips_mode__bad_run_mode(self):
        config = LambdaConfig('test', {
            'RUN_MODE': 'local',
            'FIPS_MODE': 'on'
        })

        self.assertRaises(ValueError, config.get_fips_mode)

    def test_fips_mode_detect_on(self):
        config = LambdaConfig('test', {'AWS_REGION': 'us-gov-west-1'})

        self.assertIs(config.get_fips_mode(), True)

    def test_fips_mode_detect_off(self):
        config = LambdaConfig('test', {'AWS_REGION': 'us-east-1'})

        self.assertIs(config.get_fips_mode(), False)

    def test_global_prefix(self):
        values = ('prefix', 'PREFIX')
        for value in values:
            with self.subTest(value=value):
                config = LambdaConfig('test', {'GLOBAL_PREFIX': value})

                self.assertEqual(config.get_global_prefix(), value.lower())

    def test_no_global_prefix(self):
        config = LambdaConfig('test', {})

        self.assertEqual(config.get_global_prefix(), '')

    def test_environment(self):
        values = ('dev', 'DEV')
        for value in values:
            with self.subTest(value=value):
                config = LambdaConfig('test', {'ENVIRONMENT': value})

                self.assertEqual(config.get_environment(), value.lower())

    def test_stack_name(self):
        values = ('stack-a', 'STACK-A')
        for value in values:
            with self.subTest(value=value):
                config = LambdaConfig('test', {'STACK_NAME': value})

                self.assertEqual(config.get_stack_name(), value.lower())

    def test_no_stack_name(self):
        config = LambdaConfig('test', {})

        self.assertEqual(config.get_stack_name(), '')

    def test_log_archive_mode(self):
        values = ('s3', 'stdout', 'STDOUT')
        for value in values:
            with self.subTest(value=value):
                config = LambdaConfig('test', {'LOG_ARCHIVE_MODE': value})

                self.assertEqual(config.get_log_archive_mode(), value.lower())

    def test_bad_log_archive_mode(self):
        config = LambdaConfig('test', {'LOG_ARCHIVE_MODE': 'nonsense'})

        self.assertRaises(ValueError, config.get_log_archive_mode)

    def test_log_kms_key_id(self):
        config = LambdaConfig('test', {
            'RUN_MODE': 'aws',
            'LOG_ARCHIVE_MODE': 's3',
            'LOG_KMS_KEY_ID': 'testvalue'
        })

        self.assertEqual(config.get_log_kms_key_id(), 'testvalue')

    def test_log_kms_key_id__bad_run_mode(self):
        config = LambdaConfig('test', {
            'RUN_MODE': 'local',
            'LOG_ARCHIVE_MODE': 'local',
            'LOG_KMS_KEY_ID': 'testvalue'
        })

        self.assertRaises(ValueError, config.get_log_kms_key_id)

    def test_log_kms_key_id__bad_log_mode(self):
        config = LambdaConfig('test', {
            'RUN_MODE': 'aws',
            'LOG_ARCHIVE_MODE': 'local',
            'LOG_KMS_KEY_ID': 'testvalue'
        })

        self.assertRaises(ValueError, config.get_log_kms_key_id)

    def test_build_bucket_name(self):
        tests = [
            {
                'global_prefix': True,
                'application_name': True,
                'environment': True,
                'name': 'testbucket1',
                'expected': 'test-myappname-dev-testbucket1'
            },
            {
                'global_prefix': False,
                'application_name': True,
                'environment': True,
                'name': 'testbucket2',
                'expected': 'myappname-dev-testbucket2'
            },
            {
                'global_prefix': True,
                'application_name': False,
                'environment': True,
                'name': 'testbucket2',
                'expected': 'test-dev-testbucket2'
            },
            {
                'global_prefix': True,
                'application_name': True,
                'environment': False,
                'name': 'testbucket3',
                'expected': 'test-myappname-testbucket3'
            },
            {
                'global_prefix': True,
                'application_name': False,
                'environment': False,
                'name': 'testbucket4',
                'expected': 'test-testbucket4'
            },
            {
                'global_prefix': False,
                'application_name': True,
                'environment': False,
                'name': 'testbucket4',
                'expected': 'myappname-testbucket4'
            },
            {
                'global_prefix': False,
                'application_name': False,
                'environment': True,
                'name': 'testbucket4',
                'expected': 'dev-testbucket4'
            },
            {
                'global_prefix': False,
                'application_name': False,
                'name': 'testbucket4',
                'expected': 'testbucket4'
            },
        ]
        for test in tests:
            with self.subTest(expected=test.get('expected')):
                config = LambdaConfig('test', {
                    'GLOBAL_PREFIX': 'test',
                    'APPLICATION_NAME': 'myappname',
                    'ENVIRONMENT': 'dev',
                })

                self.assertEqual(
                    config.build_bucket_name(
                        test.get('name'),
                        include_global_prefix=test.get('global_prefix'),
                        include_application_name=test.get('application_name'),
                        include_environment=test.get('environment')
                    ),
                    test.get('expected')
                )

    def test_build_legacy_ssm_param(self):
        tests = [
            {
                'global_prefix': True,
                'application_name': True,
                'stack_name': True,
                'name': 'param1',
                'expected': 'test-myappname-stack-a-ssm-param1'
            },
            {
                'global_prefix': False,
                'application_name': True,
                'stack_name': True,
                'name': 'param2',
                'expected': 'myappname-stack-a-ssm-param2'
            },
            {
                'global_prefix': True,
                'application_name': False,
                'stack_name': True,
                'name': 'param3',
                'expected': 'test-stack-a-ssm-param3'
            },
            {
                'global_prefix': True,
                'application_name': True,
                'stack_name': False,
                'name': 'param4',
                'expected': 'test-myappname-ssm-param4'
            },
            {
                'global_prefix': True,
                'application_name': False,
                'stack_name': False,
                'name': 'param5',
                'expected': 'test-ssm-param5'
            },
            {
                'global_prefix': False,
                'application_name': True,
                'stack_name': False,
                'name': 'param6',
                'expected': 'myappname-ssm-param6'
            },
            {
                'global_prefix': False,
                'application_name': False,
                'stack_name': True,
                'name': 'param7',
                'expected': 'stack-a-ssm-param7'
            },
            {
                'global_prefix': False,
                'application_name': False,
                'stack_name': False,
                'name': 'param8',
                'expected': 'ssm-param8'
            },
        ]
        for test in tests:
            with self.subTest(expected=test.get('expected')):
                config = LambdaConfig('test', {
                    'GLOBAL_PREFIX': 'test',
                    'APPLICATION_NAME': 'myappname',
                    'STACK_NAME': 'stack-a'
                })

                self.assertEqual(
                    config.build_legacy_ssm_param_name(
                        test.get('name'),
                        include_global_prefix=test.get('global_prefix'),
                        include_application_name=test.get('application_name'),
                        include_stack_name=test.get('stack_name')
                    ),
                    test.get('expected')
                )

    def test_build_ssm_param(self):
        tests = [
            # all true
            {
                'global_prefix': True,
                'application_name': True,
                'environment': True,
                'stack_name': True,
                'name': 'param1',
                'expected': '/test/myappname/dev/stack-a/ssm/param1'
            },
            # 1 false at a time
            {
                'global_prefix': False,
                'application_name': True,
                'environment': True,
                'stack_name': True,
                'name': 'param2',
                'expected': '/myappname/dev/stack-a/ssm/param2'
            },
            {
                'global_prefix': True,
                'application_name': False,
                'environment': True,
                'stack_name': True,
                'name': 'param3',
                'expected': '/test/dev/stack-a/ssm/param3'
            },
            {
                'global_prefix': True,
                'application_name': True,
                'environment': False,
                'stack_name': True,
                'name': 'param3',
                'expected': '/test/myappname/stack-a/ssm/param3'
            },
            {
                'global_prefix': True,
                'application_name': True,
                'environment': True,
                'stack_name': False,
                'name': 'param4',
                'expected': '/test/myappname/dev/ssm/param4'
            },
            # 2 false at a time
            {
                'global_prefix': True,
                'application_name': True,
                'environment': False,
                'stack_name': False,
                'name': 'param5',
                'expected': '/test/myappname/ssm/param5'
            },
            {
                'global_prefix': True,
                'application_name': False,
                'environment': True,
                'stack_name': False,
                'name': 'param5',
                'expected': '/test/dev/ssm/param5'
            },
            {
                'global_prefix': True,
                'application_name': False,
                'environment': False,
                'stack_name': True,
                'name': 'param5',
                'expected': '/test/stack-a/ssm/param5'
            },
            {
                'global_prefix': False,
                'application_name': True,
                'environment': True,
                'stack_name': False,
                'name': 'param6',
                'expected': '/myappname/dev/ssm/param6'
            },
            {
                'global_prefix': False,
                'application_name': True,
                'environment': False,
                'stack_name': True,
                'name': 'param6',
                'expected': '/myappname/stack-a/ssm/param6'
            },
            {
                'global_prefix': False,
                'application_name': False,
                'environment': True,
                'stack_name': True,
                'name': 'param7',
                'expected': '/dev/stack-a/ssm/param7'
            },
            # 3 false at a time
            {
                'global_prefix': True,
                'application_name': False,
                'environment': False,
                'stack_name': False,
                'name': 'param8',
                'expected': '/test/ssm/param8'
            },
            {
                'global_prefix': False,
                'application_name': True,
                'environment': False,
                'stack_name': False,
                'name': 'param8',
                'expected': '/myappname/ssm/param8'
            },
            {
                'global_prefix': False,
                'application_name': False,
                'environment': True,
                'stack_name': False,
                'name': 'param8',
                'expected': '/dev/ssm/param8'
            },
            {
                'global_prefix': False,
                'application_name': False,
                'environment': False,
                'stack_name': True,
                'name': 'param8',
                'expected': '/stack-a/ssm/param8'
            },
            # all false
            {
                'global_prefix': False,
                'application_name': False,
                'environment': False,
                'stack_name': False,
                'name': 'param8',
                'expected': '/ssm/param8'
            },
            # no name specified (for get_parameters_by_path)
            {
                'global_prefix': True,
                'application_name': True,
                'environment': True,
                'stack_name': True,
                'name': None,
                'expected': '/test/myappname/dev/stack-a/'
            },
        ]
        for test in tests:
            with self.subTest(expected=test.get('expected')):
                config = LambdaConfig('test', {
                    'GLOBAL_PREFIX': 'test',
                    'APPLICATION_NAME': 'myappname',
                    'ENVIRONMENT': 'dev',
                    'STACK_NAME': 'stack-a'
                })

                self.assertEqual(
                    config.build_ssm_param_name(
                        test.get('name'),
                        include_global_prefix=test.get('global_prefix'),
                        include_application_name=test.get('application_name'),
                        include_environment=test.get('environment'),
                        include_stack_name=test.get('stack_name')
                    ),
                    test.get('expected')
                )

    def test_log_bucket_name(self):
        values = ('mybucketname', 'MYBUCKETNAME')
        for value in values:
            with self.subTest(value=value):
                config = LambdaConfig('test', {'LOG_BUCKET_NAME': value})

                self.assertEqual(config.get_log_bucket_name(), value.lower())


    def test_log_bucket_name_default(self):
        config = LambdaConfig('test', {
            'GLOBAL_PREFIX': 'log',
            'APPLICATION_NAME': 'test'
        })

        self.assertEqual(config.get_log_bucket_name(), 'log-test-logs')

    def test_notification_arn(self):
        values = ('mynotificationarn', 'MYNOTIFICATIONARN')
        for value in values:
            with self.subTest(value=value):
                config = LambdaConfig('test', {'NOTIFICATION_ARN': value})

                self.assertEqual(config.get_notification_arn(), value)

if __name__ == '__main__':
    unittest.main()
