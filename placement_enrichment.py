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
import multiprocessing as mp

from flask import Response, jsonify, Flask, make_response
from glom import glom
from googleapiclient.discovery import build

import runtimeconfig

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

# Youtube client in global scope to be re-used
youtubeClient = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=YOUTUBE_AUTH_KEY)

def enrich_channels(request):

    result = []
    for channelId in request:
        channelResponse = __get_channel_info(youtubeClient, channelId)
        result.append(__map_youtube_channel_response(channelResponse, channelId))

    return jsonify(result)

def __map_youtube_channel_response(youtubeResponse, channelId):
    response = {"channelId": channelId}
    if 'items' in youtubeResponse and len(youtubeResponse['items']) > 0:
        detailResponse = youtubeResponse['items'][0]
        response.update({
            "name": __extract(detailResponse, "snippet.title"),
            "description": __extract(detailResponse, "snippet.description"),
            "language": __extract(detailResponse, "snippet.defaultLanguage"),
            "country": __extract(detailResponse, 'snippet.country'),
            "thumbnail": __extract(detailResponse, 'snippet.thumbnails.default.url'),
            "views": __cast_to_integer(__extract(detailResponse, 'statistics.viewCount')),
            "videoCount": __cast_to_integer(__extract(detailResponse, 'statistics.videoCount')),
            "subscribers": __cast_to_integer(__extract(detailResponse, 'statistics.subscriberCount')),
            "mfk": __extract(detailResponse, 'status.madeForKids'),
            "url": f"https://www.youtube.com/channel/{__extract(detailResponse, 'id')}",
        })
    return __clean_nones(response)

def __cast_to_integer(string_value):
    if string_value is None:
        return string_value
    elif type(string_value) == str and string_value != "":
        return int(string_value)


def __extract(dict, path):
    return glom(dict, path, default=None)

# Call the API's channels.list method to retrieve an existing channel localization.
# If the localized text is not available in the requested language,
# this method will return text in the default language.
def __get_channel_info(youtube, channel_id):

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

def __clean_nones(value):
    """
    Recursively remove all None values from dictionaries and lists, and returns
    the result as a new dictionary or list.
    """
    if isinstance(value, list):
        return [__clean_nones(x) for x in value if x is not None]
    elif isinstance(value, dict):
        return {
            key: __clean_nones(val)
            for key, val in value.items()
            if val is not None
        }
    else:
        return value
