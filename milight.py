#!/usr/bin/python
import socket
import mylightcmds



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
    sockserver = 0
    iboxip = ""
    cyclenr = 0
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
            live = False
            dolog("Starting up with fake settings")
        dolog("Trying to connect to server {} on port {}".format(self.iboxip, UDP_PORT_SEND))
        for icount in range(0, UDP_MAX_TRY):
            try:
                if live:
                    self.sockServer = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    self.sockServer.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    self.sockServer.bind(('', UDP_PORT_RECEIVE))
                    self.sockServer.settimeout(UDP_TIMEOUT)
                    self.sockServer.sendto(START_SESSION, (self.iboxip,  self.udp_port_send))
                    dataReceived, addr = self.sockServer.recvfrom(1024)
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
                    print "Timeout on session start: ", START_SESSION
                    dolog("Milight Script: Timeout on command... doing a retry")
                    self.sockServer.close()
                    continue

    def sndCommand(self,message):
        ''' Send a list of hex values as a message '''
        if self.live:
            self.sockServer.sendto(bytearray.fromhex(message), (self.iboxip, self.udp_port_send))
            dataReceived, addr = self.sockServer.recvfrom(1024)
            dolog("Receiving response: {response}".format(response=hexstr(dataReceived, ' ')))
            return(dataReceived,addr)
        else:
            return([0x1,0x2,0x3],1234)
            
    def buildCmd(self,cyclenr, bulbCommand, Zone, checkSum):
        preamble = [0x80, 0x00, 0x00, 0x00, 0x11]
        ret=(preamble + [self.SessionID1, self.SessionID2, 0x00, self.cyclenr, 0x00] +
              bulbCommand + [Zone, 0x00, checkSum])
        self.cyclenr = self.cyclenr + 1
        return ret

    def __del__(self):
        self.sockServer.close()




###############################################################################################


def hexstr(vals, sep=', '):
    ''' Print the provided list as a hex string, using
    the optional seperator to determine how they are seperated'''
    return'[{}]'.format(sep.join(hex(x) for x in vals))






DEVICES = {
    "BRIDGE" : [BRIDGECOMMANDS, BRIDGEVARCOMMANDS],
    "RGBW" : [RGBWCOMMANDS, RGBWVARCOMMANDS],
    "RAWCOMMANDS" : [RAWCOMMANDS],
    "WHITE" : [WHITECOMMANDS],
    }

######################
## iBox v6 commands ##
######################

def iBoxV6Commands(device, cmd, value):
    ''' Construct a MiLightBox command from the device command and value '''
    if cmd in DEVICES[device][0]:
        return DEVICES[device][0].get(cmd)
    if device == 'RAWCOMMANDS':
        dolog('Command not found:{cmd}'.format(cmd=cmd))
        return 0
    if cmd in DEVICES[device][1]:
        dolog("Variable command: {cmd} {value}".format(cmd=cmd, value=value))
        retval = DEVICES[device][1].get(cmd)+ [value] + [0x00, 0x00, 0x00]
        dolog("Trying: {command}".format(command=hexstr(retval)))
        return retval
    dolog('Command not found')
    return 0




########################
## V6 command builder ##
########################
if __name__ == "__main__":
    import sys
    ##########################
    ## Commandline commands ##
    ##########################
    
    try:
        CMDLINE_DEVICE = sys.argv[1].strip()
        dolog("Target: {target}".format(target=CMDLINE_DEVICE))
        CMDLINE_ZONE = int(sys.argv[2].strip())
        dolog("ZONE: {zone}".format(zone=CMDLINE_ZONE))

        CMDLINE_CMD = sys.argv[3].strip()
        dolog("CMD : {cmd}".format(cmd=CMDLINE_CMD))
        CMDLINE_VALUE1 = 0
        ## check the device exists
        if CMDLINE_DEVICE in DEVICES:
            dolog("Using device: {device}".format(device=CMDLINE_DEVICE))
        else:
            dolog("No device found matching: {device}".format(device=CMDLINE_DEVICE))
            raise SystemExit()
        if CMDLINE_CMD in DEVICES[CMDLINE_DEVICE][0]:
            dolog("Static command found: {cmd}".format(cmd=CMDLINE_CMD))
        elif CMDLINE_CMD in DEVICES[CMDLINE_DEVICE][1]:
            dolog("Checking variable command {cmd}".format(cmd=CMDLINE_CMD))
            CMDLINE_VALUE1 = int(sys.argv[4].strip())
            dolog("Variable command found: {cmd} {var}".format(cmd=CMDLINE_CMD, var=CMDLINE_VALUE1))
        else:
            raise SystemExit()
    except:
        dolog("Valid command not found")
        print CMDLINE_INFO
        raise SystemExit()
    
    bridge = milight_bridge()
    for icount in range(0, UDP_MAX_TRY):
        try:
            dolog("Cycle number: {cycle}".format(cycle=cyclenr))
            bulbCommand = iBoxV6Commands(CMDLINE_DEVICE, CMDLINE_CMD, CMDLINE_VALUE1)
            dolog("Light command: {Command}".format(Command=hexstr(bulbCommand, ' ')))
            useZone = CMDLINE_ZONE
            dolog("Zone: {Zone}".format(Zone=useZone))

            Checksum = sum(bulbCommand) & 0xff
            dolog("Checksum: {checksum}".format(checksum=Checksum))

            sendCommand = bridge.buildCmd(bulbCommand, useZone, Checksum)

            dolog("Sending command: {command}".format(command=hexstr(sendCommand, ' ')))

            dataReceived, addr = bridge.sndCommand(bytearray.fromhex(sendCommand))
            dolog("Receiving response: {}".format( hexstr(dataReceived, ' ')) )
            break

        except socket.timeout:
            dolog("Timeout on command: {command}".format(command=hexstr(sendCommand, ' ')))
            continue

    

#"192.168.0.34"