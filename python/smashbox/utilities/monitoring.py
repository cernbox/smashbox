from smashbox.utilities import *

# simple monitoring to grafana (disabled if not set in config)

def push_to_monitoring(metric,value,timestamp=None):

    monitoring_host=config.get('monitoring_host',None)
    monitoring_port=config.get('monitoring_port',2003)

    if not monitoring_host:
        return

    if not timestamp:
        timestamp = time.time()

    os.system("echo '%s %s %s' | nc %s %s"%(metric,value,timestamp,monitoring_host,monitoring_port))
