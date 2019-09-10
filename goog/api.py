from .resource import ResourceDescriptor
from .common import JSONDict


def make_api_type(name, info):
    return APIType.from_info(name, info)


class APIType(type):

    @classmethod
    def from_info(mcls, name, info):
        # generate resource descriptors
        ns = {}
        for rn, ri in info.get('resources', {}).items():
            ns[rn] = ResourceDescriptor(rn, ri)

        return mcls(name, (API,), ns)

class API(metaclass=APIType):
    ...
