import aiohttp

import asyncio
from inspect import Signature, Parameter
import os.path
import re

from typing import Any, List, Callable, Optional
from .common import JSONDict


def _get_annot(tp):
    '''Convenience function to associate jsonschema annotations to python
    annotations.
    '''

    return {
        'any':     Any,
        'array':   List,
        'boolean': bool,
        'integer': int,
        'number':  float,
        'object':  JSONDict,
        'string':  str,
    }[tp]

def _parameter_name(pn: str):
    '''Adapts any string to become a valid python identifier, except keywords.
    '''

    pn, n = re.subn('[^a-zA-Z0-9_]', '_', pn)
    if pn[0].isnumeric():
        return f'x{pn[1:]}'
    return pn

def make_method(name: str, rname: str, info: JSONDict,
        nested: Optional[str]=None) -> Callable:
    '''Create method for a resource managed by an API.
    
    Args:
        name: name of the method.
        rname: name of the owning resource.
        info: surface document of the owning API.
    
    Returns:
        The necessary components to build an unauthenticated request to the
        google api: a tuple (method, url, parameters, headers, body).
    '''

    if nested:
        rinfo = info['resources'][nested]
        rinfo = rinfo['resources'][rname]
    else:
        rinfo = info['resources'][rname]

    minfo = rinfo['methods'][name]

    # TODO: add undocumented method parameters unavailable through discovery:
    #  - trace
    #  - pp
    #  - userip
    #  - strict

    # TODO: add body parameter when appropriate ('request' in minfo)

    # method specific parameters
    parameters = {
        _parameter_name(pn): pi
        for pn, pi in minfo.get('parameters', {}).items()
    }

    # api wide method parameters
    parameters.update({
        _parameter_name(pn): pi
        for pn, pi in info.get('parameters', {}).items()
    })

    # path parameters
    path = {
        pn for pn, pi in parameters.items()
        if pi['location'] == 'path'
    }

    # query parameters
    query = {
        pn for pn, pi in parameters.items()
        if pi['location'] == 'query'
    }

    url_template = info['baseUrl']
    url_template = os.path.join(url_template, minfo['path'])

    def method(self, *args, **kwargs):
        pars = method.__signature__.bind(self, *args, **kwargs)

        # url parameters (path arguments)
        url = url_template.format(**{
            pn: pv for pn, pv in pars.arguments.items()
            if pn in path
        })

        # query parameters (?pn=pv)
        query_parameters = {
            pn: pv for pn, pv in pars.arguments.items()
            if pn in query
        }

        # (method, url, query_parameters, headers, body)
        return minfo['httpMethod'], url, query_parameters, {}, b''

        # return aiohttp.request(
        #     method=minfo['httpMethod'],
        #     url=url,
        #     params=query_parameters,
        # )

    method.__name__ = name
    method.__qualname__ = f'{info["name"]}.{rname}.{name}'

    # TODO: add parameter description in method documentation
    # found in pi['description'] for each parameter
    # TODO: add return specification according to minfo['response']
    method.__doc__ = minfo.get('description')

    # create signature using json schema of parameters
    sig_parameters = {}
    for pn, pi in parameters.items():
        kind = Parameter.KEYWORD_ONLY
        if pi.get('required', False):
            kind = Parameter.POSITIONAL_OR_KEYWORD

        # TODO: all logic (including default) should be in _get_annot
        tp = pi.get('type', 'string')
        tp = _get_annot(tp)

        default = None
        if 'default' in pi:
            default = pi['default']

            if tp == List:
                # default args better be immutable
                default = tuple(default)

            elif tp == JSONDict:
                # can't always make it be
                default = dict(default)

            # TODO: check whether default should be enforced client side
            # or is simply documenting server side behavior
            else:  # we are OPTIMISTS
                default = tp(default)

        p = Parameter(
            name=pn,
            kind=Parameter.POSITIONAL_OR_KEYWORD,
            default=default,
            annotation=tp,
        )

        sig_parameters[pn] = p

    sorted_parameters = [Parameter('self', kind=Parameter.POSITIONAL_ONLY)]
    for p in info.get('parameterOrder', ()):
        sorted_parameters.append(sig_parameters.pop(p))
    sorted_parameters.extend(sig_parameters.values())

    # TODO: return_annotation, see aiohttp annotations
    sig = Signature(sorted_parameters)
    method.__signature__ = sig  # type: ignore

    return method
