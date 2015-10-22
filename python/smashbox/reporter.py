class Reporter:
    """ Report execution state of smashbox.
    """

    def __init__(self):
        self.DEMO=False

    def smashbox_start(self,args,config):
        """
        Smashbox is starting.
        Arguments:
         - args: Namespace object with all the options passed when invoking smash executable
         - config: global configuration object 
        """

        if self.DEMO:
            print "SMASHBOX_START",args,config
            self.config=config

    def smashbox_stop(self):
        """
        Smashbox is about to stop.
        """

        if self.DEMO:
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

        if self.DEMO:
            print "TESTCASE_START",name,loop_i,testset_i,namespace.__doc__

            barename=name.replace("test_","")

            for c in self.config.__dict__:
                if c.startswith(barename+"_"):
                    print c,self.config[c]


    def testcase_stop(self,returncode):
        if self.DEMO:
            print "TESTCASE_STOP",returncode

