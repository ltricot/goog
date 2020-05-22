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


def make_method(name, info) -> Callable:
    def method(self, *args, **kwargs):
        # TODO: find a way to cache computation
        # -----
        infodoc = self.infodoc['methods'][name]

        # path parameters
        path = {
            pn for pn, pi in infodoc['parameters'].items()
            if pi['location'] == 'path'
        }

        # query parameters
        query = {
            pn for pn, pi in infodoc['parameters'].items()
            if pi['location'] == 'query'
        }

        # TODO:
        # doing this means there is no point in
        #  - API_INFO_ATTR
        #  - RESOURCE_API_ATTR
        #  - RESOURCE_INFO_ATTR
        url_template = self.api.infodoc['baseUrl']
        url_template = os.path.join(url_template, infodoc['path'])
        # -----

        pars = method.__signature__.bind(self, *args, **kwargs)

        url = url_template.format(**{
            pn: pv for pn, pv in pars.arguments.items()
            if pn in path
        })

        query_parameters = {
            pn: pv for pn, pv in pars.arguments.items()
            if pn in query
        }

        return aiohttp.request(
            method=infodoc['httpMethod'],
            url=url,
            params=query_parameters,
        )

    method.__name__ = name
    method.__doc__ = info.get('description')

    # create signature using json schema of parameters
    parameters = {}
    for pn, pi in info.get('parameters', {}).items():
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

        parameters[pn] = p

    sorted_parameters = [Parameter('self', kind=Parameter.POSITIONAL_ONLY)]
    for p in info.get('parameterOrder', ()):
        sorted_parameters.append(parameters.pop(p))
    sorted_parameters.extend(parameters.values())

    # TODO: return_annotation, see aiohttp annotations
    sig = Signature(sorted_parameters)
    method.__signature__ = sig  # type: ignore

    return method
