from smashbox.utilities import *
import pickle
import struct
import socket
import sys
import logging
logger = logging.getLogger()

# simple monitoring to grafana (disabled if not set in config)

def push_to_monitoring(tuples,timestamp=None):

    if not timestamp:
        timestamp = time.time()
    logger.info("publishing logs to grafana %s" % timestamp)
    send_metric(tuples)


#--------------------------------------------------------------------------------
# Send metrics to Grafana
#   Report tests results and statistics to the Grafana monitoring dashboard
#--------------------------------------------------------------------------------
def send_metric(tuples):

    monitoring_host=config.get('monitoring_host',"filer-carbon.cern.ch")
    monitoring_port=config.get('monitoring_port',2003)

    payload = pickle.dumps(tuples, protocol=2)
    header = struct.pack('!L', len(payload))
    message = header + payload
    logger.info("message %s" % message)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print 'Socket created'

    # Bind socket to local host and port
    try:
        s.connect((monitoring_host, monitoring_port))
    except socket.error as msg:
        logger.info('Connect failed. Error Code : ' + str(msg[0]) + ' Message : ' + msg[1])
        sys.exit()

    s.sendall(message)
    logger.info("publishing logs to grafana")
    s.close()
