# ##### REFLECTION ############

from typing import Any, Protocol


class SharedObject(Protocol):
    """ State shared between the worker processes (see _smash_SmashSharedObject in multiprocessing_engine).
    """
    def __getitem__(self, key: str) -> Any: ...
    def __setitem__(self, key: str, val: Any) -> None: ...
    def keys(self) -> list[str]: ...
    def dict(self) -> dict[str, Any]: ...

# set by the execution framework (multiprocessing_engine._smash_)
_smash_: Any

# some generic helpers to provide reflection on the execution framework itself (the framework must be setting here the _smash_ object at import)
def getProcessName() -> str:
    """ This is the name of the function which defines the execution code for the worker.
    """
    return _smash_.process_name

def getWorkerNumber() -> int:
    """ This is 0 for supervisor process, 0 for the first worker process, etc.
    """
    return _smash_.process_number

def getCurrentStep() -> int:
    """ Get current step. When worker is waiting at step(N) then it's
    current step is N-1. So until it passes step(1) the current step
    is 0.
    """
    if getWorkerNumber() is None:
        return None # type: ignore[return-value] # never happens: the worker number is always set
    return _smash_.steps[getWorkerNumber()]

def getSharedObject() -> SharedObject:
    """ Get the object which allows to share state between worker processes.
    """
    return _smash_.shared_object

def getNumberOfWorkers() -> int:
    return len(_smash_.workers)

def getTestcaseFilename() -> str:
    """ The absolute path to the file containing current testcase.
    """
    return _smash_.args.test_target
