#!/usr/bin/env python
# Copyright 2017 The Johns Hopkins University Applied Physics Laboratory
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
This file holds the functions need to perform deletes for Collections, Experiment, Channel and Coordinate Frame
These may be run in Lambdas or Activities in Setup Functions.
"""

import boto3
import bossutils
import bossutils.aws
import pprint
from boto3.dynamodb.conditions import Key as awsKey
import hashlib

TEST_TABLE = 'hiderrt1-test1'

"""
DeleteError will be used if an Exception occurs within any of the delete functions.
"""
class DeleteError(Exception):
    pass


def delete_metedata(input, session=None):
    """
    Deletes all metadata from DynamoDB table
    Args:
        input(Dict): Dictionary containing following keys: lookup_key, meta-db
        session(Session): AWS boto3 Session

    Returns:

    """
    #if "meta-db" not in input:
    lookup_key = input["lookup_key"]
    meta_db = input["meta-db"]
    session = bossutils.aws.get_session()
    client = session.client('dynamodb')
    query_params = {'TableName': meta_db,
                    'KeyConditionExpression':'lookup_key = :lookup_key_value',
                    'ExpressionAttributeValues': {":lookup_key_value": {"S": lookup_key}},
                    'ExpressionAttributeNames': {"#bosskey": "key"},
                    'ProjectionExpression': "lookup_key, #bosskey",
                    'ConsistentRead': True,
                    'Limit': 1000}
    query_resp = client.query(**query_params)
    if query_resp["ResponseMetadata"]["HTTPStatusCode"] != 200:
        raise DeleteError(query_resp)
    count = 0
    while query_resp['Count'] > 0:
        for meta in query_resp["Items"]:
            exclusive_start_key=meta
            count += 1
            print("deleting: {}".format(meta))
            del_resp = client.delete_item(
                TableName='bossmeta.hiderrt1.boss',
                Key=meta,
                ReturnValues='NONE',
                ReturnConsumedCapacity='NONE')
            if del_resp["ResponseMetadata"]["HTTPStatusCode"] != 200:
                pprint.pprint(del_resp)
        # Keep querying to make sure we have them all.
        query_params['ExclusiveStartKey'] = exclusive_start_key
        query_resp = client.query(**query_params)
        if query_resp["ResponseMetadata"]["HTTPStatusCode"] != 200:
            raise DeleteError(query_resp)
    print("deleted {} items".format(count))


def get_channel_key(lookup_key):
    base_key = '{}'.format(lookup_key)
    hash_str = hashlib.md5(base_key.encode()).hexdigest()
    return '{}&{}'.format(hash_str, base_key)


def delete_id_count(input, session=None):
    """
    Deletes id count for lookup key.
    Args:
        input(Dict): Dictionary containing following keys: lookup_key, id-count-table
        session(Session): AWS boto3 Session

    Returns:

    """
    id_count_table = input["id-count-table"]
    lookup_key = input["lookup_key"]
    channel_key = get_channel_key(lookup_key)

    session = bossutils.aws.get_session()
    client = session.client('dynamodb')
    query_params = {'TableName': id_count_table,
                    'KeyConditionExpression': '#channel_key = :channel_key_value',
                    'ExpressionAttributeValues': {":channel_key_value": {"S": channel_key}},
                    'ExpressionAttributeNames': {"#channel_key": "channel-key", "#version": "version"},
                    'ProjectionExpression': "#channel_key, #version",
                    'ConsistentRead': True,
                    'Limit': 1000}
    query_resp = client.query(**query_params)
    if query_resp["ResponseMetadata"]["HTTPStatusCode"] != 200:
        raise DeleteError(query_resp)

    count = 0
    while query_resp['Count'] > 0:
        for id in query_resp["Items"]:
            exclusive_start_key=id
            count += 1
            print("deleting: {}".format(id))
            del_resp = client.delete_item(
                TableName=id_count_table,
                Key=id,
                ReturnValues='NONE',
                ReturnConsumedCapacity='NONE')
            if del_resp["ResponseMetadata"]["HTTPStatusCode"] != 200:
                del_resp["deleting"] = id
                raise DeleteError(del_resp)
        # Keep querying to make sure we have them all.
        query_params['ExclusiveStartKey'] = exclusive_start_key
        query_resp = client.query(**query_params)
        if query_resp["ResponseMetadata"]["HTTPStatusCode"] != 200:
            del_resp["deleting"] = id
            raise DeleteError(query_resp)
    print("deleted {} items".format(count))


def delete_id_index(input, session=None):
    """
    Deletes id index data for lookup key.
    Args:
        input(Dict): Dictionary containing following keys: lookup_key, id-index-table
        session(Session): AWS boto3 Session

    Returns:

    """
    id_count_table = input["id-index-table"]
    lookup_key = input["lookup_key"]
    channel_key = get_channel_key(lookup_key)

    session = bossutils.aws.get_session()
    client = session.client('dynamodb')
    query_params = {'TableName': id_count_table,
                    'KeyConditionExpression': '#channel_key = :channel_key_value',
                    'ExpressionAttributeValues': {":channel_key_value": {"S": channel_key}},
                    'ExpressionAttributeNames': {"#channel_key": "channel-key", "#version": "version"},
                    'ProjectionExpression': "#channel_key, #version",
                    'ConsistentRead': True,
                    'Limit': 1000}
    query_resp = client.query(**query_params)
    if query_resp["ResponseMetadata"]["HTTPStatusCode"] != 200:
        raise DeleteError(query_resp)

    count = 0
    while query_resp['Count'] > 0:
        for id in query_resp["Items"]:
            exclusive_start_key=id
            count += 1
            print("deleting: {}".format(id))
            del_resp = client.delete_item(
                TableName=id_count_table,
                Key=id,
                ReturnValues='NONE',
                ReturnConsumedCapacity='NONE')
            if del_resp["ResponseMetadata"]["HTTPStatusCode"] != 200:
                del_resp["deleting"] = id
                raise DeleteError(del_resp)
        # Keep querying to make sure we have them all.
        query_params['ExclusiveStartKey'] = exclusive_start_key
        query_resp = client.query(**query_params)
        if query_resp["ResponseMetadata"]["HTTPStatusCode"] != 200:
            del_resp["deleting"] = id
            raise DeleteError(query_resp)
    print("deleted {} items".format(count))





if __name__ == "__main__":
    session = bossutils.aws.get_session()
    input = {
        #"lookup_key": "36&25&53",  # was lookup key being used by intTest
        "lookup_key": "23",  # lookup key being used by metadata
        "meta-db": "bossmeta.hiderrt1.boss",
        "s3-index-table": "s3index.hiderrt1.boss",
        "id-index-table": "idIndex.hiderrt1.boss",
        "id-count-table": "idCount.hiderrt1.boss",
        #"id-count-table": "intTest.idCount.hiderrt1.boss"  # had data for idCount
    }
    delete_metedata(input)
    #delete_id_count(input)