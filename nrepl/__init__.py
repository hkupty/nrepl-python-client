#!/usr/bin/env python

'''
    nrepl
    -----

    A Python client for the nREPL Clojure networked-REPL server.

    :copyright: (c) 2013 by Chas Emerick.
    :license: MIT, see LICENSE for more details.
'''


import socket
import nrepl.bencode as bencode

try:
    from urlparse import urlparse, ParseResult
except ImportError:
    from urllib.parse import urlparse, ParseResult

__version_info__ = ('0', '0', '4')
__version__ = '.'.join(__version_info__)
__author__ = 'Chas Emerick'
__license__ = 'MIT'
__copyright__ = '(c) 2013 by Chas Emerick'
__all__ = ['connect']


def _bencode_connect(uri):
    s = socket.create_connection(uri.netloc.split(":"))
    f = s.makefile('rw')
    return bencode.BencodeIO(f, on_close=s.close)


def _match_criteria(criteria, msg):
    for k, v in criteria.items():
        mv = msg.get(k, None)
        if isinstance(v, set):
            if mv not in v:
                return False
        elif not v and mv:
            pass
        elif not mv or v != mv:
            return False
    return True


# others can add in implementations here
_connect_fns = {"nrepl": _bencode_connect}


def connect(uri):
    """
    Connects to an nREPL endpoint identified by the given URL/URI.  Valid
    examples include:

      nrepl://192.168.0.12:7889
      telnet://localhost:5000
      http://your-app-name.heroku.com/repl

    This fn delegates to another looked up in  that dispatches on the scheme of
    the URI provided (which can be a string or java.net.URI).  By default, only
    `nrepl` (corresponding to using the default bencode transport) is
    supported. Alternative implementations may add support for other schemes,
    such as http/https, JMX, various message queues, etc.
    """
    #
    uri = uri if isinstance(uri, ParseResult) else urlparse(uri)
    if not uri.scheme:
        raise ValueError("uri has no scheme: " + uri)
    f = _connect_fns.get(uri.scheme.lower(), None)
    if not f:
        err = "No connect function registered for scheme `%s`" % uri.scheme
        raise Exception(err)
    return f(uri)
