import sys

class Reporter:
    """ Report execution state of smashbox.
    """

    def __init__(self):
        self.LOG=True

    def smashbox_start(self,args,config):
        """
        Smashbox is starting.
        Arguments:
         - args: Namespace object with all the options passed when invoking smash executable
         - config: global configuration object 
        """

        if self.LOG:
            print "SMASHBOX_START",args,config
            self.config=config
        curl_check_url(config)
        check_owncloudcmd(config)
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
            print "TESTCASE_START",name,loop_i,testset_i,namespace.__doc__

            barename=name.replace("test_","")

            for c in self.config.__dict__:
                if c.startswith(barename+"_"):
                    print c,self.config[c]


    def testcase_stop(self,returncode):
        if self.LOG:
            print "TESTCASE_STOP",returncode

def check_owncloudcmd(config):
    import subprocess
    from smashbox.utilities import  oc_webdav_url
    #create tmp directory localy
    cmd = 'mkdir -p test'
    process = subprocess.Popen(cmd, shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    process.wait()
    #check if owncloudcmd is correct or if path to owncloudcmd is not correct
    cmd = config.oc_sync_cmd+' '+'tests'+' '+oc_webdav_url('owncloud',remote_folder='', user_num=None)
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
    cmd = 'curl -k %s -X MKCOL %s %s'%(config.get('curl_opts',''),oc_webdav_url(remote_folder='', user_num=None),"")
    process = subprocess.Popen(cmd, shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    process.wait()
    #curl the server 
    cmd = 'curl -s -k %s -XPROPFIND %s'%(config.get('curl_opts',''),oc_webdav_url(remote_folder='', user_num=None))
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
        
    


