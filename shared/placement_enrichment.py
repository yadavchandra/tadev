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
from os import getenv

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


def enrich_channel(channelId):
    """
    Enriches a single youtube channels provided as a string. Returns a dict with the enriched data.
    """
    channelResponse = __get_channel_info(youtubeClient, channelId)
    return __map_youtube_channel_response(channelResponse, channelId)


def enrich_channels(channelIdList):
    """
    Enriches multiple youtube channels provided as a string array. Returns an array of
    dicts with the enriched data.
    """
    result = []
    for channelId in channelIdList:
        channelResponse = __get_channel_info(youtubeClient, channelId)
        result.append(__map_youtube_channel_response(channelResponse, channelId))

    return result


def __map_youtube_channel_response(youtube_response, channelId):
    """
    Youtube channel information returned is mapped to a dict
    """
    response = {"id": channelId}
    if 'items' in youtube_response and len(youtube_response['items']) > 0:
        detailResponse = youtube_response['items'][0]
        views = __cast_to_integer(__extract(detailResponse, 'statistics.viewCount'))
        videoCount = __cast_to_integer(__extract(detailResponse, 'statistics.videoCount'))
        response.update({
            "name": __extract(detailResponse, "snippet.title"),
            "description": __extract(detailResponse, "snippet.description"),
            "language": __extract(detailResponse, "snippet.defaultLanguage"),
            "originSourceCountry": __extract(detailResponse, 'snippet.country'),
            "thumbnail": __extract(detailResponse, 'snippet.thumbnails.high.url'),
            "views": views,
            "averageView": views / videoCount,
            "videos": videoCount,
            "subscribers": __cast_to_integer(__extract(detailResponse, 'statistics.subscriberCount')),
            "mfk": __extract(detailResponse, 'status.madeForKids'),
            "url": f"https://www.youtube.com/channel/{__extract(detailResponse, 'id')}",
        })
    return __clean_nones(response)


def __cast_to_integer(string_value):
    """
    Casts a string to an integer unless it is None
    """
    if string_value is None:
        return string_value
    elif type(string_value) == str and string_value != "":
        return int(string_value)


def __extract(dict, path):
    return glom(dict, path, default=None)


def __get_channel_info(youtube, channel_id):
    """
    Returns information for the given channel through the Youtube API
    """
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
