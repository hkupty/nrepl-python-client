import socket, sys
from cStringIO import StringIO

def _read_byte (s):
    return s.read(1)

def _read_int (s, terminator=None, init_data=None):
    int_chrs = init_data or []
    while True:
        c = _read_byte(s)
        if not c.isdigit() or c == terminator or not c:
            break
        else:
            int_chrs.append(c)
    return int(''.join(int_chrs))

def _read_bytes (s, n):
    data = StringIO()
    cnt = 0
    while cnt < n:
        m = s.read(n - cnt)
        if not m: raise Exception("Invalid bytestring, unexpected end of input.")
        data.write(m)
        cnt += len(m)
    data.flush()
    return data.getvalue().decode("UTF-8")

def _read_delimiter (s):
    d = _read_byte(s)
    if d.isdigit(): d = _read_int(s, ":", [d])
    return d

def _read_list (s):
    data = []
    while True:
        datum = _read_datum(s)
        if not datum: break
        data.append(datum)
    return data

def _read_map (s):
    i = iter(_read_list(s))
    return dict(zip(i, i))

_read_fns = {"i": _read_int,
             "l": _read_list,
             "d": _read_map,
             "e": lambda _: None,
             # EOF
             None: lambda _: None}

def _read_datum (s):
    delim = _read_delimiter(s)
    if delim:
        return _read_fns.get(delim, lambda s: _read_bytes(s, delim))(s)

def _write_datum (x, out):
    t = type(x)
    if t in {str, unicode}:
        x = x.encode("UTF-8")
        out.write(str(len(x)))
        out.write(":")
        out.write(x)
    elif t == int:
        out.write("i")
        out.write(str(x))
        out.write("e")
    elif t == list or t == tuple:
        out.write("l")
        for v in x: _write_datum(v, out)
        out.write("e")
    elif t == dict:
        out.write("d")
        for k, v in x.items():
            _write_datum(k, out)
            _write_datum(v, out)
        out.write("e")
    out.flush()

def encode (v):
    "bencodes the given value, may be a string, integer, list, or dict."
    s = StringIO()
    _write_datum(v, s)
    return s.getvalue()

def decode_file (file):
    while True:
        x = _read_datum(file)
        if not x: break
        yield x

def decode (string):
    "Generator that yields decoded values from the input string."
    return decode_file(StringIO(string))

class BencodeIO (object):
    def __init__ (self, file):
        self._file = file

    def read (self):
        return _read_datum(self._file)

    def __iter__ (self): return self
    def next (self):
        v = self.read()
        if not v: raise StopIteration
        return v

    def write (self, v):
        return _write_datum(v, self._file)

    def flush (self):
        if self._file.flush: self._file.flush()

    def close (self):
        self._file.close()
    
