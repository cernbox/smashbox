
from typing import Any, TypeVar

_F = TypeVar('_F')

def add_worker(f: _F, name: str | None = None) -> _F:
   return f

import logging
logger = logging.getLogger()

config: dict[str, Any] = {}

# test-cases may define a list of alternative configurations (set by bin/smash before loading a test-case)
testsets: list[dict[str, Any]]
