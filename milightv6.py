#!/usr/bin/python
''' milight module'''
import socket
from abc import ABCMeta

from utils import dolog, hexstr


CMDLINE_INFO = (
    "##########################\n"
    "## Command line options ##\n"
    "##########################\n"
    "Use command line as follow : milight.py DEVICE ZONE CMD <param>\n"
)
#todo Rename bridges and lights to be bridge specific
#generalise the milight class to be a bulb class, should provide interface and store state
# all bulbs will provide this behaviour


START_SESSION = [0x20, 0x00, 0x00, 0x00, 0x16, 0x02, 0x62,
                 0x3A, 0xD5, 0xED, 0xA3, 0x01, 0xAE, 0x08,
                 0x2D, 0x46, 0x61, 0x41, 0xA7, 0xF6, 0xDC,
                 0xAF, 0xD3, 0xE6, 0x00, 0x00, 0x1E]

class Milightv6bridge(object):
    ''' milight bridge class'''
    lightsession = False
    live = True
    sessionid = (0, 0)
    sockserver = 0
    iboxip = ""
    cyclenr = 0
    udp_port_send = 0
    UDP_PORT_RECEIVE = 55054,        # Port for receiving
    bulbs={}
    bulbtypes=["RGBW", "WHITE", "BRIDGE"]

    ''' Miligght bridge class to handle controlling a milight bridge'''
    def __init__(self, IBOX_IP="fake",        # iBox IP address
                 UDP_PORT_SEND=5987,            # Port for sending
                 UDP_MAX_TRY=5,                 # Max sending max value is 256
                 UDP_TIMEOUT=5):
        ''' Constructor function. params are
            IBOX_IP
            UDP_PORT_SEND
            UDP_PORT_RECEIVE
            UDP_MAX_TRY
            UDP_TIMEOUT '''
        self.iboxip = IBOX_IP
        self.udp_port_send = UDP_PORT_SEND
        self.udp_max_try = UDP_MAX_TRY
        self.udp_timeout = UDP_TIMEOUT
        if IBOX_IP == 'fake':
            self.live = False
            dolog("Starting up with fake settings")
        return

    def sndcommand(self, message,sockserver):
        ''' Send a list of hex values as a message '''
        dolog("Sending: {}".format(hexstr(message)))
        if self.live & self.lightsession:
            sockserver.sendto(bytearray(message), (self.iboxip, self.udp_port_send))
            datareceived, addr = sockserver.recvfrom(1024)
            dolog("Receiving response: {}".format(hexstr(bytearray(datareceived), ' ')))

            return(datareceived, addr)
        else:
            return([0x1, 0x2, 0x3], 1234)
        return
    
    def send(self,message,zone):
        dolog("Trying to connect to server {} on port {}".format(self.iboxip, self.udp_port_send))
        for count in range(0, self.udp_max_try):
            try:
                if self.live:
                    sockserver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    sockserver.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    sockserver.bind(('', self.UDP_PORT_RECEIVE))
                    sockserver.settimeout(self.udp_timeout)
                    sockserver.sendto(bytearray(START_SESSION),
                                           (self.iboxip, self.udp_port_send))
                    datareceived, addr = sockserver.recvfrom(1024)
                    datareceived = bytearray(datareceived)
                else:
                    dolog("Fake it")
                    datareceived = bytearray([0x28, 0x00, 0x00, 0x00, 0x11, 0x00, 0x02, 0xAC, 0xCF,
                                              0x23, 0xF5, 0x7A, 0xD4, 0x69, 0xF0, 0x3C, 0x23, 0x00,
                                              0x01, 0x2e, 0x00, 0x00])
                    addr = 0x123
                    sockserver="NULL" # should not be used!
                self.sessionid = (datareceived[19], datareceived[20])
                dolog("Received session message: {}:{}".format(addr, hexstr(datareceived, ' ')))
                dolog("SessionID: {}".format(self.sessionid))
                self.lightsession = True
                ret=self.sndcommand(self.buildcmd(message,zone),sockserver)

                break
            except socket.timeout:
                dolog("Timeout on session start: {}".format(hexstr(START_SESSION)))
                dolog("Milight Script: Timeout on command... doing a retry {}".format(count))
                sockserver.close()
                self.lightsession = False
                continue

        if self.live:               
            sockserver.close()
        else:
            print "Fake socket open, sent command, closing socket"
     
        
        return ret
        

    def buildcmd(self, bulbcommand, zone):
        ''' buildcmd'''
        preamble = [0x80, 0x00, 0x00, 0x00, 0x11]
        checksum = (sum(bulbcommand)+zone) & 0xff
        ret = (preamble + [self.sessionid[0], self.sessionid[1], 0x00, self.cyclenr, 0x00] +
               bulbcommand + [zone, 0x00, checksum])
        self.cyclenr = self.cyclenr + 1
        return ret

    def close(self):
        ''' CLose the milight socker'''
        return

    def addbulb(self, bulbtype, bulbname, zone):
        '''Adds a bulb to the bridge'''
        # first check the bulb name doesnt exist already
        if bulbname in self.bulbs:
            dolog("Attempt to add bulb {} which already exists".format(bulbname))
            return
        # Try and add the bulb assuming it is one we know about
        if bulbtype in self.bulbtypes:
            if bulbtype == 'RGBW':
                self.bulbs[bulbname] = V6RGBW(bulbname, zone, self)
            elif bulbtype == 'WHITE':
                self.bulbs[bulbname] = V6White(bulbname, zone, self)
            else:
                self.bulbs[bulbname] = V6BridgeLight(bulbname, zone, self)
            return self.bulbs[bulbname]
        else:
            dolog("Attempt to add a bulb type we do not support {}".format(bulbtype))
        return

class MiLightv6(object):
    ''' An object for the milight abstract milight
    Attributes:
    name: name of the light represented by this case
    zone: the zone that this light is attached to
    bridge: the bridge this light is attached to
    '''
    commands = {}
    varcommands = {}
    __metaclass__ = ABCMeta

    def __init__(self, name, zone, bridge):
        self.bridge = bridge
        self.name = name
        self.zone = zone
    def lighton(self):
        ''' On command'''
        # construct the command and send it
        self.docommand(["ON"])
    def off(self):
        ''' Off command'''
        self.docommand(["OFF"])
        # construct the command and send it

    def docommand(self, commandlist):
        ''' doCommand'''
        if commandlist[0] in self.commands:
            commandstring = self.commands.get(commandlist[0])
        elif commandlist[0] in self.varcommands:
            if len(commandlist) > 1:
                value = int(commandlist[1])
                commandstring = self.varcommands.get(commandlist[0])+[value] + [0x00, 0x00, 0x00]
            else:
                dolog("Request to do variable command with no param provided")
        else:
            dolog("Command {} not found".format(commandlist[0]))
            return

        datareceived, addr = self.bridge.send(commandstring,self.zone)
        dolog("Received Reponse:{}:{}".format(addr, hexstr(bytearray(datareceived))))
    def colour(self,colour):
        ''' Base class command to handle colour'''
        dolog("Attempt to use color for class that does not support it")
        return

class V6BridgeLight(MiLightv6):
    ''' The Bridge Light object'''
    commands = {
        "ON":    [0x31, 0x00, 0x00, 0x00, 0x03, 0x03, 0x00, 0x00, 0x00],
        "OFF":   [0x31, 0x00, 0x00, 0x00, 0x03, 0x04, 0x00, 0x00, 0x00],
        "WHITE": [0x31, 0x00, 0x00, 0x00, 0x03, 0x05, 0x00, 0x00, 0x00]
    }
    varcommands = {
        "BRIGHT"   :  [0x31, 0x00, 0x00, 0x00, 0x02],
        "MODE"     :  [0x31, 0x00, 0x00, 0x00, 0x04]
    }

    def colour(self,color):
        ''' Color handling for the bridge class'''
        # first figure out how the color has been handled, could be 
        # RGB ### string , HueSV, HUE angle
        # Convert to the Hue value supported byt the bridge and transmit it
        
class V6RGBW(MiLightv6):
    ''' The RGBW Light object'''
    commands = {
        "ON" :   [0x31, 0x00, 0x00, 0x07, 0x03, 0x01, 0x00, 0x00, 0x00],
        "OFF":   [0x31, 0x00, 0x00, 0x07, 0x03, 0x02, 0x00, 0x00, 0x00],
        "NIGHT": [0x31, 0x00, 0x00, 0x07, 0x03, 0x06, 0x00, 0x00, 0x00],
        "WHITE": [0x31, 0x00, 0x00, 0x07, 0x03, 0x05, 0x00, 0x00, 0x00]
    }
    varcommands = {
        "BRIGHT"   : [0x31, 0x00, 0x00, 0x07, 0x02],
        "MODE"     : [0x31, 0x00, 0x00, 0x07, 0x04]
    }

class V6White(MiLightv6):
    ''' The White Light milight class implementaiton '''
    commands = {
        "ON"        : [0x31, 0x00, 0x00, 0x01, 0x01, 0x07, 0x00, 0x00, 0x00],
        "OFF"       : [0x31, 0x00, 0x00, 0x01, 0x01, 0x08, 0x00, 0x00, 0x00],
        "NIGHT"     : [0x31, 0x00, 0x00, 0x01, 0x01, 0x06, 0x00, 0x00, 0x00],
        "BRIGHTUP"  : [0x31, 0x00, 0x00, 0x01, 0x01, 0x01, 0x00, 0x00, 0x00],
        "BRIGHTDOWN": [0x31, 0x00, 0x00, 0x01, 0x01, 0x02, 0x00, 0x00, 0x00],
        "TEMPUP"    : [0x31, 0x00, 0x00, 0x01, 0x01, 0x03, 0x00, 0x00, 0x00],
        "TEMPDOWN"  : [0x31, 0x00, 0x00, 0x01, 0x01, 0x04, 0x00, 0x00, 0x00],
    }
    varcommands = {}




if __name__ == "__main__":
    MAXTRIES = 5
    BRIDGE = Milightv6bridge(UDP_MAX_TRY=MAXTRIES)
  #  bridge = milight_bridge(IBOX_IP="192.168.0.34", UDP_MAX_TRY=maxtries)
    MYLIGHT = V6BridgeLight("mylight", 0, BRIDGE)

    for icount in range(0, MAXTRIES):
        try:
            MYLIGHT.off()
            MYLIGHT.docommand(['BRIGHT', '51'])
            break

        except socket.timeout:
            dolog("Timeout on command!")
            continue
    BRIDGE.close()
