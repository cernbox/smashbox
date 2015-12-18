import os,subprocess, datetime,sys

""" dropbox section """
                
class dropbox:
    def __init__(self):
        pass
    
    @staticmethod    
    def reset_owncloud_account(args,config,worker_name):
        return
    
    @staticmethod
    def sync_engine(args,config,worker_name):
        option = args[1]
        stop = True
        finish = False
        exclude = False
        if option:
            for opt in option:
                if opt=='exclude_time':
                    exclude = True
                elif opt=='start_only':
                    stop = False
                elif opt=='finish_only':
                    finish = True
        local_folder = os.path.abspath(os.path.join(config.smashdir,"dropbox-"+worker_name+"/Dropbox/"))
        if finish==False:
            dropbox_restart(config.smashdir, worker_name, local_folder)
        t0 = datetime.datetime.now()
        log = get_running_dropbox(worker_name, config.smashdir)
        if(log != None):
            result = [t0,datetime.datetime.now()]
            if stop==True:
                stop_dropbox(worker_name, config.smashdir)  
            if exclude==True:
                return None
            log_test(config.smashdir,log)
            return result
    @staticmethod    
    def make_workdir(args,config,worker_name):
        import os
        name = args
        if name is ():
            name = worker_name
        d = os.path.abspath(os.path.join(config.smashdir,"dropbox-"+name+"/Dropbox"))
        return d
    
    @staticmethod      
    def curl_check_url(args,config,worker_name):
        pass

def install_dropbox():
    from os.path import expanduser
    import platform,sys
    def is_32bit():
        if (platform.architecture()[0]).find("64") != -1:
            return "x86_64"
        else:
            return "x86"
    home = expanduser("~")
    directory = home + "/.dropbox-dist"
    if not os.path.exists(directory):
        print "%s does not exists, begin installation.."%directory
        dist = 'http://www.dropbox.com/download/?plat=lnx.%s'%is_32bit()
        import subprocess
        subprocess.call(["wget", "-O", "dropbox.tar.gz",dist], cwd=home)
        print "downloaded, unpack"
        subprocess.call(["tar", "-xvzf", "dropbox.tar.gz"], cwd=home)
    print "dropbox installed"
       
def setup_dropbox(smashdir, smash_workers):
    install_dropbox()
    check_if_dropbox_stopped()
    boss="boss"
    clean_directory(smashdir, boss)
    import time
    time.sleep(1)
    start_dropbox(boss, smashdir) 
    if(get_running_dropbox(boss, smashdir) != None):
        clean_directory(smashdir, boss)
        import time
        time.sleep(1)
    
    worker_name_array = []   
    if(get_running_dropbox(boss, smashdir) != None):
        for i,f_n in enumerate(smash_workers):
            f = f_n[0]
            fname = f_n[1]
            if fname is None:
                fname = f.__name__ 
            worker_name_array.append(fname) 
            dropbox_add_workers_to_conf(fname, smashdir)   
        prepare_smashbox(smashdir,worker_name_array,boss)
        
    return worker_name_array
        
        
def prepare_smashbox(smashdir,worker_name_array,boss):
    if(get_running_dropbox(boss, smashdir) != None):
        stop_dropbox(boss, smashdir)#stop_dropbox(boss, smashdir)
        #print "BOSS DONE"
        
    for i in range(0, len(worker_name_array)):
        fname = worker_name_array[i]
        stop_dropbox(fname, smashdir)
    
    check_if_dropbox_stopped()

def clean_directory(smashdir, fname):        
    d = os.path.abspath(os.path.join(smashdir,"dropbox-"+fname+"/Dropbox"))
    cmd = ('rm -rf '+(d+"/*"))
    process = subprocess.Popen(cmd, shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    process.wait()
             
def finish_dropbox():
    print "START FINISHING DROPBOX"
    check_if_dropbox_stopped()

def check_if_dropbox_stopped():
    import time
    t_syncprepare = time_now() 
    running = True
    cmd = os.path.dirname(__file__)+"/./running.sh dropbox"
    status = "Process not running"
    while(running):
        process = subprocess.Popen(cmd, shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        stdout = (process.communicate()[0]).encode('ascii','ignore')
        if((stdout.find(status) != -1)):
            running = False
        else:
            print "some dropbox process is still running"
            time.sleep(1)
    
def stop_dropbox(fname, smashdir):
    import os
    import time
    d = os.path.abspath(os.path.join(smashdir,"dropbox-"+str(fname)))
    cmd = os.path.dirname(__file__)+"/./dropbox.py --set "+d+"/.dropbox stop"  
    process = subprocess.Popen(cmd, shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    process.wait() 
    #print "%s stop dropbox"%fname 


def get_output_from_start(process):
    while True:
        line = process.stdout.readline()
        stdout.append(line)
        print line,
        if line == '' and process.poll() != None:
            break
    
def start_dropbox(fname, smashdir, get_running=True):
    import os
    from os.path import expanduser
    from multiprocessing import Process
    d = os.path.abspath(os.path.join(smashdir,"dropbox-"+str(fname)))
    cmd = os.path.dirname(__file__)+"/./mdroboxinstances.sh "+expanduser("~")+" "+ d
    process = subprocess.Popen(cmd, shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,)
    if(get_running==True):
        import time
        nbsr = NonBlockingStreamReader(process.stdout)
        while True:
            output = nbsr.readline(0.1)
            if output:
                print output
            stdout = check_status_dropbox(str(fname), smashdir)
            if((stdout.find("Up to date") != -1)):
                break
            elif((stdout.find("link") != -1)):
                print stdout
            time.sleep(1)
            
                
        cmd = os.path.dirname(__file__)+"/./dropbox.py --set "+d+"/.dropbox lansync n"  
        process = subprocess.Popen(cmd, shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        process.wait() 

def exclude_dropbox(function, fname, smashdir, directory):
    import os
    d = os.path.abspath(os.path.join(smashdir,"dropbox-"+fname))
    cmd = os.path.dirname(__file__)+"/./dropbox.py --set "+d+"/.dropbox exclude "+function+" "+directory
    process = subprocess.Popen(cmd, shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    process.wait() 
    
    if(get_running_dropbox(fname, smashdir) != None):
        pass

def check_status_dropbox(fname, smashdir):
    import os
    d = os.path.abspath(os.path.join(smashdir,"dropbox-"+str(fname)))
    cmd = os.path.dirname(__file__)+"/./dropbox.py --set "+d+"/.dropbox status"    
    process = subprocess.Popen(cmd, shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    return (process.communicate()[0]).encode('ascii','ignore')
    
def get_running_dropbox(fname, smashdir,status="Up to date"):
    import time
    up_to_date_flag=0
    timeout_flag=0
    stdout_array=[]
    while (up_to_date_flag < 2): 
        stdout = check_status_dropbox(fname, smashdir)
        stdout_array.append("%s - %s"%(time_now(),stdout))
        if((stdout.find(status) != -1)):
            up_to_date_flag += 1
        else:
            up_to_date_flag = 0
        time.sleep(0.01)
        
    return { fname : stdout_array } 
    
def dropbox_restart(smashdir, worker_name, local_folder):
    import time
    def dropbox_check_resume_sync(smashdir, worker_name):
        indexing_flag=True  
        while(indexing_flag):
            stdout = check_status_dropbox(worker_name, smashdir)
            #(stdout.find("Connecting") != -1) or 
            if((stdout.find("Indexing") != -1) or (stdout.find("Downloading") != -1) or (stdout.find("Up to date") != -1)):
                indexing_flag = False
        return time_now()
    #main
    start_dropbox(worker_name, smashdir, get_running=False)
    d = os.path.abspath(os.path.join(smashdir,"dropbox-"+worker_name))
    cmd = os.path.dirname(__file__)+"/./dropbox.py --set "+d+"/.dropbox lansync n"  
    process = subprocess.Popen(cmd, shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    process.wait() 
    cmd = os.path.dirname(__file__)+"/./dropbox.py --set "+d+"/.dropbox exclude remove "+local_folder
    process = subprocess.Popen(cmd, shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    process.wait() 
    indexing = dropbox_check_resume_sync(smashdir, worker_name)
    return indexing
    
def dropbox_add_workers_to_conf(fname, smashdir):
    clean_directory(smashdir, fname) 
    
    if(check_status_dropbox(fname, smashdir).find("Up to date") == -1):
        start_dropbox(fname, smashdir)
    
    if(get_running_dropbox(str(fname), smashdir) != None):
        pass

""" seafile section """

class seafile:
    def __init__(self):
        pass
        
    @staticmethod
    def sync_engine(args,config,worker_name):
        option = args[1]
        stop = True
        finish = False
        exclude = False
        if option:
            for opt in option:
                if opt=='exclude_time':
                    exclude = True
                elif opt=='start_only':
                    stop = False
                elif opt=='finish_only':
                    finish = True
        smashdir = config.smashdir
        if finish==False:
            run_seafile(smashdir, worker_name)
        get_running_seafile(worker_name, smashdir)
        t0 = datetime.datetime.now()
        log = get_synced_seafile(worker_name, smashdir)
        result = [t0,datetime.datetime.now()]
        if stop==True:
            stop_seafile(worker_name, smashdir)
        if exclude==True:
            return None
        log_test(smashdir,log)
        return result
        
    
    @staticmethod    
    def reset_owncloud_account(args,config,worker_name):
        return
          
    @staticmethod    
    def make_workdir(args,config,worker_name):
        import os
        fname = args
        if fname is ():
            fname = worker_name
        workerdir = os.path.abspath(config.smashdir+"/seafile-"+fname)
        return workerdir
    
    @staticmethod      
    def curl_check_url(args,config,worker_name):
        pass 
     
""" P2P SCENARIO - 
class XXXY(XXX):
    @staticmethod
    def sync_engine(args,config,fname):
        option = None
        if args and len(args)>1:
            option = args[1]
        smashdir = config.smashdir
        if option == "multi":
            worker_name_array = config.worker_name_array
            for i in range(0, len(worker_name_array)):
                worker_name = worker_name_array[i]
                if worker_name != fname:
                    run_XXX(smashdir, worker_name)
                    get_synced_XXX(worker_name, smashdir)
        run_XXX(smashdir, fname)
        get_running_XXX(fname, smashdir)
        t0 = datetime.datetime.now()
        log = get_synced_XXX(fname, smashdir)
        sync_exec_time = (datetime.datetime.now()-t0).total_seconds()
        if option == "multi":
            for i in range(0, len(worker_name_array)):
                worker_name = worker_name_array[i] 
                stop_XXX(worker_name, smashdir)
        else:
            stop_XXX(fname, smashdir)
        log_test(smashdir,log)
        return sync_exec_time

"""

def run_seafile(smashdir, fname):
    parentdir = os.path.abspath(smashdir+"/seafile-w-"+fname)
    workerdir = os.path.abspath(smashdir+"/seafile-"+fname)
    workerconfdir = os.path.abspath(smashdir+"/seafile-c-"+fname+"/.ccnet")
    subprocess.call(["./seaf-cli", "start", "-c",workerconfdir], cwd=parentdir)
    
def install_seafile(smashdir,version):
    from os.path import expanduser
    import platform
    def is_32bit():
        if (platform.architecture()[0]).find("64") != -1:
            return "seafile-cli_"+version+"_x86-64"
        else:
            return "seafile-cli_"+version+"_i386"
    home = expanduser("~")
    directory = home + "/seafile-cli-"+version
    if not os.path.exists(directory):
        print "%s does not exists, begin installation.."%directory
        dist = 'https://bintray.com/artifact/download/seafile-org/seafile/%s.tar.gz'%is_32bit()
        subprocess.call(["wget", "-O", "seafile-cli.tar.gz",dist], cwd=home)
        print "downloaded, unpack"
        subprocess.call(["tar", "-xvzf", "seafile-cli.tar.gz"], cwd=home)
        print "seafile installed"
    
    return directory
    
def start_seafile(fname, smashdir,directory,config):
    from os.path import expanduser
    home = expanduser("~")
    parentdir = os.path.abspath(smashdir+"/seafile-w-"+fname)
    workerdir = os.path.abspath(smashdir+"/seafile-"+fname)
    workerconfdir = os.path.abspath(smashdir+"/seafile-c-"+fname+"/.ccnet")
    if not os.path.exists(parentdir):
        subprocess.call(["cp", "-R", directory, parentdir], cwd=home)
        subprocess.call(["mkdir", workerdir], cwd=home) 
        subprocess.call(["mkdir", os.path.abspath(smashdir+"/seafile-c-"+fname)], cwd=home) 
        subprocess.call(["./seaf-cli", "init", "-c",workerconfdir,"-d", parentdir], cwd=parentdir)
        subprocess.call(["./seaf-cli", "start", "-c",workerconfdir], cwd=parentdir)
        while (not os.path.exists(os.path.join(parentdir,'seafile'))) or (not os.path.exists(os.path.join(parentdir,'seafile-data'))):
            subprocess.call(["./seaf-cli", "stop", "-c",workerconfdir], cwd=parentdir)
            subprocess.call(["./seaf-cli", "start", "-c",workerconfdir], cwd=parentdir)
        subprocess.call(["./seaf-cli", "config", "-c",workerconfdir,"-k","disable_verify_certificate","-v","true"], cwd=parentdir)
        subprocess.call(["./seaf-cli", "stop", "-c",workerconfdir], cwd=parentdir)
        subprocess.call(["./seaf-cli", "start", "-c",workerconfdir], cwd=parentdir)
        cmd_arr = ["./seaf-cli", "sync", "-c",workerconfdir, "-l",config.seafile_lib,"-s",config.seafile_server,"-u",config.seafile_user,"-p",config.seafile_password,"-d",workerdir]
        subprocess.call(cmd_arr, cwd=parentdir)
    else:
        subprocess.call(["./seaf-cli", "start", "-c",workerconfdir], cwd=parentdir)
    get_synced_seafile(fname, smashdir)
    stop_seafile(fname, smashdir)

def stop_seafile(fname, smashdir):
    import os
    parentdir = os.path.abspath(smashdir+"/seafile-w-"+fname)
    workerconfdir = os.path.abspath(smashdir+"/seafile-c-"+fname+"/.ccnet")
    subprocess.call(["./seaf-cli", "stop", "-c",workerconfdir], cwd=parentdir)
    

def check_status_seafile(fname, smashdir):
    parentdir = os.path.abspath(smashdir+"/seafile-w-"+fname)
    workerconfdir = os.path.abspath(smashdir+"/seafile-c-"+fname+"/.ccnet")
    cmd = "./seaf-cli status -c "+workerconfdir
    process = subprocess.Popen(cmd, cwd=parentdir, shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    return (process.communicate()[0]).encode('ascii','ignore')

def get_synced_seafile(fname, smashdir):
    import time
    flag = 0 
    stdout_array = []
    while flag<3:
        stdout = check_status_seafile(fname, smashdir)
        stdout_array.append("%s - %s"%(time_now(),stdout))
        if(stdout.find("synchronized") != -1):
            flag+=1
        else:
            flag=0
        time.sleep(0.05)
    return { fname : stdout_array }
    
def get_running_seafile(fname, smashdir):
    flag = 0
    while flag<2:
        if(((check_status_seafile(fname, smashdir)).find("waiting for sync") != -1)):
            flag+=1
    
def setup_seafile(smashdir, smash_workers,config):
    import time
    directory = install_seafile(smashdir,config.version)
    start_seafile("boss", smashdir,directory,config)
    seafile_clean_directory(smashdir, "boss")
    start_seafile("boss", smashdir,directory,config)
    worker_name_array = []   
    for i,f_n in enumerate(smash_workers):
        f = f_n[0]
        fname = f_n[1]
        if fname is None:
            fname = f.__name__ 
        worker_name_array.append(fname) 
        seafile_clean_directory(smashdir, fname)
        start_seafile(fname, smashdir,directory,config) 
    return worker_name_array
    
def seafile_clean_directory(smashdir, fname): 
    workerdir = os.path.abspath(smashdir+"/seafile-"+fname)
    cmd = ('rm -rf '+(workerdir+"/*"))
    process = subprocess.Popen(cmd, shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    process.wait()
""" common functions """

def check_if_stopped(service):
    import time
    t_syncprepare = time_now() 
    running = True
    cmd = os.path.dirname(__file__)+"/./running.sh "+service
    status = "Process not running"
    while(running):
        process = subprocess.Popen(cmd, shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        stdout = (process.communicate()[0]).encode('ascii','ignore')
        if((stdout.find(status) != -1)):
            running = False
        else:
            print "some %s process is still running: %s"%(service,stdout)
            time.sleep(1)

def log_test(smashdir,data):
    import io,json
    with io.open(smashdir+"/engine-log.log", 'a', encoding='utf-8') as file:
        file.write(unicode(json.dumps(data, ensure_ascii=False, indent=4)))
              
def time_now(time_zero=None): 
    import datetime
    if time_zero==None:
        return datetime.datetime.now()
    else:
        return (datetime.datetime.now()-time_zero)  
  
  
from threading import Thread
from Queue import Queue, Empty

class NonBlockingStreamReader:

    def __init__(self, stream):
        '''
        stream: the stream to read from.
                Usually a process' stdout or stderr.
        '''

        self._s = stream
        self._q = Queue()

        def _populateQueue(stream, queue):
            '''
            Collect lines from 'stream' and put them in 'quque'.
            '''

            while True:
                line = stream.readline()
                if line:
                    queue.put(line)
                else:
                    pass

        self._t = Thread(target = _populateQueue,
                args = (self._s, self._q))
        self._t.daemon = True
        self._t.start() #start collecting lines from the stream

    def readline(self, timeout = None):
        try:
            return self._q.get(block = timeout is not None,
                    timeout = timeout)
        except Empty:
            return None
