from smashbox.utilities import ocsync_version
import socket
#import requests
#import json
import platform
from requests.auth import HTTPBasicAuth
import time
import urllib3

import argparse
import queue
import multiprocessing.managers
from typing import Any

import requests

from smashbox.script import Configuration

class StateMonitor:

    worker_results: 'queue.Queue[list[list[str]]] | None'
    test_results: dict[str, Any]
    runtimestamp: float

    def __init__(self,manager: multiprocessing.managers.SyncManager, args: argparse.Namespace, config: Configuration) -> None:
        """
        Initialize the test state with initial information
        """
        self.monit_host = config.get('monit_host', None)
        self.monit_port = config.get('monit_port', 10012)


        print ("------------------------------------------- monitoring info")
        print (self.monit_host)
        print (self.monit_port)
        print (ocsync_version())
        print (str(str(ocsync_version())[1:-1].replace(", ",".")))
        print ("-----------------------------------------------------------")

        self._test_ignored = config.get('_test_ignored', None)

        if not self.monit_host:
            self.worker_results = None
            return

        testname = (str(args.test_target).split("test_"))[-1].split(".")[0]
        self.worker_results = manager.Queue()
        self.test_results = dict()
        self.runtimestamp = config._run_timestamp

        # extract test parameters
        parameters: list[dict[str, Any]] = []
        param: dict[str, Any] = {}
        for c in config.__dict__:
            if c.startswith(testname + "_"):
                param[str((c.replace(testname + "_", "")))] = config[c]
                parameters.append(param)
                print(c, config[c])

        if platform.system() == 'Linux':
            # platform.dist() was removed in python 3.8
            try:
                os_release = platform.freedesktop_os_release()
            except OSError:
                os_release = {}
            distribution = (os_release.get('ID', ''), os_release.get('VERSION_ID', ''))
            #client_platform = str(platform.system()) + "-" + str(distribution[0])+str(distribution[1])
            distr = tuple([str(x) for x in distribution[1].split(".")])
            client_platform = str(distribution[0])+distr[0]
        elif platform.system() == 'Darwin':
            ver = platform.mac_ver()
            client_platform = "OSX" + str(ver[0])
        else:
            client_platform = platform.system() + platform.release()


        # initialize json to be sent for monitoring
        self.test_results = {"activity": config.monit_activity, 'test_name': testname, 'hostname': socket.gethostname(),'backend': config.instance_name,
                             'oc_client_version': str(str(ocsync_version())[1:-1].replace(", ",".")),'oc_server': config.oc_server.split("/")[0],'platform': client_platform,
                             'parameters':parameters,'parameters_text':str(parameters),'errors': [],'errors_text': "",'success': [],
                             'total_errors':0,'total_success':0, 'qos_metrics': [],'ignoredFailures':0,'passed': 0,'failed': 0, 'test_ignored': self._test_ignored }


    def join_worker_results(self) -> None:
        """
        Join partial worker tests results information. The partial results are stored in queue (FIFO order)
        """
        if not self.monit_host:
            return

        partial_results = self.worker_results.get() # type: ignore[union-attr] # set whenever monit_host is
        if(partial_results[0]): self.test_results['errors'].append(partial_results[0])

        self.test_results['total_errors']+=len(self.test_results['errors'])


    def test_finish(self) -> None:
        """"
        Check if the test has passed and publish results
        """
        if not self.monit_host:
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


    def get_json_results(self) -> list[dict[str, Any]]:
        """
        Saved results in a dictionary to be able to convert them in a json format
        """
        thuman = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.runtimestamp))

        if (self.test_results['errors']): self.test_results['errors_text'] = str(self.test_results['errors'])
        json_result = [{'producer':"smashboxtests", 'type_prefix':"raw", 'type':"dbmetric", 'hostname': socket.gethostname(), 'timestamp':int(self.runtimestamp), 'elapsed':int(time.time() - self.runtimestamp), 'timestamp_full': thuman, "data":self.test_results}]
        return json_result

    # --------------------------------------------------------------------------------
    # Send metrics to the monit central service
    #   Report tests results and statistics to the monitoring dashboard
    # --------------------------------------------------------------------------------

    def send(self,document: list[dict[str, Any]]) -> requests.Response:
        import requests, json
        dest = self.monit_host + ":" + str(self.monit_port) + "/smashboxtests"
        print ("------------------------------------------- monitoring data")
        print ("Dest: %s" % dest)
        print (json.dumps(document))
        print ("-----------------------------------------------------------")

        urllib3.disable_warnings()
        return requests.post(dest, data=json.dumps(document),
                             auth=HTTPBasicAuth('smashboxtests', '0mILcBs^9M10'),
                             headers={"Content-Type": "application/json; charset=UTF-8"},
                             verify=False)

    def send_and_check(self,document: list[dict[str, Any]], should_fail: bool = False) -> None:
        response = self.send(document)
        assert (
        (response.status_code in [200]) != should_fail), 'With document: {0}. Status code: {1}. Message: {2}'.format(
            document, response.status_code, response.text)
