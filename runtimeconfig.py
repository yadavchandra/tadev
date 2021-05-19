# Copyright 2015 Google Inc. All Rights Reserved.
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

"""Uses the google runtime config library to fetch all configuration
variables for a particular config and (optionally) updates os.environ
with these variables.

To just get the runtime configuration variables::

    >>> variables = runtimeconfig.fetch(config_name)
    {'key': 'value', ...}

To get the variables and update ``os.environ``::

    >>> runtimeconfig.fetch_and_update_environ(config_name)
    >>> os.environ['SOME_KEY']
    some_value

It will *not* replace keys already present in ``os.environ``.
"""

import base64
import logging
import os
import sys
import traceback

import gcloud._helpers
import gcloud.credentials
from googleapiclient import discovery
import httplib2shim

logger = logging.getLogger(os.getenv('FUNCTION_NAME'))
logger.setLevel(logging.INFO)

def _create_client():
    credentials = gcloud.credentials.get_credentials()
    logger.debug("creds: {}".format(repr(credentials)))
    client = discovery.build(
        'runtimeconfig',
        'v1beta1',
        credentials=credentials)
#        http=httplib2shim.Http())
    return client


def _list_variables(client, project_name, config_name):
    r = client.projects().configs().variables().list(
        parent='projects/{}/configs/{}'.format(project_name, config_name)).execute()
    return [variable['name'] for variable in r.get('variables', [])]


def _fetch_variable_values(client, variable_names):
    variables = {}

    def batch_callback(request_id, response, exception):
        if exception is not None:
            raise exception

        # The variable name has the whole path in it, so just get the last
        # part.
        variable_name = response['name'].split('/')[-1]
        # b64 decoded value decode from bytes string type
        # TODO: check this more carefully
        variables[variable_name] = base64.b64decode(response['value']).decode()

    batch = client.new_batch_http_request(callback=batch_callback)

    for variable_name in variable_names:
        batch.add(client.projects().configs().variables().get(
            name=variable_name))

    batch.execute()

    return variables


def fetch(project_name, config_name):
    """Fetch the variables and values for the given config.

    Returns a dictionary of variable names to values."""
    # project = gcloud._helpers._determine_default_project()
    client = _create_client()

    variable_names = _list_variables(client, project_name, config_name)
    variables = _fetch_variable_values(client, variable_names)

    return variables


def update_environ(variables):
    """Updates ``os.environ`` with the given values.

    Transforms the key name from ``some-key`` to ``SOME_KEY``.

    It will *not* replace keys already present in ``os.environ``. This means
    you can locally override whatever is in the runtime config.
    """
    for name, value in variables.items():
        compliant_name = name.upper().replace('-', '_')
        # logger.debug("set env var {} = {}".format(compliant_name, value))
        os.environ.setdefault(compliant_name, value)


def fetch_and_update_environ(project_name, config_name):
    """Fetches the variables and updates ``os.environ``."""
    try : 
        variables = fetch(project_name, config_name)
        update_environ(variables)
        return variables
    except :
        exc_type, exc_value, exc_traceback = sys.exc_info()
        
        logger.error(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
