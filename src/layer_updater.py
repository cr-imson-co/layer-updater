#!/usr/bin/env python
'''
#
# cr.imson.co
#
# Lambda layer automated updater
#
# @author Damian Bushong <katana@odios.us>
#
'''

# pylint: disable=C0116,C0301,C0411,W0511,W1202,R0912,R0914,R0915

import time

from crimsoncore import LambdaCore

from aws_xray_sdk.core import patch_all
patch_all()

LAMBDA_NAME = 'layer_updater'
LAMBDA = LambdaCore(LAMBDA_NAME)
LAMBDA.init_s3()
LAMBDA.init_sns()
LAMBDA.init_lambda()

def parse_lambda_layer_arn(arn):
    _, _, _, region, account_id, _, layer_name, layer_version = arn.split(':') # pylint: disable=W0612

    return {
        'region': region,
        'account_id': account_id,
        'layer': layer_name,
        'version': int(layer_version)
    }

def get_layer_version_from_arn(arn):
    return parse_lambda_layer_arn(arn).get('version')

def lambda_handler(event, context):
    start_time = str(int(time.time() * 1000))
    log_name = f'{LAMBDA_NAME}_{start_time}.log'
    LAMBDA.change_logfile(log_name)

    try:
        layer_name = event.get('layer_name', False)
        if not layer_name:
            raise ValueError('A layer name to update must be specified')

        runtime = event.get('runtime', False)
        if not runtime:
            raise ValueError('A target runtime must be specified')

        lambda_names = event.get('lambda_names', None)

        LAMBDA.logger.info(f'Retargeting Lambdas to use the latest version of the layer "{layer_name}" ({runtime})')
        if lambda_names is not None:
            LAMBDA.logger.info(f'Focusing on the lambdas {",".join(lambda_names)}')

        # get the lambdas to work with
        lambda_functions = []
        if lambda_names is None:
            paginator = LAMBDA.awslambda.get_paginator('list_functions')
            iterator = paginator.paginate()
            for ret in iterator:
                lambda_functions += [lambda_function for lambda_function in ret.get('Functions') if lambda_function.get('Runtime') == runtime]
        else:
            for lambda_name in lambda_names:
                ret = LAMBDA.awslambda.get_function(FunctionName=lambda_name)
                if ret.get('Runtime') == runtime:
                    lambda_functions.append(ret.get('Configuration'))

        LAMBDA.logger.info(f'Pulled back details on {len(lambda_functions)} lambdas')

        # identify which of the lambdas we've found actually use the layer we're updating
        target_functions = []
        for lambda_function in lambda_functions:
            layers = [parse_lambda_layer_arn(layer.get('Arn')).get('layer') for layer in lambda_function.get('Layers')]

            if any(layer_name == layer for layer in layers):
                target_functions.append(lambda_function)

        LAMBDA.logger.info(f'Filtered down to {len(target_functions)} actually using the specified lambda layer')

        # identify the latest version of the layer we're updating...
        layer_versions = []
        paginator = LAMBDA.awslambda.get_paginator('list_layer_versions')
        iterator = paginator.paginate(
            CompatibleRuntime=runtime,
            LayerName=layer_name
        )
        for ret in iterator:
            layer_versions += [layer_version.get('LayerVersionArn') for layer_version in ret.get('LayerVersions')]

        best_layer_version = max(layer_versions, key=get_layer_version_from_arn)

        LAMBDA.logger.info(f'Best version of the layer identified as v{parse_lambda_layer_arn(best_layer_version).get("version")}')

        for target_function in target_functions:
            # validate that they are not on the latest available version for this runtime...
            if not any(best_layer_version == layer for layer in target_function.get('Layers')):
                # build the new list of layers (PRESERVING ORDER!)
                new_layers = []
                for layer in [layer.get('Arn') for layer in target_function.get('Layers')]:
                    new_layers.append(best_layer_version if parse_lambda_layer_arn(layer).get('layer') == layer_name else layer)

                LAMBDA.logger.info(f'Updating layer configuration for {target_function.get("FunctionName")} to [{",".join(new_layers)}]')

                LAMBDA.awslambda.update_function_configuration(
                    FunctionName=target_function.get('FunctionArn'),
                    Layers=new_layers
                )

        LAMBDA.logger.info('Run completed')
    except Exception:
        LAMBDA.logger.error('Fatal error during script runtime', exc_info=True)

        # do our best to fire off the emergency flare
        error_log_dest = f'logs/{LAMBDA_NAME}/{log_name}'
        with open(f'{LAMBDA.config.get_log_path()}/{log_name}', 'r') as file:
            LAMBDA.archive_log_file(error_log_dest, file.read())

        LAMBDA.send_notification('error', f'λ! - {LAMBDA_NAME} lambda error notification - error logs are available at {error_log_dest}')

        raise
    finally:
        LAMBDA.change_logfile(f'{LAMBDA_NAME}_interim.log')
