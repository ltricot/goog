from __future__ import annotations

from .method import make_method

from typing import Any, Union
from .common import JSONDict


RESOURCE_INFO_ATTR = 'infodoc'
RESOURCE_API_ATTR  = 'api'
RESOURCE_METHOD_MARKER = '__is_method__'


class ResourceType(type):

    @classmethod
    def from_info(mcls: type, name: str, info: JSONDict):
        # generate methods and nested resources
        # TODO: nested resources
        rinfo = info['resources'][name]

        ns = {}
        for mn in rinfo.get('methods', {}):
            ns[mn] = make_method(mn, name, info)
            setattr(ns[mn], RESOURCE_METHOD_MARKER, True)

        assert RESOURCE_INFO_ATTR not in ns
        ns[RESOURCE_INFO_ATTR] = rinfo

        return mcls(name, (Resource,), ns)


class Resource(metaclass=ResourceType):

    def __init__(self):
        ...


class ResourceDescriptor:

    def __set_name__(self, apit: type, name: str):
        setattr(self._resource, RESOURCE_API_ATTR, apit)
        assert name == self.name

    def __init__(self, name: str, info: JSONDict):
        # TODO: set documentation to something interesting
        # no description in API surface document
        self.__doc__ = None
        self.name = name

        self._resource_type = ResourceType.from_info(name, info)
        self._resource = self._resource_type()

    def __get__(self, obj: Any, tp: type=None) -> \
            Union[Resource, ResourceDescriptor]:
        if obj is None:
            return self
        return self._resource


    # the following two methods complete the data decriptor protocol
    # they are necessary to show documentation when invoking help

    def __set__(self, obj: Any, value: Any):
        msg = f'cannot set resource attribute of {obj!r}'
        raise AttributeError(msg)

    def __delete__(self, obj: Any):
        msg = f'cannot delete resource attribute of {obj!r}'
        raise AttributeError(msg)
