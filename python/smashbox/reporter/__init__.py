import sys

class Reporter:
    """ Report execution state of smashbox.
    """

    def __init__(self):
        self.LOG=True
        self.data = None
        self.shared_result = []
        self.shared_result_i=0
        self.shared_result_j=0
        self.shared_result_workers = {}
        
    def smashbox_start(self,config):
        """
        Smashbox is starting.
        Arguments:
         - args: Namespace object with all the options passed when invoking smash executable
         - config: global configuration object 
        """

        if self.LOG:
            print "SMASHBOX_START",config
            self.config=config
        self.resultfile = config.smashdir +"/results-"+config.oc_server+"-"+config.runid
        self.start_date = time_now()    
    def smashbox_stop(self):
        """
        Smashbox is about to stop.
        """

        if self.LOG:
            print "SMASHBOX_STOP"

    
    def testcase_start(self,name,loop_i,testset_i,namespace):
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
        
        if self.LOG:
            print "TESTCASE_START",name,loop_i,testset_i,namespace

        barename=name.replace("test_","")
        barename=barename.replace(".py","")
        self.test_name = barename
        scenario = {}
        for c in self.config.__dict__:
            if c.startswith(barename+"_"):
                dict = { c : self.config[c] }
                scenario.update(dict)
        if(scenario=={}):
            scenario = "default"            
        dict = { "scenario": scenario,
                 "scenarioid": testset_i,
                 "results": [],
                 "loopid": loop_i,
                 "timeid": time_now().strftime("%y%m%d-%H%M%S")
        }
        self.data = append_to_json(dict,barename,self.data,self.config)
        
        #curl_check_url(self.config)
        #check_owncloudcmd(self.config)
        
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
        exec_time = datetime.datetime.strptime(exec_time, '%H:%M:%S.%f')
        for i in range(1, len(sync_exec_time_array)):
            sync_exec_time =  sync_exec_time_array[i]
            sync_exec_time = datetime.datetime.strptime(sync_exec_time, '%H:%M:%S.%f')
                    #exec_time = datetime.datetime.strptime(data[0], '%H:%M:%S.%f')
            sync_exec_time = datetime.timedelta(hours=sync_exec_time.hour, minutes=sync_exec_time.minute, seconds=sync_exec_time.second, milliseconds=(sync_exec_time.microsecond/1000))
            exec_time = datetime.timedelta(hours=exec_time.hour, minutes=exec_time.minute, seconds=exec_time.second, milliseconds=(exec_time.microsecond/1000))
            exec_time = (exec_time + sync_exec_time)
    else:
        exec_time = datetime.timedelta(hours=0, minutes=0, seconds=0, milliseconds=0)
    return str(exec_time)       

def log_results(result,resultfile,config,test_name):
    data = get_data_from_json_file(resultfile)
    if data==None:
        #new file
        data = result
    else:
        #file(data) exists
        data = append_to_json(result,test_name,data,config)
    write_to_json_file(data, resultfile)        
            
def check_owncloudcmd(config):
    import subprocess
    from smashbox.utilities import  oc_webdav_url
    #create tmp directory localy
    cmd = 'mkdir -p test'
    process = subprocess.Popen(cmd, shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    process.wait()
    #check if owncloudcmd is correct or if path to owncloudcmd is not correct
    cmd = config.oc_sync_cmd+' '+'tests'+' '+oc_webdav_url('owncloud',remote_folder='test', user_num=None)
    process = subprocess.Popen(cmd, shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    stdout,stderr = process.communicate()
    if((stderr).find("not found") != -1):
        print stderr
        sys.exit()
    #delete tmp directory localy
    cmd = 'rm -rf test'
    process = subprocess.Popen(cmd, shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    process.wait()
    
def curl_check_url(config):
    import subprocess
    from smashbox.utilities import  oc_webdav_url
    #create oc_server_folder 
    cmd = 'curl -k %s -X MKCOL %s %s'%(config.get('curl_opts',''),oc_webdav_url(remote_folder='test', user_num=None),"")
    process = subprocess.Popen(cmd, shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    process.wait()
    #curl the server 
    cmd = 'curl -s -k %s -XPROPFIND %s'%(config.get('curl_opts',''),oc_webdav_url(remote_folder='test', user_num=None))
    process = subprocess.Popen(cmd, shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    stdout,stderr = process.communicate()
    import xml.etree.ElementTree as ET
    exit_flag = False
    if len(stdout) and stderr=='':
        #stdout found, no errors
        try:
            root = ET.fromstring(stdout)
            for i in range(0, len(root)):
                child=root[i]
                if len(child) and i==0 and (child.tag).find("response") != -1:
                    #standard output of webdav
                    print "SMASHBOX_CHECK OK: %s"%child[0].text
                else:
                    if((child.tag).find("message") != -1):
                        print "\nSMASHBOX_CHECK WARNING: %s"%child.text
                        #some server error, print message
                        exit_flag = True
                    elif((child.tag).find("exception") != -1):
                        #some server error, print reason
                        print "\nSMASHBOX_CHECK WARNING: %s"%child.text
                        exit_flag = True
        except Exception, e:
            exit_flag = True
            print e
            print stdout
        finally:
            #exit if needed
            if(exit_flag):
                sys.exit()
                
    else:
        #critical error, check the configuration
        cmd = 'curl -I -s -k %s'%(oc_webdav_url(remote_folder='', user_num=None))
        process = subprocess.Popen(cmd, shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        print process.communicate()
        print "SMASHBOX_CHECK ERROR: "+(stderr)+"\n CHECK CONFIGURATION - oc_root, oc_ssl_enabled, oc_server, oc_server_shell_cmd etc."
        sys.exit()
        
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
