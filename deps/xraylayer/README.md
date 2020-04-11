# AWS X-Ray - Lambda Layer builder

Just a small layer builder for an AWS Lambda Layer for AWS X-Ray SDK.

## license

This project (the packaging of the layer) is licensed under the MIT License.

Please note that the actual content within the layer may use a different license.

## generating an updated requirements file

With docker running, run the command: `docker run --rm python:3.8 /bin/bash -c "pip install aws-xray-sdk >/dev/null && pip freeze"`
