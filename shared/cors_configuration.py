def configure_cors(request, response_code, controller=(lambda _: "")):
    """
    Sets the CORS headers for regular and preflight requests

    For more information about CORS and CORS preflight requests, see
    https://developer.mozilla.org/en-US/docs/Glossary/Preflight_request
    for more information.
    """

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

        return '', 204, headers

    # Set CORS headers for the main request
    headers = {
        'Access-Control-Allow-Origin': '*'
    }

    return controller(request), response_code, headers
