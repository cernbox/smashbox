from smashbox.utilities import *
import pickle
import struct
import socket
import sys
# simple monitoring to grafana (disabled if not set in config)

def push_to_monitoring(metric,value,timestamp=None):

    if not timestamp:
        timestamp = time.time()

    data = (metric,(value,timestamp))
    send_metric(data)


#--------------------------------------------------------------------------------
# Send metrics to Grafana
#   Report tests results and statistics to the Grafana monitoring dashboard
#--------------------------------------------------------------------------------
def send_metric(data):

    monitoring_host=config.get('monitoring_host',None)
    monitoring_port=config.get('monitoring_port',2003)

    if not monitoring_host:
        return

    print("publishing logs to grafana")
    payload = pickle.dumps(data, protocol=2)
    header = struct.pack("!L", len(payload))
    message = header + payload

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print 'Socket created'

    # Bind socket to local host and port
    try:
        s.bind((monitoring_host, monitoring_port))
    except socket.error as msg:
        print 'Bind failed. Error Code : ' + str(msg[0]) + ' Message : ' + msg[1]
        sys.exit()

    print 'Socket bind complete'

    # Start listening on socket
    s.listen(10)
    print 'Socket now listening'

    # now keep talking with the client
    while 1:
        # wait to accept a connection - blocking call
        conn, addr = s.accept()
        print 'Connected with ' + addr[0] + ':' + str(addr[1])

    s.sendall(message)

    s.close()

