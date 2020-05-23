from collections import defaultdict
from functools import lru_cache
from urllib.request import urlopen
from urllib.error import HTTPError
import json, gzip

from typing import Optional

from .cache import file_cache
from .common import JSONDict
from .api import make_api_type, API


DISCOVERY = 'https://www.googleapis.com/discovery/v1'
DISCOVERY_V1 = f'{DISCOVERY}' '/apis/{name}/{version}/rest'
DISCOVERY_V2 = (
    'https://{name}.googleapis.com/$discovery/rest?'
    'version={version}'
)


@lru_cache
def discover(name: str, version: Optional[str]=None) -> API:
    '''Constructs an API type for the service required and instantiates it.
    
    Args:
        name: name of the required service (e.g. drive).
        version: version of the required service, preferred version (set by
            google discovery api) is used if not specified.

    Returns:
        An `API` object corresponding to the required service.
    '''

    if version is None:
        version = _get_default_version(name)

    info = _surface_doc(name, version)
    apit = make_api_type(name, info)
    return apit()

@lru_cache(1)
@file_cache(post_process=json.loads)
def _list_apis() -> JSONDict:
    '''Returns google's list of APIs according to their discovery service.'''

    with urlopen(f'{DISCOVERY}/apis') as resp:
        return b'\n'.join(resp)

apis = defaultdict(list)
for api in _list_apis()['items']:
    apis[api['name']].append(api['version'])

def _get_default_version(name: str) -> str:
    '''Returns the JSON object describing the preferred version of the API
    name.
    
    Args:
        name: name of the required service.

    Returns:
        The JSON object describing the preferred version of the required
        service.

    Raises:
        ValueError: The requested service could not be found.
    '''

    for api in _list_apis()['items']:
        if api['name'] == name and api.get('preferred', False):
            return api['version']
    else:
        raise ValueError(f'no service with such name: {name}')

@lru_cache(300)  # > num of all versioned apis
@file_cache(post_process=json.loads)
def _surface_doc(name: str, version: str) -> JSONDict:
    '''Convenience function to fetch and cache google's surface document
    describing all services covered by the discovery API.'''

    exc = None

    # google offers multiple versions :)
    for template in (DISCOVERY_V1, DISCOVERY_V2):
        try:
            with urlopen(template.format(name=name, version=version)) as resp:
                binary = resp.read()

                if resp.info().get('Content-Encoding') == 'gzip':
                    binary = gzip.decompress(binary)

                return binary

        except HTTPError as e:
            exc = e
            pass

    # cannot be None
    raise exc
