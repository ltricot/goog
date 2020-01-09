from __future__ import annotations

from .method import make_method

from typing import Any, Union
from .common import JSONDict


RESOURCE_INFO_ATTR = 'infodoc'
RESOURCE_API_ATTR  = 'api'


class ResourceType(type):

    @classmethod
    def from_info(mcls, name, info):
        # generate methods and nested resources
        ns = {}
        for mn, mi in info.get('methods', {}).items():
            ns[mn] = make_method(mn, mi)

        assert RESOURCE_INFO_ATTR not in ns
        ns[RESOURCE_INFO_ATTR] = info

        return mcls(name, (Resource,), ns)


class Resource(metaclass=ResourceType):
    ...


class ResourceDescriptor:

    # TODO: apit: APIType
    # but circular import is an issue
    def __set_name__(self, apit: type, name: str):
        setattr(self._resource, RESOURCE_API_ATTR, apit)

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


    # the following methods complete the data decriptor protocol
    # they are necessary to show documentation when invoking help

    def __set__(self, obj: Any, value: Any):
        msg = f'cannot set resource attribute of {obj!r}'
        raise AttributeError(msg)

    def __delete__(self, obj: Any):
        msg = f'cannot delete resource attribute of {obj!r}'
        raise AttributeError(msg)
