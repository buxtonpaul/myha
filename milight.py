#!/usr/bin/python
import socket
from milightcmds import *



def dolog(msg):
    ''' Log a message'''
    print "DEBUG: ", msg


###################
## Configuration ##
###################
               # Wait for data in sec
CMDLINE_INFO = (
    "##########################\n"
    "## Command line options ##\n"
    "##########################\n"
    "Use command line as follow : milight.py DEVICE ZONE CMD <param>\n"
    "                           : CMD1 Bulb zone\n"
    "                           : CMD2 Bulb command\n"
    "-------------------------------------------------------------------------------\n"
    " Select the Bulb device    : RAWCOMMANDS RGBW BRIDGE"
    "Select the bulb zone       : 00 01 02 03 04\n"
    "RAWCOMMANDS"
    "Bulb on/off                : ON OFF NIGHTON WHITEON\n"
    "Mode Speed up/down         : SPEEDUP SPEEDDOWN\n"
    "Kelvin warmwhite           : WW00 WW25 WW50 WW75 WW100\n"
    "Saturation                 : SATUR00 SATUR25 SATUR50 SATUR75 SATUR100\n"
    "Mode (discomode)           : MODE01 MODE02 MODE03 MODE04 MODE05\n"
    "                           : MODE06 MODE07 MODE08 MODE09\n"
    "Bulb color                 : COLOR001 COLOR002 COLOR003 COLOR004\n"
    "BRIDGE and RGBW            : ON OFF WHITEON MODE X BRIGHT X\n"
    "WHITE commands             : ON OFF WHITEON NIGHTON TEMPUP TEMPDOWN BRIGHTUP BRIGHTDOWN\n"
)



class milight_bridge(object):

    lightSession = False
    live = True
    SessionID1 = 0
    SessionID2 = 0
    sockServer = 0
    iboxip = ""
    cyclenr = 0
    bridgeopen=False
    ''' Miligght bridge class to handle controlling a milight bridge'''
    def __init__(self, IBOX_IP="fake",        # iBox IP address
                 UDP_PORT_SEND=5987,            # Port for sending
                 UDP_PORT_RECEIVE=55054,        # Port for receiving
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
        for icount in range(0, UDP_MAX_TRY):
            try:
                if self.live:
                    self.sockServer = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    self.sockServer.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    self.sockServer.bind(('', UDP_PORT_RECEIVE))
                    self.sockServer.settimeout(UDP_TIMEOUT)
                    self.sockServer.sendto( bytearray(START_SESSION), (self.iboxip,  self.udp_port_send))
            
                   
                    dataReceived, addr = self.sockServer.recvfrom(1024)
                    dataReceived = bytearray(dataReceived)
                else:
                    dolog("Fake it")
                    dataReceived = [0x28, 0x00, 0x00, 0x00, 0x11, 0x00, 0x02, 0xAC, 0xCF,
                                    0x23, 0xF5, 0x7A, 0xD4, 0x69, 0xF0, 0x3C, 0x23, 0x00,
                                    0x01, 0x05, 0x00, 0x00]
                self.SessionID1 = dataReceived[19]
                self.SessionID2 = dataReceived[20]
                dolog("Received session message: {message}".format(message=hexstr(dataReceived, ' ')))
                dolog("SessionID1: {session1}".format(session1=self.SessionID1))
                dolog("SessionID2: {session1}".format(session1=self.SessionID2))
                self.lightSession = True
                break
            except socket.timeout:
                    print "Timeout on session start: ", hexstr(START_SESSION)
                    dolog("Milight Script: Timeout on command... doing a retry")
                    self.sockServer.close()
                    self.lightSession=False
                    continue

    def sndCommand(self,message):
        ''' Send a list of hex values as a message '''
        if self.live & self.lightSession:
            self.sockServer.sendto(bytearray(message), (self.iboxip, self.udp_port_send))
            dataReceived, addr = self.sockServer.recvfrom(1024)
            dolog("Receiving response: {response}".format(response=hexstr(bytearray(dataReceived), ' ')))
            return(dataReceived,addr)
        else:
            return([0x1,0x2,0x3],1234)
            
    def buildCmd(self, bulbCommand, Zone, checkSum):
        preamble = [0x80, 0x00, 0x00, 0x00, 0x11]
        ret=(preamble + [self.SessionID1, self.SessionID2, 0x00, self.cyclenr, 0x00] +
              bulbCommand + [Zone, 0x00, checkSum])
        self.cyclenr = self.cyclenr + 1
        return ret

    def close(self):
        if(self.live & self.lightSession):
            print "closing socket"
            self.sockServer.close()




###############################################################################################


def hexstr(vals, sep=', '):
    ''' Print the provided list as a hex string, using
    the optional seperator to determine how they are seperated'''
    return'[{}]'.format(sep.join(hex(x) for x in vals))


from abc import ABCMeta, abstractmethod

class MiLight(object):
    ''' An object for the milight abstract milight 
    Attributes:
    name: name of the light represented by this case
    zone: the zone that this light is attached to
    bridge: the bridge this light is attached to
    '''
    __metaclass__ = ABCMeta

    def __init__(self,name,zone,bridge):
        self.bridge=bridge
        self.name=name
        self.zone=zone

    def on(self):
        # construct the command and send it
        self.doCommand("ON")
    def off(self):
        self.doCommand("OFF")
        # construct the command and send it

    def doCommand(self,command,value='none'):
        if command in self.commands:
            commandstring=self.commands.get(command)
            Checksum = sum(commandstring) & 0xff
            sendCommand = self.bridge.buildCmd(commandstring, self.zone, Checksum)
            dolog("Sending Command:{}".format(hexstr(bytearray(sendCommand))))
            dataReceived, addr = self.bridge.sndCommand(bytearray(sendCommand))
            dolog("Received Reponse:{}".format(hexstr(bytearray(dataReceived))))
        elif command in self.varcommands:
            if value!='none':
                commandstring=self.varcommands.get(command)+[value] + [0x00, 0x00, 0x00]
                Checksum = sum(commandstring) & 0xff
                sendCommand = self.bridge.buildCmd(commandstring, self.zone, Checksum)
                dolog("Sending Command:{}".format(hexstr(bytearray(sendCommand))))
                dataReceived, addr = self.bridge.sndCommand(bytearray(sendCommand))
                dolog("Received Reponse:{}".format(hexstr(bytearray(dataReceived))))
            else:
                dolog("Request to do variable command with no param provided")
        else:
            dolog("Command {} not found".format(command))
 

class BridgeLight(MiLight):
    ''' The Bridge Light object'''
    commands={
        "ON":    [0x31, 0x00, 0x00, 0x00, 0x03, 0x03, 0x00, 0x00, 0x00],
        "OFF":   [0x31, 0x00, 0x00, 0x00, 0x03, 0x04, 0x00, 0x00, 0x00],
        "WHITE": [0x31, 0x00, 0x00, 0x00, 0x03, 0x05, 0x00, 0x00, 0x00]
    }
    varcommands={
    "BRIGHT"   :  [0x31, 0x00, 0x00, 0x00, 0x02],
    "MODE"     :  [0x31, 0x00, 0x00, 0x00, 0x04]
    }


class RGBW(MiLight):
    ''' The RGBW Light object'''
    commands={
    "ON" :   [0x31, 0x00, 0x00, 0x07, 0x03, 0x01, 0x00, 0x00, 0x00],
    "OFF":   [0x31, 0x00, 0x00, 0x07, 0x03, 0x02, 0x00, 0x00, 0x00],
    "NIGHT": [0x31, 0x00, 0x00, 0x07, 0x03, 0x06, 0x00, 0x00, 0x00],
    "WHITE": [0x31, 0x00, 0x00, 0x07, 0x03, 0x05, 0x00, 0x00, 0x00]
    
    }
    varcommands={
    "BRIGHT"   : [0x31, 0x00, 0x00, 0x07, 0x02],
    "MODE"     : [0x31, 0x00, 0x00, 0x07, 0x04]}

class White(MiLight):
    commands = {
    "ON"        : [0x31, 0x00, 0x00, 0x01, 0x01, 0x07, 0x00, 0x00, 0x00],
    "OFF"       : [0x31, 0x00, 0x00, 0x01, 0x01, 0x08, 0x00, 0x00, 0x00],
    "NIGHT"     : [0x31, 0x00, 0x00, 0x01, 0x01, 0x06, 0x00, 0x00, 0x00],
    "BRIGHTUP"  : [0x31, 0x00, 0x00, 0x01, 0x01, 0x01, 0x00, 0x00, 0x00],
    "BRIGHTDOWN": [0x31, 0x00, 0x00, 0x01, 0x01, 0x02, 0x00, 0x00, 0x00],
    "TEMPUP"    : [0x31, 0x00, 0x00, 0x01, 0x01, 0x03, 0x00, 0x00, 0x00],
    "TEMPDOWN"  : [0x31, 0x00, 0x00, 0x01, 0x01, 0x04, 0x00, 0x00, 0x00],
    
    }
    varcommands={}


######################
## iBox v6 commands ##
######################

#def iBoxV6Commands(device, cmd, value):
#    ''' Construct a MiLightBox command from the device command and value '''
#    if cmd in DEVICES[device][0]:
#        return DEVICES[device][0].get(cmd)
#    if device == 'RAWCOMMANDS':
#        dolog('Command not found:{cmd}'.format(cmd=cmd))
#        return 0
#    if cmd in DEVICES[device][1]:
#        dolog("Variable command: {cmd} {value}".format(cmd=cmd, value=value))
#        retval = DEVICES[device][1].get(cmd)+ [value] + [0x00, 0x00, 0x00]
#        dolog("Trying: {command}".format(command=hexstr(retval)))
#        return retval
#    dolog('Command not found')
#    return 0







########################
## V6 command builder ##
########################
if __name__ == "__main__":
    import sys
    CMDLINE_CMD = 'ON'
    CMDLINE_ZONE = 0
    CMDLINE_VALUE1 = 100
    CMDLINE_DEVICE = "RGBW"
    
    maxtries=5
    
    
    bridge = milight_bridge(UDP_MAX_TRY=maxtries)
  #  bridge = milight_bridge(IBOX_IP="192.168.0.34", UDP_MAX_TRY=maxtries)

    mylight=BridgeLight("mylight",0,bridge)

    for icount in range(0, maxtries):
        try:
            mylight.off()
            mylight.doCommand('BRIGHT',51)
            
            break

        except socket.timeout:
            dolog("Timeout on command: {command}".format(command=hexstr(sendCommand, ' ')))
            continue
    bridge.close()
    

#"192.168.0.34"