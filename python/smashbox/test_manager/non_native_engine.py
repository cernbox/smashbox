import os,subprocess, datetime

class dropbox:
    def __init__(self):
        pass
    
    @staticmethod    
    def reset_owncloud_account(args,config,worker_name):
        return
    
    @staticmethod
    def sync_engine(args,config,worker_name):
        local_folder = os.path.abspath(os.path.join(config.smashdir,"dropbox-"+worker_name+"/Dropbox/"))
        dropbox_restart(config.smashdir, worker_name, local_folder)
        t0 = datetime.datetime.now()
        if(get_running_dropbox(worker_name, config.smashdir, print_status = True)):
            sync_exec_time = (datetime.datetime.now()-t0).total_seconds() 
            stop_dropbox(worker_name, config.smashdir)  
        return sync_exec_time
          
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
          
def time_now(time_zero=None): 
    import datetime
    if time_zero==None:
        return datetime.datetime.now()
    else:
        return (datetime.datetime.now()-time_zero) 

def install_dropbox():
    from os.path import expanduser
    import platform,sys
    def is_32bit():
        if ((platform.architecture()[0]).find("32") != -1):
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
    rm_file_dir("test.conf")
    boss="boss"
    clean_directory(smashdir, boss)
    import time
    time.sleep(1)
    start_dropbox(boss, smashdir) 
    if(get_running_dropbox(boss, smashdir)):
        clean_directory(smashdir, boss)
        import time
        time.sleep(1)
    
    worker_name_array = []   
    if(get_running_dropbox(boss, smashdir)):
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
    if(get_running_dropbox(boss, smashdir)):
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
             
def finish_dropbox(smashdir,worker_name_array):
    #print "START FINISHING DROPBOX"
    for i in range(0, len(worker_name_array)):
        fname = worker_name_array[i]
        start_dropbox(fname, smashdir)
        clean_directory(smashdir, fname) 
        if(get_running_dropbox(str(fname), smashdir)):
            stop_dropbox(fname, smashdir)
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
    
def start_dropbox(fname, smashdir, get_running=True):
    import os
    d = os.path.abspath(os.path.join(smashdir,"dropbox-"+str(fname)))
    cmd = os.path.dirname(__file__)+"/./mdroboxinstances.sh "+ d
    process = subprocess.Popen(cmd, shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if(get_running and get_running_dropbox(str(fname), smashdir)):
        cmd = os.path.dirname(__file__)+"/./dropbox.py --set "+d+"/.dropbox lansync n"  
        process = subprocess.Popen(cmd, shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        process.wait() 

def exclude_dropbox(function, fname, smashdir, directory):
    import os
    d = os.path.abspath(os.path.join(smashdir,"dropbox-"+fname))
    cmd = os.path.dirname(__file__)+"/./dropbox.py --set "+d+"/.dropbox exclude "+function+" "+directory
    process = subprocess.Popen(cmd, shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    process.wait() 
    
    if(get_running_dropbox(fname, smashdir)):
        pass

def check_status_dropbox(fname, smashdir):
    import os
    d = os.path.abspath(os.path.join(smashdir,"dropbox-"+str(fname)))
    cmd = os.path.dirname(__file__)+"/./dropbox.py --set "+d+"/.dropbox status"    
    process = subprocess.Popen(cmd, shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    return (process.communicate()[0]).encode('ascii','ignore')
    
def get_running_dropbox(fname, smashdir,status="Up to date", print_status = False):
    import time
    up_to_date_flag=0
    timeout_flag=0
    while (up_to_date_flag < 2): 
        stdout = check_status_dropbox(fname, smashdir)
        if(print_status):
            print "%s: %s"%(fname,stdout)
        if((stdout.find(status) != -1)):
            up_to_date_flag += 1
        else:
            up_to_date_flag = 0
            timeout_flag +=1
            if(timeout_flag>10000):
                e = ("%s get running timeout - ignore, not important!"%(fname))
                raise Exception, e
        time.sleep(0.01)
    return True   
    
def dropbox_restart(smashdir, worker_name, local_folder):
    import time
    def dropbox_check_resume_sync(smashdir, worker_name):
        indexing_flag=True  
        indexing_timeout=0
        while(indexing_flag):
            stdout = check_status_dropbox(worker_name, smashdir)
            #(stdout.find("Connecting") != -1) or 
            if((stdout.find("Indexing") != -1) or (stdout.find("Downloading") != -1) or (stdout.find("Up to date") != -1)):
                indexing_flag = False
            else:
                indexing_timeout+=1
                if(indexing_timeout==1000):
                    #print "indexing timeout"
                    return False
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
    if(indexing==False):
        raise Exception, "indexing timeout"
    else:
        return indexing
    
def dropbox_add_workers_to_conf(fname, smashdir):
    clean_directory(smashdir, fname) 
    
    if(check_status_dropbox(fname, smashdir).find("Up to date") == -1):
        start_dropbox(fname, smashdir)
    
    if(get_running_dropbox(str(fname), smashdir)):
        pass