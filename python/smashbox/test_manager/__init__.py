
class Test_Manager:
    """ Manage all the test plugins and handle the test execution
    """

    def __init__(self,name,config):
        self.LOG=True
        self.name = name
        self.config = config
        from smashbox.utilities import curl_check_url
        curl_check_url(config)
        import smashbox.test_manager.reporter
        self.reporter = smashbox.test_manager.reporter.Reporter(name,config)
        
    def setup_test(self):
        if self.LOG:
            print "TESTCASE_START",self.name,self.config.loop_i,self.config.testset_i,self.config.test_doc
        self.reporter.reporter_setup_test()
    
    def finalize_test(self):
        if self.LOG:
            print "TESTCASE_STOP"
        self.reporter.reporter_finalize_test()
        
    def setup_worker(self,manager,fname):
        self.reporter.reporter_setup_worker(manager,fname)
        
    def finalize_step(self,supervisor_step):
        pass
    
    def finalize_worker(self,sync_exec_time_array, reported_errors,fname): 
        self.reporter.reporter_finalize_worker(sync_exec_time_array, reported_errors,fname)
            

