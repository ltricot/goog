from .resource import ResourceDescriptor
from .common import JSONDict


def make_api_type(name: str, info: JSONDict):
    return APIType.from_info(name, info)


API_INFO_ATTR = 'infodoc'


class APIType(type):

    @classmethod
    def from_info(mcls: type, name: str, info: JSONDict):
        # generate resource descriptors
        ns = {}
        for rn in info.get('resources', {}):
            ns[rn] = ResourceDescriptor(rn, info)

        assert API_INFO_ATTR not in info
        ns[API_INFO_ATTR] = info
        ns['__doc__']  = info.get('description')

        return mcls(name, (API,), ns)


class API(metaclass=APIType):
    ...
