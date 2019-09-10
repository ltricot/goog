from schemaclasses.schemas import fromschema
import json
from dataclasses import fields
from pprint import pprint


with open('schemas.json') as f:
    info = json.load(f)

for sname, schema in info.items():
    dcls = fromschema(schema)
    pprint(fields(dcls))
