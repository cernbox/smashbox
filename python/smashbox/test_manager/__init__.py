import smashbox.test_manager.non_native_engine
class Test_Manager:
    """ Manage all the test plugins and handle the test execution
    """

    def __init__(self,name,config):
        self.LOG=True
        self.NON_NATIVE_ENGINE = hasattr(config, "engine")
        self.SNIFFER = hasattr(config, "sniffer")
        self.name = name
        self.config = config
        rm_file_dir(config.smashdir+"/engine-log.log")
        from smashbox.utilities import curl_check_url
        curl_check_url(config)
        import smashbox.test_manager.reporter
        import smashbox.test_manager.sniffer
        self.reporter = smashbox.test_manager.reporter.Reporter(name,config)
        if self.SNIFFER:
            self.sniffer = smashbox.test_manager.sniffer.SnifferThread()
        if self.NON_NATIVE_ENGINE:
            self.engine = getattr(config, "engine")
        
    def setup_test(self, smash_workers, manager):
        if self.LOG:
            print "TESTCASE_START",self.name,self.config.loop_i,self.config.testset_i,self.config.test_doc
        self.reporter.reporter_setup_test(smash_workers,manager)
        if self.NON_NATIVE_ENGINE:
            if self.engine == "dropbox":
                self.worker_name_array=smashbox.test_manager.non_native_engine.setup_dropbox(self.config.smashdir,smash_workers)
            elif self.engine == "seafile":
                setattr(self.config, "version", "4.3.2")
                setattr(self.config, "seafile_lib", "1ba5703c-c3b9-403e-ac3c-dec836076ce2")
                setattr(self.config, "seafile_user", "pimr@dtu.dk")
                setattr(self.config, "seafile_password", "dummy")
                self.worker_name_array=smashbox.test_manager.non_native_engine.setup_seafile(self.config.smashdir,smash_workers,self.config)
                setattr(self.config, "worker_name_array", self.worker_name_array)
        if self.SNIFFER:
            self.sniffer.start()
        
    def finalize_test(self):
        if self.LOG:
            print "TESTCASE_STOP"
        self.reporter.reporter_finalize_test()
        
        if self.SNIFFER:
            test_results = self.reporter.reporter_get_test_results()
            test_results["packet_trace"] = self.sniffer.stop()
            self.sniffer.join()
            self.reporter.reporter_set_test_results(test_results)
        
        self.reporter.reporter_log_results()   
         
        if self.NON_NATIVE_ENGINE:
            if self.engine == "dropbox":
                smashbox.test_manager.non_native_engine.finish_dropbox(self.config.smashdir,self.worker_name_array)
            elif self.engine == "seafile":
                smashbox.test_manager.non_native_engine.finish_seafile(self.config,self.worker_name_array)
    def finalize_step(self,supervisor_step):
        if self.NON_NATIVE_ENGINE:
            if self.engine == "dropbox":
                smashbox.test_manager.non_native_engine.check_if_stopped("dropbox")
            elif self.engine == "seafile":
                smashbox.test_manager.non_native_engine.check_if_stopped("ccnet")
    
    def finalize_worker(self,sync_exec_time_array, reported_errors,fname): 
        self.reporter.reporter_finalize_worker(sync_exec_time_array, reported_errors,fname)

def rm_file_dir(file_path):
    import os, shutil
    if(os.path.exists(file_path)):
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path): 
                shutil.rmtree(file_path)
        except:
            pass   
