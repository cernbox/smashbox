#!/usr/bin/env python2
# -*- python -*-
#
# The _open_SmashBox Project.
#
# Author: Jakub T. Moscicki, CERN, 2013
# License: AGPL
#
#$Id: $
#
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Perform internal setup of the environment.
# This is a Copy/Paste logic which must stay in THIS file
def standardSetup():
   import sys, os.path
   # insert the path to cernafs based on the relative position of this scrip inside the service directory tree
   exeDir = os.path.abspath(os.path.normpath(os.path.dirname(os.path.dirname(sys.argv[0]))))
   pythonDir = os.path.join(os.path.dirname(exeDir), 'python' )
   sys.path.insert(0, pythonDir)
   import smashbox.setup
   smashbox.setup.standardSetup(sys.argv[0]) # execute a setup hook

standardSetup()
del standardSetup
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

# all internal symbols start with _smash_
# other symbols defined in this file are available in the user's test scripts


# obsolete to be removed
def log(*args,**kwds):
    import time
    print time.ctime(),_smash_.process_name,(" ".join([str(s) for s in args]))%kwds

#import shelve

class _smash_SmashSharedObject:
    """ A bunch of shared attributes stored in a directory as separate files.
    """

    def __init__(self, d):
        self._dir = d
        self._makedir()

    def _makedir(self):
        try:
            os.makedirs(self._dir)
        except OSError, x:
            import errno
            if x.errno != errno.EEXIST:
                raise

    def __getitem__(self, key):
        self._makedir()
        import pickle
        try:
            return pickle.load(file(os.path.join(self._dir, '_attr_' + key)))
        except Exception, x:
            logger.debug(x)
            raise AttributeError(x)

    def __setitem__(self, key, val):
        self._makedir()
        import pickle
        import time
        tmp_name = os.path.join(self._dir, 'tmp.%s.%s._attr_%s' % (os.getpid(), time.time(), key))
        dest_name = os.path.join(self._dir, '_attr_' + key)
        pickle.dump(val, file(tmp_name, 'w'))

        import shutil
        shutil.move(tmp_name, dest_name)

    def keys(self):
        import glob
        self._makedir()
        attrs = [os.path.basename(a)[len('_attr_'):] for a in glob.glob(os.path.join(self._dir, '_attr_*'))]
        return attrs

    def dict(self):
        keys = {}
        for a in self.keys():
            keys[a] = self[a]
        return keys

    def __str__(self):
        return repr(self.dict())

class _smash_:
    """ Internals of the stepper synchronization framework. This class
    is merely a namespace to avoid polluting global namespace of
    user's test scripts.
    """

    # all the rest of attributes are internal -- accessors for process_name and common_dict are defined in utilities

    process_name = None
    process_number = 0
    
    DEBUG = False

    # this is a hardcoded maximum number of steps
    N_STEPS = 100
    
    workers = []
    all_procs = []

    @staticmethod
    def supervisor(steps):

        import time
        #print "SU",steps
        #print 'SU',[s for s in steps]

        if _smash_.DEBUG:
            log('start',_smash_.supervisor_step.value,_smash_.steps)

        while _smash_.supervisor_step.value < _smash_.N_STEPS-1:
            while 1:
                time.sleep(0.01)
                #print [s for s in steps]
                passed = all([_smash_.steps[i]>_smash_.supervisor_step.value for i in range(len(_smash_.steps))])
                #print 'passed',supervisor_step.value,passed
                if passed:
                    break

            #print "supervisor step completed:",supervisor_step.value,steps

            _smash_.supervisor_step.value += 1

        

        if _smash_.DEBUG:
            log('stop',_smash_.supervisor_step.value,_smash_.steps)

    @staticmethod
    def _step(i,wi,message):
        import time
        _smash_.steps[wi] = i

        def supervisor_status():
            return "(supervisor_step="+str(_smash_.supervisor_step.value)+" worker_steps="+str(_smash_.steps)+")"

        if _smash_.DEBUG:
            logger.debug('step %d waiting (wi=%d) %s'%(i,wi,supervisor_status()))
        while _smash_.supervisor_step.value<i:
            time.sleep(0.01)

        if _smash_.DEBUG:
            logger.debug('step %d entered (wi=%d) %s'%(i,wi,supervisor_status()))

        if message is not None:
            sep='*'*80
            logger.info( 'entering new step \n'+sep+'\n'+'(%d) %s:  %s\n'%(i,_smash_.process_name,message.upper())+sep)

    @staticmethod
    def worker_wrap(wi,f,fname):
        if fname is None:
            fname = f.__name__
        _smash_.process_name=fname
        _smash_.process_number = wi
        def step(i,message=""):
            _smash_._step(i,wi,message)
        try:
            try:
                f(step)
            except Exception,x:
                import traceback
                logger.fatal("Exception occured: %s \n %s", x,traceback.format_exc())
                import sys
                sys.exit(1)
        finally:
            # worker finish
            step(_smash_.N_STEPS-1,None) # don't print any message

            import smashbox.utilities
            if smashbox.utilities.reported_errors:
               logger.error('%s error(s) reported',len(smashbox.utilities.reported_errors))
               import sys
               sys.exit(2)
                  

    @staticmethod
    def run():
        """ Lunch worker processes and the supervisor loop. Block until all is finished.
        """
        from multiprocessing import Process, Manager

        import smashbox.utilities
        smashbox.utilities.setup_test()        

        manager = Manager()

        _smash_.shared_object = _smash_SmashSharedObject(os.path.join(config.rundir,'_shared_objects'))
        
        #_smash_.shared_object = shelve.open(os.path.join(config.rundir,'_shared_objects.shelve'))

        #print "SUPERVISOR NAMESPACE",_smash_.shared_object.__dict__
        
        _smash_.supervisor_step = manager.Value('i',0)

        _smash_.process_name = "supervisor"

        _smash_.steps = manager.list([0 for x in range(len(_smash_.workers))])

        # first worker => process number == 0
        for i,f_n in enumerate(_smash_.workers):
            f = f_n[0]
            fname = f_n[1]
            p = Process(target=_smash_worker_starter,args=(i,f,fname,_smash_.shared_object,_smash_.steps,_smash_.supervisor_step))
            p.start()
            _smash_.all_procs.append(p)

        _smash_.supervisor(_smash_.steps)

        for p in _smash_.all_procs:
            p.join()

        smashbox.utilities.finalize_test()

        for p in _smash_.all_procs:
           if p.exitcode != 0:
              import sys
              sys.exit(p.exitcode)

def add_worker(f,name=None):
    """ Decorator for worker functions in the user-defined test
    scripts: workers execute in parallel and may use 'step(N)' syntax
    to define synchronization points.
    """
    _smash_.workers.append((f,name))
    return f

def _smash_worker_starter(i,funct,fname, shared_object, steps,supervisor_step):
    """ Wrapper of worker_wrap() static method.
        Static methods cannot be used directly as the target
        argument on Windows. Since windows lacks of os.fork(), it is needed
        to ensure that all the arguments to Process.__init__() are picklable.
    """
    logger.debug('Starting worker process %d %s',i,fname or funct.__name__)
    _smash_.shared_object = shared_object
    globals().update(_smash_.shared_object)
    _smash_.steps=steps
    _smash_.supervisor_step=supervisor_step
    _smash_.worker_wrap(i, funct, fname)

### HERE IS THE START OF THE EXECUTABLE SCRIPT

# common initialization
if True:
    import smashbox.compatibility.argparse
    import smashbox.script

    # let's use _smash_ namespace to avoid name pollution...
    _smash_.parser = smashbox.compatibility.argparse.ArgumentParser()
    _smash_.parser.add_argument('test_target')
    _smash_.parser.add_argument('config_blob')

    _smash_.args = _smash_.parser.parse_args()

    # this is OK: config and logger will be visible symbols in the user's test code
    config = smashbox.script.configure_from_blob(_smash_.args.config_blob)

    import smashbox.utilities.reflection
    smashbox.utilities.reflection._smash_ = _smash_

    def getLogger():
       import logging
       import os.path
       import smashbox.utilities
       import sys

       logger = smashbox.script.getLogger('run')

       logger.setLevel(logging.NOTSET)
       
       class SmashFilter(logging.Filter):
          def filter(self, record):
             record.smash_process_name = smashbox.utilities.reflection.getProcessName()
             return True

       logger.addFilter(SmashFilter())

       logdir,logfn = os.path.split(config.rundir)
       try:
          fh = logging.FileHandler(os.path.join(logdir,'log-'+logfn+'.log'),mode='w')
       except IOError:
          print 'File %s cannot be created (missing directory?) ' % (os.path.join(logdir,'log-'+logfn+'.log'))
          sys.exit(-1)

       fh.setLevel(logging.DEBUG)
       # create console handler with a higher log level
       ch = logging.StreamHandler()
       ch.setLevel(config._loglevel) # set the loglevel as defined in the config
       # create formatter and add it to the handlers
       formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(smash_process_name)s - %(message)s')
       ch.setFormatter(formatter)
       fh.setFormatter(formatter)
       # add the handlers to logger
       logger.addHandler(ch)
       logger.addHandler(fh)
       logger.propagate=False
       return logger
    
    try:
       import os
       os.makedirs(config.rundir)
    except OSError,x:
       import errno
       if x.errno != errno.EEXIST:
          raise

    logger = getLogger()

    import logging
    smashbox.script.config_log(logging.DEBUG)

    smashbox.utilities.logger = logger

    # load test case file directly into the global namespace of this script
    execfile(_smash_.args.test_target)

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()  # add support for when a program which uses multiprocessing has been frozen to produce a Windows executable

    logger.info('BEGIN SMASH RUN - rundir: %s', config.rundir)
    # start the framework and dispatch workers
    _smash_.run()


    
    
