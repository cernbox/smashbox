import smashbox.test_manager.non_native_engine
class Test_Manager:
    """ Manage all the test plugins and handle the test execution
    """

    def __init__(self,name,config):
        self.LOG=True
        self.NON_NATIVE_ENGINE = hasattr(config, "engine")
        self.name = name
        self.config = config
        from smashbox.utilities import curl_check_url
        curl_check_url(config)
        import smashbox.test_manager.reporter
        self.reporter = smashbox.test_manager.reporter.Reporter(name,config)
        
    def setup_test(self, smash_workers, manager):
        if self.LOG:
            print "TESTCASE_START",self.name,self.config.loop_i,self.config.testset_i,self.config.test_doc
        self.reporter.reporter_setup_test(smash_workers,manager)
        if self.NON_NATIVE_ENGINE:
            self.worker_name_array=smashbox.test_manager.non_native_engine.setup_dropbox(self.config.smashdir,smash_workers)
    
    def finalize_test(self):
        if self.LOG:
            print "TESTCASE_STOP"
        self.reporter.reporter_finalize_test()
        if self.NON_NATIVE_ENGINE:
            smashbox.test_manager.non_native_engine.finish_dropbox(self.config.smashdir,self.worker_name_array)
        
    def finalize_step(self,supervisor_step):
        if self.NON_NATIVE_ENGINE:
            smashbox.test_manager.non_native_engine.check_if_dropbox_stopped()
        pass
    
    def finalize_worker(self,sync_exec_time_array, reported_errors,fname): 
        self.reporter.reporter_finalize_worker(sync_exec_time_array, reported_errors,fname)
            

