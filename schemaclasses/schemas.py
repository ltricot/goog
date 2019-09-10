'''See https://developers.google.com/discovery/v1/reference/apis

This is derived from JSONSchema
'''

from __future__ import annotations

from dataclasses import dataclass, make_dataclass, field, Field
from functools import wraps

from typing import NewType, ClassVar, Dict, Optional, List, Any, Union, Tuple
from .equiv import types, formats, JSONDict, Base64

__all__ = ['fromschema', 'toschema']


JSONSchema = NewType('JSONSchema', JSONDict)
DataClass = NewType('DataClass', type)

SchemaId = NewType('SchemaId', str)

@dataclass
class Schema:
    __cache: ClassVar[Dict[str, Schema]] = {}

    id:                     str
    type:                   str
    ref:                    Optional[SchemaId]
    description:            Optional[str]
    default:                Optional[Any]  # of type type (above)
    required:               Optional[bool]
    format:                 Optional[str]
    pattern:                Optional[str]
    minimum:                Optional[str]
    maximum:                Optional[str]
    enum:                   Optional[List]
    enumDescriptions:       Optional[List[str]]
    repeated:               Optional[bool]
    location:               Optional[str]
    properties:             Optional[Dict[str, Schema]]
    additionalProperties:   Optional[Schema]
    items:                  Optional[Schema]
    annotations:            Optional[JSONDict]  # with key: "required[]"

    def from_json(cls, info):
        if '$ref' in info:  # no other choice
            info['ref'] = info['$ref']
            del info['$ref']

        # recursive parsing
        for prop in ('items', 'additionalProperties'):
            info[prop] = cls.from_json(info[prop])

        for key, schema in info.get('properties', {}).items():
            info['properties'][key] = cls.from_json(schema)

        return cls(**info)

def fromschema(schema: JSONSchema, name: str=None) -> DataClass:
    tp = schema['type']

    handler = _handlers.get(tp)
    if handler is None:
        raise ValueError(tp)

    # so that a property knows its name
    if name is not None and schema.get('type') == 'object':
        return handler(schema, name)
    return handler(schema)

HANDLER_ERR_MSG = 'expected schema with type "{}" but got type "{}"'
FORMAT_HANDLER_ERR_MSG = 'expected schema with format "{}" but got format "{}"'
_handlers = {}
_format_handlers = {}

PrimitiveField = Union[Tuple[type], Tuple[type, Field]]

def _schema_handler(handler: callable):
    tname = handler.__name__[8:]  # exclude _handle_

    @wraps(handler)
    def _(schema: JSONSchema) -> Union[DataClass, PrimitiveField]:
        if schema['type'] != tname:
            raise ValueError(HANDLER_ERR_MSG.format(tname, schema['type']))
        return handler(schema)

    _handlers[tname] = _
    return _

def _format_handler(handler: callable):
    fname = handler.__name__[8:]  # exclude _handle_

    @wraps(handler)
    def _(schema: JSONSchema) -> PrimitiveField:
        if schema['format'] != fname:
            raise ValueError(
                FORMAT_HANDLER_ERR_MSG.format(fname, schema['format']))
        return handler(schema)

    _format_handlers[fname] = _
    return _

def _primitive_handler(tname: str, primitive: type, format: bool=True):
    # `format` indicates whether format is relevant

    def _(schema: JSONSchema) -> PrimitiveField:
        if format and 'format' in schema:
            handler = _format_handlers(schema['format'])
            return handler(schema)

        if 'default' in schema:
            return primitive, field(default=schema['default'])
        return primitive,

    _.__name__ = f'_handle_{tname}'
    _ = _schema_handler(_)
    return _

@_schema_handler
def _handle_object(schema: JSONSchema, name: str=None) -> DataClass:
    fields = []
    for key, schema in schema['properties'].items():
        args = (schema,)
        fields.append((key, *fromschema(*args)))

    def __post_init__(self):
        # for non-trivial formats
        for f in fields(self):
            pro = f.metadata.get('post-process')
            if pro is None:
                setattr(self, f.name, pro(getattr(self, f.name)))

    namespace = {'__post_init__': __post_init__}
    name = schema.get('id', name or '_unknown_name')
    return make_dataclass(name, fields, namespace=namespace)

@_schema_handler
def _handle_array(schema: JSONSchema) -> Tuple[type]:
    it = fromschema(schema['items'])
    return List[it],

@_schema_handler
def _handler_any(schema: JSONSchema) -> Tuple[type]:
    return Any,  # what'll you do

_handle_integer = _primitive_handler('integer', int, format=False)
_handle_number  = _primitive_handler('number', float, format=False)
_handle_string  = _primitive_handler('string', str)
_handle_boolean = _primitive_handler('boolean', bool, format=False)

@_format_handler
def _handle_int64(schema: JSONSchema) -> PrimitiveField:
    return InitVar[str], field(
            metadata={'post-process': int},
            default=schema.get('default'))

@_format_handler
def _handle_uint64(schema: JSONSchema) -> PrimitiveField:
    return InitVar[str], field(
            metadata={'post-process': int},
            default=schema.get('default'))

@_format_handler
def _handle_byte(schema: JSONSchema) -> PrimitiveField:
    return InitVar[str], field(
            metadata={'post-process': b64decode},
            default=schema.get('default'))

def toschema(dcls: DataClass) -> JSONSchema:
    ...
