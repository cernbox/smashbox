# -*- coding: utf-8 -*-

# wget https://raw.githubusercontent.com/kennethreitz/requests/v1.2.3/requests/structures.py

"""
requests.structures
~~~~~~~~~~~~~~~~~~~

Data structures that power Requests.

"""

import os
import collections.abc
from collections.abc import Iterable, Iterator, Mapping
from itertools import islice
from typing import Any, TypeVar

_V = TypeVar('_V')


class IteratorProxy(object):
    """docstring for IteratorProxy"""
    def __init__(self, i: Any) -> None:
        self.i = i
        # self.i = chain.from_iterable(i)

    def __iter__(self) -> Iterator[Any]:
        return self.i

    def __len__(self) -> int | None:
        if hasattr(self.i, '__len__'):
            return len(self.i)
        if hasattr(self.i, 'len'):
            return self.i.len
        if hasattr(self.i, 'fileno'):
            return os.fstat(self.i.fileno()).st_size
        return None

    def read(self, n: int | None) -> str:
        return "".join(islice(self.i, None, n))


class CaseInsensitiveDict(collections.abc.MutableMapping[str, _V]):
    """
    A case-insensitive ``dict``-like object.

    Implements all methods and operations of
    ``collections.MutableMapping`` as well as dict's ``copy``. Also
    provides ``lower_items``.

    All keys are expected to be strings. The structure remembers the
    case of the last key to be set, and ``iter(instance)``,
    ``keys()``, ``items()``, ``iterkeys()``, and ``iteritems()``
    will contain case-sensitive keys. However, querying and contains
    testing is case insensitive:

        cid = CaseInsensitiveDict()
        cid['Accept'] = 'application/json'
        cid['aCCEPT'] == 'application/json'  # True
        list(cid) == ['Accept']  # True

    For example, ``headers['content-encoding']`` will return the
    value of a ``'Content-Encoding'`` response header, regardless
    of how the header name was originally stored.

    If the constructor, ``.update``, or equality comparison
    operations are given keys that have equal ``.lower()``s, the
    behavior is undefined.

    """
    def __init__(self, data: Mapping[str, _V] | Iterable[tuple[str, _V]] | None = None, **kwargs: _V) -> None:
        self._store: dict[str, tuple[str, _V]] = dict()
        if data is None:
            data = {}
        self.update(data, **kwargs)

    def __setitem__(self, key: str, value: _V) -> None:
        # Use the lowercased key for lookups, but store the actual
        # key alongside the value.
        self._store[key.lower()] = (key, value)

    def __getitem__(self, key: str) -> _V:
        return self._store[key.lower()][1]

    def __delitem__(self, key: str) -> None:
        del self._store[key.lower()]

    def __iter__(self) -> Iterator[str]:
        return (casedkey for casedkey, mappedvalue in self._store.values())

    def __len__(self) -> int:
        return len(self._store)

    def lower_items(self) -> Iterator[tuple[str, _V]]:
        """Like iteritems(), but with all lowercase keys."""
        return (
            (lowerkey, keyval[1])
            for (lowerkey, keyval)
            in self._store.items()
        )

    def __eq__(self, other: object) -> bool:
        if isinstance(other, collections.abc.Mapping):
            other = CaseInsensitiveDict(other)
        else:
            return NotImplemented
        # Compare insensitively
        return dict(self.lower_items()) == dict(other.lower_items())

    # Copy is required
    def copy(self) -> 'CaseInsensitiveDict[_V]':
         return CaseInsensitiveDict(self._store.values())

    def __repr__(self) -> str:
        return '%s(%r)' % (self.__class__.__name__, dict(self.items()))


class LookupDict(dict[Any, Any]):
    """Dictionary lookup object."""

    def __init__(self, name: str | None = None) -> None:
        self.name = name
        super(LookupDict, self).__init__()

    def __repr__(self) -> str:
        return '<lookup \'%s\'>' % (self.name)

    def __getitem__(self, key: Any) -> Any:
        # We allow fall-through here, so values default to None

        return self.__dict__.get(key, None)

    def get(self, key: Any, default: Any = None) -> Any:
        return self.__dict__.get(key, default)
