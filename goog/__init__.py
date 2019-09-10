from .discovery import discover
from .api import API


# enables 'from goog import drive'
def __getattr__(name: str) -> API:
    api = discover(name)
    return api
