# Copyright 2019 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import os
import sys
import traceback
from os import getenv

from flask import Response, jsonify, Flask, make_response
from glom import glom
from googleapiclient.discovery import build

import runtimeconfig

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# load runtime config into environment variables
# TODO: do they really need to be in environment variables
# config must have: INSTANCE_CONNECTION_NAME ,MYSQL_USER ,MYSQL_PASSWORD ,MYSQL_DATABASE
runtimeconfig.fetch_and_update_environ(os.getenv('GCP_PROJECT'), os.getenv('CONFIG_NAME'))

# Setup YouTube API
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'
YOUTUBE_AUTH_KEY = getenv('YOUTUBE_AUTH_KEY', 'The Youtube Auth Key')

logger = logging.getLogger(os.getenv('FUNCTION_NAME'))
logger.setLevel(logging.DEBUG)


def entrypoint(request):
    try:
        if request.method == 'OPTIONS':
            return __configure_cors(request)
        elif request.method == 'POST':
            logger.debug(" POST request: {}".format(repr(request)))
            response = __configure_cors(
                request,
                lambda request: post_enrich_channels(request.get_json())
            )
        else:
            raise NotImplementedError("Method {} not supported".format(request.method))

        return response
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        logger.error(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
        # return error status
        return Response('{"message":"error"}', status=500, mimetype='application/json')


def post_enrich_channels(request):
    # get channel list
    # batch_name = request_context.get('batchName')
    # batch_source_type = request_context.get('sourceType')
    youtubeClient = get_authenticated_youtube_service()

    result = []
    for channelId in request:
        channelResponse = get_channel_info(youtubeClient, channelId)
        result.append(map_youtube_channel_response(channelResponse, channelId))

    return jsonify(result)


def map_youtube_channel_response(youtubeResponse, channelId):
    response = {"channelId": channelId}
    if youtubeResponse['items'] and len(youtubeResponse['items']) > 0:
        detailResponse = youtubeResponse['items'][0]
        response.update({
            "title": extract(detailResponse, "snippet.title"),
            "description": extract(detailResponse, "snippet.description"),
            "language": extract(detailResponse, "snippet.defaultLanguage"),
            "country": extract(detailResponse, 'snippet.country'),
            "thumbnail": extract(detailResponse, 'snippet.thumbnails.default.url'),
            "views": extract(detailResponse, 'statistics.viewCount'),
            "videoCount": extract(detailResponse, 'statistics.videoCount'),
            "subscribers": extract(detailResponse, 'statistics.subscriberCount'),
            "madeForKids": extract(detailResponse, 'status.madeForKids'),
        })
    return clean_nones(response)


def extract(dict, path):
    return glom(dict, path, default=None)

# Call the API's channels.list method to retrieve an existing channel localization.
# If the localized text is not available in the requested language,
# this method will return text in the default language.
def get_channel_info(youtube, channel_id):
    results = youtube.channels().list(
        part='snippet,'
             'contentDetails,'
             'status,'
             'statistics,'
             'brandingSettings,'
             'topicDetails,'
             'localizations',
        id=channel_id,
        hl=None
    ).execute()

    return results

def clean_nones(value):
    """
    Recursively remove all None values from dictionaries and lists, and returns
    the result as a new dictionary or list.
    """
    if isinstance(value, list):
        return [clean_nones(x) for x in value if x is not None]
    elif isinstance(value, dict):
        return {
            key: clean_nones(val)
            for key, val in value.items()
            if val is not None
        }
    else:
        return value


# Authorize the request and store authorization credentials.
def get_authenticated_youtube_service():
    return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=YOUTUBE_AUTH_KEY)


def __configure_cors(request, controller=(lambda _: "")):
    # For more information about CORS and CORS preflight requests, see
    # https://developer.mozilla.org/en-US/docs/Glossary/Preflight_request
    # for more information.

    # Set CORS headers for the preflight request
    if request.method == 'OPTIONS':
        # Allows GET requests from any origin with the Content-Type
        # header and caches preflight response for an 3600s
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': '*',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600'
        }

        return ('', 204, headers)

    # Set CORS headers for the main request
    headers = {
        'Access-Control-Allow-Origin': '*'
    }

    return (controller(request), 200, headers)
