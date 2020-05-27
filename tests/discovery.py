from googleapiclient.discovery import build, Resource
from googleapiclient.errors import UnknownApiNameOrVersion

from urllib.error import HTTPError
from collections import defaultdict
import unittest

from goog.discovery import discover, apis


def _gac_resources(service):
    for name in service._dynamic_attrs:
        attr = getattr(service, name)

        try:
            resource = attr.__call__()  # let's be explicit
        # is a method
        except TypeError:
            continue

        if not isinstance(resource, Resource):
            continue

        yield name, resource

def _gac_resource_methods(resource):
    for name in resource._dynamic_attrs:
        attr = getattr(service, name)

        try:
            method = attr.__call__()
        except TypeError:
            yield name, attr
            continue

        if isinstance(method, Resource):
            continue

        yield name, attr


class ApiCoverage(unittest.TestCase):
    '''Concerned with which service coverage, resource coverage in each service,
    and method coverage in each resource of each service.
    '''

    def setUp(self):
        self.services = defaultdict(dict)

    def test_discovery(self):
        for api in apis:
            for version in apis[api]:
                with self.subTest(api=api, version=version):
                    try:
                        self.services[api][version] = discover(api, version)
                    except HTTPError as e:
                        try:
                            build(api, version)
                        except UnknownApiNameOrVersion:
                            self.skipTest(
                                f'{api} {version} isn\'t found by '
                                'reference library either'
                            )
                        else:
                            raise e

    def test_resources(self):
        for api in self.services:
            for version, service in self.services[api].items():
                for name, _ in _gac_resources(build(api, version)):
                    with self.subTest(api=api, version=version, resource=name):
                        self.assertTrue(hasattr(service, name))

    def test_methods(self):
        for api in self.services:
            for version, service in self.services[api].items():
                for rname, resource in _gac_resources(build(api, version)):
                    for mname, _ in _gac_resource_methods(resource):
                        with self.subTest(
                            api=api,
                            version=version,
                            resource=rname,
                            method=mname,
                        ):
                            if not hasattr(service, rname):
                                self.skipTest(f'{rname} not discovered')

                            self.assertTrue(hasattr(resource, mname))
