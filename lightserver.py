#!/usr/bin/env python
''' A module to expose control of the milightv6 bridge'''
import pika
import time
import threading
import yaml

from milightv6 import Milightv6bridge


def timehandler(group):
    ''' function to handle timer event'''
    if group in LIGHTS:
        LIGHTS[group].decrementref()
    else:
        print("Unknown group called")

def rabbitcallback(ch, method, properties, body):
    print " [x] Received %r" % body
    # parse the command
    params = body.split()
    if len(params) == 0:
        print "Empty Command string received"
        return
    group = params[0]


    if group in LIGHTS:
        # we have a valid group
        if len(params) < 2:
            print "No parameters provided for group {}".format(params[0])
            return
        targetgroup = LIGHTS[group]
        if params[1] == 'on':
            targetgroup.lighton()
        elif params[1] == 'off':
            targetgroup.off()
        else:
            # Let the light handle calls it knows about!
            targetgroup.docommand(params[1:])
    elif group in triggers:
        LIGHTS[triggers[group]["light"]].incrementref()
        threading.Timer(int(triggers[group]["time"]), timehandler, args=[triggers[group]["light"]]).start()
    elif group == "threads":
        # print out the currently running threads
        threads=threading.enumerate()
        for cur in threads:
            print "Known thread {}".format(cur)

    else:
        print 'Unknown command {}'.format(params[0])










MAXTRIES = 3
#BRIDGE = Milightv6bridge(IBOX_IP="192.168.0.34",UDP_MAX_TRY=MAXTRIES)
# parse a config file to get
# Bridges, zones and lights

LIGHTS={}

sections = {}

with open("config.yml", 'r') as ymlfile:
    cfg = yaml.load(ymlfile)
    ymlfile.close()
    if cfg["bridges"]:
        for bridgekey, bridgeval in cfg["bridges"].items():
            # check if the bridge is one we can handle then add it!
            if bridgeval["bridgetype"] == "mifi6":
                print "Bridge {} @ {}".format(bridgekey, bridgeval["bridgeip"])
                curbridge=Milightv6bridge(UDP_MAX_TRY=MAXTRIES)
                for key, val in bridgeval.items():
                    if key == "rgbw":
                        print "Found RGBW lights {}".format(val)
                        for bulb, zone in val.items():
                            zonenum = int(zone)
                            print " Bulb {} with zone {} added to bridge {}".format(bulb, zonenum, bridgekey)
                            curlight=curbridge.addbulb("RGBW",bulb,zonenum)
                            LIGHTS[bulb]=curlight
                    if key == "white":
                        print "Found White lights {}".format(val)
                        for bulb, zone in val.items():
                            zonenum = int(zone)
                            print " Bulb {} with zone {} added to bridge {}".format(bulb, zonenum, bridgekey)
                            curlight=curbridge.addbulb("WHITE",bulb,zonenum)
                            LIGHTS[bulb]=curlight
 
                    if key == "bridge":
                        print "Found bridge light {}".format(val)
                        for bulb, zone in val.items():
                            zonenum = int(zone)
                            print " Bulb {} with zone {} added to {}".format(bulb, zonenum, bridgekey)
                            curlight=curbridge.addbulb("BRIDGE",bulb,zonenum)
                            LIGHTS[bulb]=curlight
                    

            else:
                print "Unknown bridgetype {}".format(bridgeval["bridgetype"])
    
    if cfg["triggers"]:
        # We have a section with triggers
        triggers=cfg["triggers"]
    else:
        triggers = {}


connection = pika.BlockingConnection(pika.ConnectionParameters(
        host='localhost'))
channel = connection.channel()

channel.queue_declare(queue='lightserver')


channel.basic_consume(rabbitcallback,
                      queue='lightserver',
                      no_ack=True)

print(' [*] Waiting for messages. To exit press CTRL+C')
channel.start_consuming()






