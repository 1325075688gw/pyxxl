import time
import logging
from functools import wraps


def retry(exception, tries=3, delay=1, back_off=2, logger=None):
    """Retry calling the decorated function using an exponential backoff.

    http://www.saltycrane.com/blog/2009/11/trying-out-retry-decorator-python/
    original from: http://wiki.python.org/moin/PythonDecoratorLibrary#Retry

    :param exception: the exception to check. may be a tuple of
        exceptions to check
    :type exception Exception
    :param tries: number of times to try (not retry) before giving up
    :type tries: int
    :param delay: initial delay between retries in seconds
    :type delay: int
    :param back_off: back off multiplier e.g. value of 2 will double the delay
        each retry
    :type back_off: int
    :param logger: logger to use. If None, print
    :type logger: logging.Logger instance
    """

    def deco_retry(f):
        @wraps(f)
        def f_retry(*args, **kwargs):
            m_tries, m_delay = tries, delay
            while m_tries > 1:
                try:
                    return f(*args, **kwargs)
                except exception as e:
                    msg = f"{e}, Retrying in {m_delay} seconds..."
                    if logger:
                        logger.info(msg)
                    else:
                        logging.info(msg)
                    if m_delay > 0:
                        time.sleep(m_delay)
                    m_tries -= 1
                    m_delay *= back_off
            return f(*args, **kwargs)

        return f_retry  # true decorator

    return deco_retry
