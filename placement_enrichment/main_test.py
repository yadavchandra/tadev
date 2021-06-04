import os
from subprocess import STDOUT
import subprocess
import time
import requests
from urllib3.util.retry import Retry

enrich_channels_schema = {
    "$schema": "https://json-schema.org/schema#",

    "type" : "object",
    "properties" : {
        "channelId" : {"type" : "string"},
        "country" : {"type" : "string"},
        "description" : {"type" : "string"},
        "madeForKids" : {"type" : "boolean"},
        "subscribers" : {"type" : "integer"},
        "thumbnail" : {"type" : "string"},
        "title" : {"type" : "string"},
        "videoCount" : {"type" : "integer"},
        "views" : {"type" : "integer"},
    }
}

def test_post_enrich_channels_success():
    port = os.getenv('PORT', 8095)  # Each functions framework instance needs a unique port

    process = subprocess.Popen(
      [
        'functions-framework',
        '--target', 'entrypoint',
        # '--source', 'main.py',
        # '--signature-type=http',
        '--port', str(port)
      ],
      cwd=os.path.dirname(__file__),
      stdin=subprocess.PIPE,
      stdout=subprocess.PIPE,
      stderr=subprocess.STDOUT,
      shell=True
    )

    # Send HTTP request simulating Pub/Sub message
    # (GCF translates Pub/Sub messages to HTTP requests internally)
    # BASE_URL = f'http://localhost:{port}'
    #
    # retry_adapter = requests.adapters.HTTPAdapter()
    #
    # session = requests.Session()
    # session.mount(BASE_URL, retry_adapter)
    #
    # response = requests.post(
    #   BASE_URL,
    #   json=[
    #       "UCbCmjCuTUZos6Inko4u57UQ"
    #   ]
    # )
    # assert response.status_code == 200
    # assert response.headers["content-type"] == "application/json"
    #
    # response_body = response.json()

    time.sleep(100)
    # Stop the functions framework process
    process.kill()
    process.wait()