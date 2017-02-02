#!/usr/bin/python
''' milight module'''
import socket
from abc import ABCMeta
from milightcmds import START_SESSION
from utils import dolog, hexstr


CMDLINE_INFO = (
    "##########################\n"
    "## Command line options ##\n"
    "##########################\n"
    "Use command line as follow : milight.py DEVICE ZONE CMD <param>\n"
)



class Milightbridge(object):
    ''' milight bridge class'''
    lightsession = False
    live = True
    sessionid = (0, 0)
    sockserver = 0
    iboxip = ""
    cyclenr = 0
    udp_port_send = 0
    UDP_PORT_RECEIVE = 55054,        # Port for receiving

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
        if IBOX_IP == 'fake':
            self.live = False
            dolog("Starting up with fake settings")
        dolog("Trying to connect to server {} on port {}".format(self.iboxip, UDP_PORT_SEND))
        for count in range(0, UDP_MAX_TRY):
            try:
                if self.live:
                    self.sockserver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    self.sockserver.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    self.sockserver.bind(('', self.UDP_PORT_RECEIVE))
                    self.sockserver.settimeout(UDP_TIMEOUT)
                    self.sockserver.sendto(bytearray(START_SESSION),
                                           (self.iboxip, self.udp_port_send))
                    datareceived, addr = self.sockserver.recvfrom(1024)
                    datareceived = bytearray(datareceived)
                else:
                    dolog("Fake it")
                    datareceived = bytearray([0x28, 0x00, 0x00, 0x00, 0x11, 0x00, 0x02, 0xAC, 0xCF,
                                              0x23, 0xF5, 0x7A, 0xD4, 0x69, 0xF0, 0x3C, 0x23, 0x00,
                                              0x01, 0x05, 0x00, 0x00])
                    addr = 0x123
                self.sessionid = (datareceived[19], datareceived[20])
                dolog("Received session message: {}:{}".format(addr, hexstr(datareceived, ' ')))
                dolog("SessionID: {}".format(self.sessionid))
                self.lightsession = True
                break
            except socket.timeout:
                print "Timeout on session start: ", hexstr(START_SESSION)
                dolog("Milight Script: Timeout on command... doing a retry {}".format(count))
                self.sockserver.close()
                self.lightsession = False
                continue
        return

    def sndcommand(self, message):
        ''' Send a list of hex values as a message '''
        if self.live & self.lightsession:
            self.sockserver.sendto(bytearray(message), (self.iboxip, self.udp_port_send))
            datareceived, addr = self.sockserver.recvfrom(1024)
            dolog("Receiving response: {}".format(hexstr(bytearray(datareceived), ' ')))
            return(datareceived, addr)
        else:
            return([0x1, 0x2, 0x3], 1234)
        return

    def buildcmd(self, bulbcommand, zone, checksum):
        ''' buildcmd'''
        preamble = [0x80, 0x00, 0x00, 0x00, 0x11]
        ret = (preamble + [self.sessionid[0], self.sessionid[1], 0x00, self.cyclenr, 0x00] +
               bulbcommand + [zone, 0x00, checksum])
        self.cyclenr = self.cyclenr + 1
        return ret

    def close(self):
        ''' CLose the milight socker'''
        if self.live & self.lightsession:
            print "closing socket"
            self.sockserver.close()
        return



class MiLight(object):
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
            checksum = sum(commandstring) & 0xff
            sendcmd = self.bridge.buildcmd(commandstring, self.zone, checksum)
            dolog("Sending Command:{}".format(hexstr(bytearray(sendcmd))))
            datareceived, addr = self.bridge.sndcommand(bytearray(sendcmd))
            dolog("Received Reponse:{}:{}".format(addr, hexstr(bytearray(datareceived))))
        elif commandlist[0] in self.varcommands:
            if len(commandlist) >1:
                value=int(commandlist[1])          
                commandstring = self.varcommands.get(commandlist[0])+[value] + [0x00, 0x00, 0x00]
                checksum = sum(commandstring) & 0xff
                sendcmd = self.bridge.buildcmd(commandstring, self.zone, checksum)
                dolog("Sending Command:{}".format(hexstr(bytearray(sendcmd))))
                datareceived, addr = self.bridge.sndcommand(bytearray(sendcmd))
                dolog("Received Reponse:{}".format(hexstr(bytearray(datareceived))))
            else:
                dolog("Request to do variable command with no param provided")
        else:
            dolog("Command {} not found".format(commandlist[0]))

class BridgeLight(MiLight):
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


class RGBW(MiLight):
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

class White(MiLight):
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
    BRIDGE = Milightbridge(UDP_MAX_TRY=MAXTRIES)
  #  bridge = milight_bridge(IBOX_IP="192.168.0.34", UDP_MAX_TRY=maxtries)
    MYLIGHT = BridgeLight("mylight", 0, BRIDGE)

    for icount in range(0, MAXTRIES):
        try:
            MYLIGHT.off()
            MYLIGHT.docommand(['BRIGHT', '51'])
            break

        except socket.timeout:
            dolog("Timeout on command!")
            continue
    BRIDGE.close()
