class Test_Reporter:
    """ Manage all the test plugins and handle the test execution.
        To add new plugins to smashbox, just add required files in the test_manager directory
    """

    def __init__(self,name,config):
        self.LOG=True
        self.name = name
        self.config = config
        
    def start_test(self, smash_workers, manager):
        if self.LOG:
            print "TESTCASE_START"
        
    def finalize_test(self):
        if self.LOG:
            print "TESTCASE_STOP"
                
    def finalize_step(self,supervisor_step):
        pass
    
    def finalize_worker(self,sync_exec_time_array, reported_errors,fname): 
        if self.LOG:
            print "FINISHING", fname

