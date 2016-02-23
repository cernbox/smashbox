class Test_Reporter:
    """ Manage all the test reportinh plugins and handle the test execution.
        To add new plugins to smashbox, just add required files in the test_manager directory
        and edit this file.
    """

    def __init__(self,name,config,smash_workers,manager):
        self.LOG=False
        self.name = name
        self.config = config
        self.SNIFFER = getattr(config, "sniffer",False)
        self.BACKUPLOG = getattr(config, "backuplog",False)
        import smashbox.test_reporter.reporter, importlib
        self.reporter = smashbox.test_reporter.reporter.Reporter(name,config)
        
        if self.LOG:
            print "TESTCASE_START"
        self.reporter.reporter_setup_test(smash_workers,manager)  
        if self.SNIFFER==True:
            import smashbox.test_reporter.sniffer
            self.sniffer = smashbox.test_reporter.sniffer.SnifferThread()
            self.sniffer.start()
             
    def finalize_test(self):
        if self.LOG:
            print "TESTCASE_STOP"
        self.reporter.reporter_finalize_test()
    
        if self.SNIFFER==True:
            test_results = self.reporter.reporter_get_test_results()
            test_results["packet_trace"] = self.sniffer.stop()
            self.sniffer.join()
            self.reporter.reporter_set_test_results(test_results)
            
        self.reporter.reporter_log_results() 
    
    def finalize_worker(self,sync_exec_time_array, reported_errors,fname): 
        if self.LOG:
            print sync_exec_time_array,reported_errors
            print "FINISHING", fname
        self.reporter.reporter_finalize_worker(sync_exec_time_array, reported_errors,fname)

