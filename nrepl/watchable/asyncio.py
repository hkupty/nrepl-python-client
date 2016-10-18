import asyncio


class WatchableConnection(object):
    def __init__(self, IO):
        """
        Create a new WatchableConnection with an nREPL message transport
        supporting `read()` and `write()` methods that return and accept nREPL
        messages, e.g. bencode.BencodeIO.
        """
        self._IO = IO
        self._watches = {}
        self._loop = asyncio.get_event_loop()

    def close(self):
        self._IO.close()

    async def run_watches(self):
        for incoming in self._IO:
            for key, (pred, callback) in self._watches.items():
                if pred(incoming):
                    callback(incoming, self, key)

    def send(self, message):
        "Send an nREPL message."
        self._IO.write(message)
        self._loop.run_until_complete(self.run_watches)

    def unwatch(self, key):
        "Removes the watch previously registered with [key]."
        with self._watches_lock:
            self._watches.pop(key, None)

    def watch(self, key, criteria, callback):
        """
        Registers a new watch under [key] (which can be used with `unwatch()`
        to remove the watch) that filters messages using [criteria] (may be a
        predicate or a 'criteria dict' [see the README for more info there]).
        Matching messages are passed to [callback], which must accept three
        arguments: the matched incoming message, this instance of
        `WatchableConnection`, and the key under which the watch was
        registered.
        """
        if hasattr(criteria, '__call__'):
            pred = criteria
        else:
            pred = lambda incoming: _match_criteria(criteria, incoming)
        with self._watches_lock:
            self._watches[key] = (pred, callback)

