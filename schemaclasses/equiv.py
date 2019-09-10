'''See https://developers.google.com/discovery/v1/type-format

This is derived from JSONSchema
'''

from typing import NewType, Any, List, Dict
from datetime import date, datetime


JSONDict = Dict[str, Any]
Base64 = NewType('Base64', str)


types = {
    'any':      Any,
    'array':    List,
    'boolean':  bool,
    'integer':  int,
    'number':   float,
    'object':   JSONDict,
    'string':   str,
}

formats = {
    'int32':    int,
    'uint32':   int,
    'double':   float,
    'float':    float,
    'byte':     Base64,
    'date':     date,
    'datetime': datetime,
    'int64':    int,
    'uint64':   int
}

def get_annot(info):
    tp = types['type']
    if tp == List:
        tp = List[get_annot(info['items'])]
    return tp

def get_constructor(info):
    tp = types['type']
    if tp == List:
        return list
    if tp == JSONDict:
        return dict
    if tp == bool:
        return lambda s: s.lower() == 'true'
    return tp
