import io,subprocess,os

class InfluxDBClient:
    import io,subprocess,os
    def __init__(self,config):
        self.tmp_file = "measurement.txt"
        SERVER_URL = config.remote_storage_server
        DB_NAME = config.remote_database
        DB_USER = config.remote_storage_user
        DB_PASSWORD = config.remote_storage_password
        self.CURL_CMD = "curl -i -u %s:%s -XPOST %s/write?db=%s --data-binary @%s"%(DB_USER,DB_PASSWORD,SERVER_URL,DB_NAME,self.tmp_file)
        self.result_array = [[]]
        self.result_array_len = 0
        self.tmp_result_array_len = 0
        
    def initialize_keys(self,engine, server_name, scenario):
        self.tags = ["engine=%s"%engine,"server_name=%s"%server_name]
        
        if scenario != "default":
            for the_key, the_value in (scenario).iteritems():
                self.tags.append(str(the_key)+"="+str(the_value))
            
    def write(self,measurement_name,tags,value,timestamp):
        CURL_TAG = ""
        tags = tags + self.tags
        for i in range(0, len(tags)):
            CURL_TAG+=",%s"%tags[i]
        data_binary = "%s%s value=%s %s000\n"%(measurement_name,CURL_TAG,value,timestamp)
        if(self.tmp_result_array_len>50000):
            self.result_array.append([])
            self.result_array_len += 1 
            self.tmp_result_array_len = 0
        self.result_array[self.result_array_len].append(data_binary)
        self.tmp_result_array_len += 1
       
    def send(self):
        try:
            for i in range(0, self.result_array_len+1):    
                with io.open(self.tmp_file,'w', encoding='utf-8') as file_write:
                    result_string = ''.join(self.result_array[i])
                    file_write.write(unicode(result_string))
                    
                with open(os.devnull, "w") as fnull:
                    #process = subprocess.Popen(self.CURL_CMD, shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                    #output = process.communicate()
                    #print (output[0]).encode('ascii','ignore')
                    #print (output[1]).encode('ascii','ignore')
                    subprocess.call(self.CURL_CMD, shell=True,stdout=fnull,stderr=fnull)
        except Exception,e:
            print e
              
                  
class Reporter:
    """ Report execution state of smashbox.
    """
    
    def __init__(self,name,config):
        self.data = None
        self.shared_result = []
        self.shared_result_i=0
        self.shared_result_j=0
        self.shared_result_workers = {}
        self.config=config
        barename=name.replace("test_","")
        barename=barename.replace(".py","")
        self.test_name = barename
    
    def reporter_setup_test(self,smash_workers,manager):
        import datetime
        #prepare configurations
        barename = self.test_name
        config = self.config
        self.resultfile = config.smashdir +"/results-"+config.oc_server+"-"+config.runid
        self.start_date = time_now() 
        #log
        #prepare dictionary for the test results    
        scenario = {}
        for c in self.config.__dict__:
            if c.startswith(barename+"_"):
                dict = { c : self.config[c] }
                scenario.update(dict)
        if(scenario=={}):
            scenario = "default"
            
        if(hasattr(config, "engine")):
            engine = config.engine
        else:
            engine = "owncloud"
                             
        dict = { "scenario": scenario,
                 "scenarioid": config.testset_i,
                 "results": [],
                 "engine": engine,
                 "timeid": (datetime.datetime.now()).strftime('%s%f')
        }
        self.data = append_to_json(dict,barename,self.data,self.config)
        for i,f_n in enumerate(smash_workers):
            f = f_n[0]
            fname = f_n[1]
            if fname is None:
                fname = f.__name__
            self.shared_result.append(None)
            shared_result_i=self.shared_result_i
            self.shared_result_workers.update({ fname : shared_result_i })
            self.shared_result[shared_result_i] = manager.dict()
            self.shared_result[shared_result_i]["worker"] = fname
            self.shared_result_i +=1
    
    def reporter_log_results(self):
        result = append_to_json(self.test_result_dict,self.test_name,self.data,self.config)
        try:
            if getattr(self.config, "remote")=="true":
                self.remote_storage(result)
        except Exception,e:
            print "%s: continue and save results localy"%e
            self.local_storage(result)         
    
    def reporter_finalize_test(self):
        dict = { "results" : [] }
        for i in range(0, len(self.shared_result_workers)):
            dict["results"].append(self.get_shared_results())
        dict["total_exec_time"]=(time_now(self.start_date)).total_seconds()
        self.test_result_dict = dict
    
    def reporter_get_test_results(self):  
        return self.test_result_dict
    
    def reporter_set_test_results(self, dict):  
        self.test_result_dict = dict
       
    def get_shared_results(self):
        shared_result_j=self.shared_result_j
        self.shared_result_j +=1
        return eval(str(self.shared_result[shared_result_j]))
    
    def reporter_finalize_worker(self,sync_exec_time_array, reported_errors,fname): 
        i = self.shared_result_workers[fname]
        if sync_exec_time_array:
            self.shared_result[i]["sync_time"] = sync_exec_time(sync_exec_time_array)
            self.shared_result[i]["sync_time_intervals"] = set_sync_intervals(sync_exec_time_array)
        else:
            self.shared_result[i]["sync_time"] = 0
            self.shared_result[i]["sync_time_intervals"] = []
        if reported_errors:
            self.shared_result[i]["errors"] = reported_errors
    
    def remote_storage(self,result):
        
        def process_packets():
            
            def in_sync_period(packet_time):
                for i in range(0, len(test_results)):
                    sync_array = test_results[i]["sync_time_intervals"]
                    for j in range(0, len(sync_array)):
                        if packet_time >= sync_array[j][0] and packet_time <= sync_array[j][1]:
                            return True
                return False    
            for j in range(0, len(packet_trace)):
                packet = packet_trace[j]
                send_packet_tag = []
                send_packet_tag.append("ip=%s"%packet["ip"])
                send_packet_tag.append("incoming=%s"%packet["incoming"])
                if in_sync_period(packet["time"]):
                    send_packet_tag.append("sync_packet=true")
                else:
                    send_packet_tag.append("sync_packet=false")
                
                influxdb_client.write(("%s-pkt"%RUNID), send_packet_tag, packet["size"],str(packet["time"])) 
            TIMEID = str(packet["time"])
            
        def process_results():
            total_sync_time = 0
            sync_time_array = []
            for i in range(0, len(test_results)):
                test_result = test_results[i]
                err_tags = [("worker_name=%s"%test_result["worker"])]
                if test_result.has_key("errors"): 
                    import urllib
                    err_tags.append("errors=%s"%urllib.quote(str(test_result["errors"])))
                    error_flag = 1
                else:
                    error_flag = 0
                influxdb_client.write(("%s-err"%RUNID), err_tags, str(error_flag) ,TIMEID)
                
            if error_flag==0:    
                for j in range(0, len(test_results)):
                    test_result = test_results[j]
                    if(test_result["sync_time"]!=0):
                        total_sync_time += test_result["sync_time"]
                        influxdb_client.write(("%s-syn"%RUNID), [("worker_name=%s"%test_result["worker"])], test_result["sync_time"] ,TIMEID)     
                #total sync has to be calculated due to grouping of values at grafana, no option to calculate it in query 
                if(total_sync_time!=0):
                    influxdb_client.write(("%s-total-syn"%RUNID),[],total_sync_time,TIMEID)
                    influxdb_client.write(("%s-total-exec"%RUNID),[],TOTAL_EXEC,TIMEID)
            
        influxdb_client = InfluxDBClient(self.config)    
        SERVER_NAME = self.config.oc_server
        TEST_NAME=self.test_name
        RUNID = result["runid"]+"-"+TEST_NAME
        result_raw = result[SERVER_NAME][TEST_NAME][0] #function remote_storage is called always after the test, so it is only result avaiable at that iteration
        
        test_results = result_raw.pop("results")
        TIMEID = str(result_raw["timeid"])
        TOTAL_EXEC = result_raw["total_exec_time"]
         
        influxdb_client.initialize_keys(result_raw["engine"], SERVER_NAME, result_raw["scenario"])
        
        if result_raw.has_key("packet_trace"):
            packet_trace = result_raw["packet_trace"]
            print len(packet_trace)
            process_packets()
        process_results()
        influxdb_client.send()
        
    def local_storage(self,result):
        data = get_data_from_json_file(self.resultfile)
        if data==None:
            #new file
            data = result
        else:
            #file(data) exists
            data = append_to_json(result,self.test_name,data,self.config)
        write_to_json_file(data, self.resultfile) 

def set_sync_intervals(sync_exec_time_array):
    import calendar
    sync_intervals = []
    for i in range(1, len(sync_exec_time_array)):
        if sync_exec_time_array[i]!=None:
            t0=int((sync_exec_time_array[i][0]).strftime('%s%f'))
            t1=int((sync_exec_time_array[i][1]).strftime('%s%f'))
            sync_intervals.append([t0,t1])
    return sync_intervals  

def sync_exec_time(sync_exec_time_array):
    import datetime 
    if sync_exec_time_array[0]!=None:
        exec_time = (sync_exec_time_array[0][1]-sync_exec_time_array[0][0]).total_seconds()
    else:
        exec_time = 0
    for i in range(1, len(sync_exec_time_array)):
        if sync_exec_time_array[i]!=None:
            sync_exec_time =  (sync_exec_time_array[i][1]-sync_exec_time_array[i][0]).total_seconds()
            exec_time = (exec_time + sync_exec_time)
    
    return exec_time     
        
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

def get_data_from_json_file(file_path):
    import json
    import io
    import os
    if(os.path.exists(file_path)):
        with io.open(file_path,'r') as file:
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