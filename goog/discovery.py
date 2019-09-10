from functools import lru_cache
from urllib.request import urlopen
import json

from typing import Optional

from .common import JSONDict
from .api import make_api_type, API


DISCOVERY = 'https://www.googleapis.com/discovery/v1'

def discover(name: str, version: Optional[str]=None) -> API:
    if version is None:
        version = _get_default_version(name)

    info = _surface_doc(name, version)
    apit = make_api_type(name, info)
    return apit()

@lru_cache(1)
def _list_apis() -> JSONDict:
    with urlopen(f'{DISCOVERY}/apis') as resp:
        return json.loads(b'\n'.join(resp))

def _get_default_version(name: str) -> str:
    for api in _list_apis()['items']:
        if api['name'] == name and api.get('preferred', False):
            return api['version']
    else:
        raise ValueError(f'no service with such name: {name}')

@lru_cache(300)  # > num of all versioned apis
def _surface_doc(name: str, version: str) -> JSONDict:
    with urlopen(f'{DISCOVERY}/apis/{name}/{version}/rest') as resp:
        return json.loads(b'\n'.join(resp))
