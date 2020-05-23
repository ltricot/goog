from .discovery import discover, apis
from .api import API


# enables 'from goog import drive'
# only called when nothing is found
def __getattr__(name: str) -> API:
    api = discover(name)
    return api
