import aiohttp

import asyncio
from inspect import Signature, Parameter
import os.path

from typing import Any, List, Callable
from .common import JSONDict


def _get_annot(tp):
    return {
        'any':     Any,
        'array':   List,
        'boolean': bool,
        'integer': int,
        'number':  float,
        'object':  JSONDict,
        'string':  str,
    }[tp]


def make_method(name: str, rname: str, info: JSONDict) -> Callable:
    rinfo = info['resources'][rname]
    minfo = rinfo['methods'][name]

    parameters = minfo.get('parameters', {})

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

        url = url_template.format(**{
            pn: pv for pn, pv in pars.arguments.items()
            if pn in path
        })

        query_parameters = {
            pn: pv for pn, pv in pars.arguments.items()
            if pn in query
        }

        return minfo['httpMethod'], url, query_parameters

        # return aiohttp.request(
        #     method=minfo['httpMethod'],
        #     url=url,
        #     params=query_parameters,
        # )

    method.__name__ = name
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
