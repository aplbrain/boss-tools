#!/usr/bin/env python3

# Copyright 2016 The Johns Hopkins University Applied Physics Laboratory
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import boto3
import os
import sys

from bossutils.deploy_lambdas import S3_BUCKET
from bossutils.deploy_lambdas import create_session

def delete_func(args):
    """Delete the lambda function and all of its versions.
    """
    session = create_session(args.aws_credentials)
    client = session.client('lambda')
    resp = client.delete_function(FunctionName=args.name)
    print(resp)

def setup_parser():
    parser = argparse.ArgumentParser(
        description='Script for deleting lambda functions.  To supply arguments from a file, provide the filename prepended with an `@`.',
        fromfile_prefix_chars = '@')
    parser.add_argument(
        '--aws-credentials', '-a',
        metavar = '<file>',
        default = os.environ.get('AWS_CREDENTIALS'),
        type = argparse.FileType('r'),
        help = 'File with credentials for connecting to AWS (default: AWS_CREDENTIALS)')
    parser.add_argument(
        'name',
        help = 'Name of function.')

    return parser


if __name__ == '__main__':
    parser = setup_parser()
    args = parser.parse_args()

    if args.aws_credentials is None:
        parser.print_usage()
        print("Error: AWS credentials not provided and AWS_CREDENTIALS is not defined.")
        sys.exit(1)

    delete_func(args)
