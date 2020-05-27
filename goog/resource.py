from __future__ import annotations

from typing import Any, Union

from .method import make_method
from .common import (
   JSONDict, RESOURCE_INFO_ATTR, RESOURCE_API_ATTR, RESOURCE_METHOD_MARKER,
   API_RESOURCE_MARKER
)


class ResourceType(type):

    @classmethod
    def from_info(
            mcls: type, name: str, info: JSONDict,
            nested: Optional[str]=None) -> Resource:
        '''Generate methods and nested resources.'''

        if nested:
            rinfo = info['resources'][nested]
            rinfo = rinfo['resources'][name]
        else:
            rinfo = info['resources'][name]

        ns = {}
        for rn in rinfo.get('resources', {}):
            ns[rn] = ResourceDescriptor(rn, info, nested=name)
            setattr(ns[rn], API_RESOURCE_MARKER, True)

        for mn in rinfo.get('methods', {}):
            ns[mn] = make_method(mn, name, info, nested=nested)
            setattr(ns[mn], RESOURCE_METHOD_MARKER, True)

        assert RESOURCE_INFO_ATTR not in ns
        ns[RESOURCE_INFO_ATTR] = rinfo

        return mcls(name, (Resource,), ns)


class Resource(metaclass=ResourceType):

    def __iter__(self):
        for key, val in vars(type(self)).items():
            if hasattr(val, RESOURCE_METHOD_MARKER):
                method = getattr(self, key)
                yield method


class ResourceDescriptor:

    def __set_name__(self, apit: type, name: str):
        setattr(self._resource, RESOURCE_API_ATTR, apit)
        self.name = name

    def __init__(self, *args, **kwargs):
        # TODO: set documentation to something interesting
        # no description in API surface document
        self.__doc__ = None

        self._resource_type = ResourceType.from_info(*args, **kwargs)
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
