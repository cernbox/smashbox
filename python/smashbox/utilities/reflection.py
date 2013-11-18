# ##### REFLECTION ############

# some generic helpers to provide reflection on the execution framework itself (the framework must be setting here the _smash_ object at import)
def getProcessName():
    """ This is the name of the function which defines the execution code for the worker.
    """
    return _smash_.process_name

def getWorkerNumber():
    """ This is 0 for supervisor process, 0 for the first worker process, etc.
    """
    return _smash_.process_number

def getCurrentStep():
    """ Get current step. When worker is waiting at step(N) then it's
    current step is N-1. So until it passes step(1) the current step
    is 0.
    """
    if getWorkerNumber() is None:
        return None
    return _smash_.steps[getWorkerNumber()]

def getSharedObject():
    """ Get the object which allows to share state between worker processes.
    """
    return _smash_.shared_object

def getNumberOfWorkers():
    return len(_smash_.workers)
