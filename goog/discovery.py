from functools import lru_cache
from urllib.request import urlopen
import json

from typing import Optional

from .cache import file_cache
from .common import JSONDict
from .api import make_api_type, API


DISCOVERY = 'https://www.googleapis.com/discovery/v1'


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

    with urlopen(f'{DISCOVERY}/apis/{name}/{version}/rest') as resp:
        return b'\n'.join(resp)
