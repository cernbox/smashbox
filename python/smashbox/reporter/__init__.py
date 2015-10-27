
class Reporter:
    """ Report execution state of smashbox.
    """

    def __init__(self,name,config):
        self.LOG=True
        self.data = None
        self.shared_result = []
        self.shared_result_i=0
        self.shared_result_j=0
        self.shared_result_workers = {}
        self.config=config
        barename=name.replace("test_","")
        barename=barename.replace(".py","")
        self.test_name = barename
        from smashbox.utilities import curl_check_url
        curl_check_url(config)
        
    def testcase_start(self):
        """
        Testcase is about to start.
        Arguments:
         - name: short name of the testcase 
         - loop_i: loop index or None if not running in the loop
         - testset_i: testset index or None if running with default configuration
         - namespace: access to the testcase module namespace

         Example: 
          try:
           print "Current testset configuration", namespace.testsets[testset_i]
          expect AttributeError:
           print "Testsets not defined"

        """
        barename = self.test_name
        config = self.config
        if self.LOG:
            print "TESTCASE_START",barename,config.loop_i,config.testset_i,config.test_doc
            
        self.resultfile = config.smashdir +"/results-"+config.oc_server+"-"+config.runid
        self.start_date = time_now() 
        scenario = {}
        for c in self.config.__dict__:
            if c.startswith(barename+"_"):
                dict = { c : self.config[c] }
                scenario.update(dict)
        if(scenario=={}):
            scenario = "default"            
        dict = { "scenario": scenario,
                 "scenarioid": config.testset_i,
                 "results": [],
                 "loopid": config.loop_i,
                 "timeid": time_now().strftime("%y%m%d-%H%M%S")
        }
        self.data = append_to_json(dict,barename,self.data,self.config)
        
    def testcase_stop(self):
        if self.LOG:
            print "TESTCASE_STOP"
        dict = { "results" : [] }
        for i in range(0, len(self.shared_result_workers)):
            dict["results"].append(self.get_shared_results())
        dict["total_exec_time"]=str(time_now(self.start_date))
        data = append_to_json(dict,self.test_name,self.data,self.config)
        log_results(data,self.resultfile,self.config,self.test_name)
        #print json.dumps(self.data, ensure_ascii=False, indent=4)
        
    def shared_results_manager(self,manager,fname):
        self.shared_result.append(None)
        shared_result_i=self.shared_result_i
        self.shared_result_workers.update({ fname : shared_result_i })
        self.shared_result[shared_result_i] = manager.dict()
        self.shared_result[shared_result_i]["worker"] = fname
        self.shared_result_i +=1
        #return self.shared_result[shared_result_i]
        
    def get_shared_results(self):
        shared_result_j=self.shared_result_j
        self.shared_result_j +=1
        return eval(str(self.shared_result[shared_result_j]))
    
    def append_results(self,sync_exec_time_array, reported_errors,fname): 
        i = self.shared_result_workers[fname]
        if sync_exec_time_array:
            self.shared_result[i]["sync_time"] = sync_exec_time(sync_exec_time_array)
        else:
            self.shared_result[i]["sync_time"] = '0:00:00.000000'
        if reported_errors:
            self.shared_result[i]["errors"] = reported_errors
            
def sync_exec_time(sync_exec_time_array):
    import datetime 
    if sync_exec_time_array != None:
        exec_time =  sync_exec_time_array[0]
        for i in range(1, len(sync_exec_time_array)):
            sync_exec_time =  sync_exec_time_array[i]
            exec_time = (exec_time + sync_exec_time)
    else:
        exec_time = datetime.timedelta(hours=0, minutes=0, seconds=0, milliseconds=0).total_seconds()
    
    return str(datetime.timedelta(seconds=exec_time))

def log_results(result,resultfile,config,test_name):
    data = get_data_from_json_file(resultfile)
    if data==None:
        #new file
        data = result
    else:
        #file(data) exists
        data = append_to_json(result,test_name,data,config)
    write_to_json_file(data, resultfile)         
        
def time_now(time_zero=None): 
    import datetime
    if time_zero==None:
        return datetime.datetime.now()
    else:
        return (datetime.datetime.now()-time_zero)    

def append_to_json(dict,test_name,data,config):
    import json
    import io
    import os.path
    
    if (data!=None):
        #json exists or log_file appends
        if data.has_key(str(config.oc_server)):
            #append to results from the same server
            serv_dict = data[str(config.oc_server)]
            if(serv_dict.has_key(test_name)):
                #append to the existing test branch
                if(dict.has_key(str(config.oc_server))):
                    #log_file appends
                    data[str(config.oc_server)][test_name].append( dict[str(config.oc_server)][test_name][0] )
                else:
                    #scenario results appends
                    data[str(config.oc_server)][test_name][0].update(dict)            
            else:
                #append new test branch
                if(dict.has_key(str(config.oc_server))):
                    #log_file appends
                    data[str(config.oc_server)][test_name]=[ dict[str(config.oc_server)][test_name][0] ]
                else:
                    #scenario results appends
                    data[str(config.oc_server)][test_name]=[dict]
        else:
            #append to results from the other server
            data.update(dict)
    else:
        #new json 
        data = { config.oc_server: { test_name: [dict] } }
        
    if(not data.has_key("runid")):
        data["runid"] = config.runid    
    return data

def get_data_from_json_file(f_name):
    import json
    import io
    import os
    if(os.path.exists(f_name)):
        with io.open(f_name,'r') as file:
            data = json.load(file)    
        return data  
    
def write_to_json_file(data, file_path):
    import json
    import io
    
    def mkdir_p(filename):
        import os
        try:
            folder=os.path.dirname(filename)  
            if not os.path.exists(folder):  
                os.makedirs(folder)
            return True
        except:
            return False
    
    mkdir_p(file_path)
    with io.open(file_path, 'w', encoding='utf-8') as file:
        file.write(unicode(json.dumps(data, ensure_ascii=False, indent=4)))

