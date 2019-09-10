import aiohttp

import asyncio
from inspect import Signature, Parameter

from typing import Any, List
from .common import JSONDict


def _get_annot(tp):
    return {
        'any':      Any,
        'array':    List,
        'boolean':  bool,
        'integer':  int,
        'number':   float,
        'object':   JSONDict,
        'string':   str,
    }[tp]


def make_method(name, info) -> callable:
    async def method(self, *args, **kwargs):
        ...

    method.__name__ = name
    method.__doc__ = info.get('description')

    # create signature using json schema of parameters
    parameters = {}
    for pn, pi in info.get('parameters', {}).items():
        kind = Parameter.KEYWORD_ONLY
        if pi.get('required', False):
            kind = Parameter.POSITIONAL_OR_KEYWORD

        tp = pi.get('type', 'string')
        tp = _get_annot(tp)

        default = None
        if 'default' in pi:
            default = pi['default']
            if tp == List:
                default = list(default)
            elif tp == JSONDict:
                default = dict(default)
            else:
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

    # TODO: return_annotation, see googleapiclient.model
    sig = Signature(sorted_parameters)
    method.__signature__ = sig

    return method
