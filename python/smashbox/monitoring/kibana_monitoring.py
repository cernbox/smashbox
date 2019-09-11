from smashbox.utilities import ocsync_version
import socket
#import requests
#import json
import platform

class StateMonitor:

    def __init__(self,manager, args, config):
        """
        Initialize the test state with initial information
        """
        self.kibana_monitoring_host = config.get('kibana_monitoring_host', None)
        self.kibana_monitoring_port = config.get('kibana_monitoring_port', 10012)

        self._test_ignored = config.get('_test_ignored', None)

        if not self.kibana_monitoring_host:
            self.worker_results = None
            return

        testname = (str(args.test_target).split("test_"))[-1].split(".")[0]
        self.worker_results = manager.Queue()
        self.test_results = dict()
        self.runtimestamp = config._run_timestamp

        # extract test parameters
        parameters = []
        param = {}
        for c in config.__dict__:
            if c.startswith(testname + "_"):
                param[str((c.replace(testname + "_", "")))] = config[c]
                parameters.append(param)
                print c, config[c]

        if platform.system() == 'Linux':
            distribution = platform.dist()
            #client_platform = str(platform.system()) + "-" + str(distribution[0])+str(distribution[1])
            distr = tuple([str(x) for x in distribution[1].split(".")])
            client_platform = str(distribution[0])+distr[0]
        elif platform.system() == 'Darwin':
            ver = platform.mac_ver()
            client_platform = "OSX" + str(ver[0])
        else:
            client_platform = platform.system() + platform.release()


        # initialize json to be sent for monitoring
        self.test_results = {"activity": config.kibana_activity, 'test_name': testname, 'hostname': socket.gethostname(),'backend': config.instance_name,
                             'oc_client_version': str(str(ocsync_version())[1:-1].replace(", ",".")),'oc_server': config.oc_server.split("/")[0],'platform': client_platform,
                             'parameters':parameters,'parameters_text':str(parameters),'errors': [],'errors_text': "",'success': [],
                             'total_errors':0,'total_success':0, 'qos_metrics': [],'ignoredFailures':0,'passed': 0,'failed': 0, 'test_ignored': self._test_ignored }


    def join_worker_results(self):
        """
        Join partial worker tests results information. The partial results are stored in queue (FIFO order)
        """
        if not self.kibana_monitoring_host:
            return

        partial_results = self.worker_results.get()
        if(partial_results[0]): self.test_results['errors'].append(partial_results[0])

        self.test_results['total_errors']+=len(self.test_results['errors'])


    def test_finish(self):
        """"
        Check if the test has passed and publish results
        """
        if not self.kibana_monitoring_host:
            return

        if self._test_ignored is None: # we just want to track tests that we considered fixed
            if(self.test_results['total_errors']>=1): # A subtest is considered failed with one or more errors
                self.test_results['passed'] = 0
                self.test_results['failed'] = 1
            else:
                self.test_results['failed'] = 0
                self.test_results['passed'] = 1
        else:
            self.test_results['ignoredFailures'] = 1 # if the test is ignored we put it in a separate counter

        json_results = self.get_json_results()

        self.send_and_check(json_results)


    def get_json_results(self):
        """
        Saved results in a dictionary to be able to convert them in a json format
        """
        if (self.test_results['errors']): self.test_results['errors_text'] = str(self.test_results['errors'])
        json_result = [{'producer':"cernbox", 'type':"ops", 'hostname': socket.gethostname(), 'timestamp':int(round(self.runtimestamp * 1000)), "data":self.test_results}]
        return json_result

    # --------------------------------------------------------------------------------
    # Send metrics to kibana-monit central service
    #   Report tests results and statistics to the kibana monitoring dashboard
    # --------------------------------------------------------------------------------

    def send(self,document):
        import requests, json
        return requests.post(self.kibana_monitoring_host + ":" + self.kibana_monitoring_port + "/", data=json.dumps(document),
                             headers={"Content-Type": "application/json; charset=UTF-8"})

    def send_and_check(self,document, should_fail=False):
        response = self.send(document)
        assert (
        (response.status_code in [200]) != should_fail), 'With document: {0}. Status code: {1}. Message: {2}'.format(
            document, response.status_code, response.text)
