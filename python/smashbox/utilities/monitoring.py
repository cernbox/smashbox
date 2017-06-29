from smashbox.utilities import *
import socket
import sys
import logging
logger = logging.getLogger()

# Simple monitoring to grafana (disabled if not set in config)
# data should be presented in the format: metric.name value
def push_to_monitoring(data):

    time1 = time.time()
    data = data + " " + str(time1)

    if not data[-1] == '\n':
        data += '\n'

    send_metric(data)


#--------------------------------------------------------------------------------
# Send metrics to Grafana
#   Report tests results and statistics to the Grafana monitoring dashboard
#--------------------------------------------------------------------------------
def send_metric(data):
    monitoring_host=config.get('monitoring_host',"filer-carbon.cern.ch")
    monitoring_port=config.get('monitoring_port',2003)

    logger.info("message %s" % data)

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Bind socket to local host and port
    try:
        s.connect((monitoring_host, monitoring_port))
    except socket.error as msg:
        logger.info('Connect failed. Error Code : ' + str(msg[0]) + ' Message : ' + msg[1])
        sys.exit()

    s.sendall(data)
    logger.info("--->publishing logs to grafana")
    s.close()

