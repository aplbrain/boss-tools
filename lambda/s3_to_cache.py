#!/usr/bin/env python3.4
# Page in cuboid from S3 to the cache.
#
# Expects these keys from the events dictionary:
# {
#   'kv_config': {...},
#   'state_config': {...},
#   'object_store_config': {...},
#   'object_key': '...',
#   'page_in_channel': '...'
# }

print("in s3_to_cache lambda")
import json
import sys
from spdb.spatialdb import SpatialDB

# Parse input args passed as a JSON string from the lambda loader
json_event = sys.argv[1]
event = json.loads(json_event)

# Setup SPDB instance
sp = SpatialDB(event['kv_config'],
               event['state_config'],
               event['object_store_config'])

object_key = event['object_key']
page_in_channel = event['page_in_channel']

exist_keys, missing_keys = sp.objectio.cuboids_exist([object_key])
if exist_keys:
    cube_bytes = sp.objectio.get_single_object(exist_keys[0])
    sp.kvio.put_cubes(exist_keys[0], [cube_bytes])
    sp.cache_state.notify_page_in_complete(page_in_channel, object_key)
else:
    print('Key: {} does not exist!'.format(object_key))
