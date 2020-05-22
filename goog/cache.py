from functools import wraps
from typing import Callable
import tempfile, os


_CACHE_NAME_PREFIX = 'better-than-google-cache'


# TODO: implement max age
# TODO: do not depend on `hash` as this will differ across runtimes in secure
# environments
def file_cache(*, post_process: Callable) -> \
        Callable[[Callable], Callable]:
    # don't you find decorators fun to type hint ?

    def decorator(func: Callable) -> Callable:
        cache = f'{_CACHE_NAME_PREFIX}-{func.__qualname__}.txt'
        path = os.path.join(tempfile.gettempdir(), cache)
        if not os.path.exists(path):
            os.makedirs(path)

        # TODO: check `wraps` updates type signature
        @wraps(func)
        def wrapper(*args, **kws):
            fname = os.path.join(path, str(hash((args, tuple(kws.items())))))
            if os.path.exists(fname):
                text = open(fname, 'rb').read()
            else:
                text = func(*args, **kws)
                with open(fname, 'wb') as f:
                    f.write(text)
            return post_process(text)

        return wrapper
    return decorator
