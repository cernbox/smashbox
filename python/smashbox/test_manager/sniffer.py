import os, time
import threading
import socket, sys
from struct import *
import datetime

try:
    import netifaces
except ImportError,e :
    print('Error!%s'%e)
    sys.exit()
    
"""
    Packet extraction reference - http://www.binarytides.com/python-packet-sniffer-code-linux/
"""
class SnifferThread(threading.Thread):
    def __init__(self):
        super(SnifferThread, self).__init__()
        self.stoprequest = threading.Event()
        self.packet_traces = []
        #create a AF_PACKET type raw socket (thats basically packet level)
        #define ETH_P_ALL    0x0003          /* Every packet (be careful!!!) */
        try:
            self.s = socket.socket( socket.AF_PACKET , socket.SOCK_RAW , socket.ntohs(0x0003))
        except socket.error , msg:
            print 'Socket could not be created. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
            sys.exit()
            
        
    def run(self):
        localhost = str([l for l in ([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")][:1], [[(s.connect(('8.8.8.8', 80)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]]) if l][0][0])
        while not self.stoprequest.isSet():
            packet = self.s.recvfrom(65565)
            #packet string from tuple
            packet = packet[0]
            #take first 20 characters for the ip header
            eth_length = 14
             
            eth_header = packet[:eth_length]
            eth = unpack('!6s6sH' , eth_header)
            eth_protocol = socket.ntohs(eth[2])
            if eth_protocol == 8 :
                ip_header = packet[eth_length:20+eth_length]
                #now unpack them :)
                iph = unpack('!BBHHHBBH4s4s' , ip_header)
                protocol = iph[6]
                if protocol == 6 :
                    s_addr = socket.inet_ntoa(iph[8]);
                    d_addr = socket.inet_ntoa(iph[9]);
                    incoming = None
                    ip=None
                    if (str(s_addr) == str(d_addr)):
                        ip = "localhost"
                        incoming = False
                    elif (str(s_addr) == localhost  or str(s_addr) == '127.0.0.1'):
                        ip = str(d_addr)
                        incoming = False
                    elif (str(d_addr) == localhost or str(d_addr) == '127.0.0.1'):
                        ip = str(s_addr)
                        incoming = True
                    
                    dict = { "time": int((datetime.datetime.now()).strftime('%s%f')), "ip": ip, "incoming": incoming,"size" : str(len(packet)) }
                    self.packet_traces.append(dict)
            
    def stop(self):
        self.stoprequest.set()
        return self.packet_traces

    def join(self, timeout=10):
        super(SnifferThread, self).join(timeout)