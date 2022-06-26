import itertools
import sys

PY2 = int(sys.version_info[0]) == 2

if PY2:
    # pytype: disable=import-error
    # pytype: disable=name-error
    # pytype: disable=module-attr
    import urlparse

    urlparse = urlparse
    text_type = unicode
    binary_type = str
    string_types = (str, unicode)
    unicode = unicode
    basestring = basestring
    iterkeys = lambda d: d.iterkeys()
    itervalues = lambda d: d.itervalues()
    iteritems = lambda d: d.iteritems()
    zip_longest = itertools.izip_longest
    # pytype: enable=import-error
    # pytype: enable=name-error
    # pytype: disable=module-attr
else:
    import urllib.parse

    urlparse = urllib.parse
    text_type = str
    binary_type = bytes
    string_types = (str,)
    unicode = str
    basestring = (str, bytes)
    iterkeys = lambda d: d.keys()
    itervalues = lambda d: d.values()
    iteritems = lambda d: d.items()
    zip_longest = itertools.zip_longest
