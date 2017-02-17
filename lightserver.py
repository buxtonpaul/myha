#!/usr/bin/env python
''' A module to expose control of the milightv6 bridge'''
import pika
import time
import threading
from milightv6 import Milightv6bridge

MAXTRIES = 3
#BRIDGE = Milightv6bridge(IBOX_IP="192.168.0.34",UDP_MAX_TRY=MAXTRIES)
# parse a config file to get
# Bridges, zones and lights


BRIDGE = Milightv6bridge(UDP_MAX_TRY=MAXTRIES)
BRIDGE.addbulb("BRIDGE", "nightlight", 1)
BRIDGE.addbulb("WHITE", "spareroom", 1)
BRIDGE.addbulb("RGBW", "bedroom", 1)
LANDINGLIGHT = BRIDGE.addbulb("RGBW", "landinglight", 2)


LIGHTS = BRIDGE.bulbs

triggers={}

triggers["door"]="landinglight"

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
        LIGHTS[triggers[group]].incrementref()
        threading.Timer(15.0, timehandler, args=[triggers[group]]).start()
    elif group == "threads":
        # print out the currently running threads
        threads=threading.enumerate()
        for cur in threads:
            print "Known thread {}".format(cur)

    else:
        print 'Unknown command {}'.format(params[0])









connection = pika.BlockingConnection(pika.ConnectionParameters(
        host='localhost'))
channel = connection.channel()

channel.queue_declare(queue='lightserver')


channel.basic_consume(rabbitcallback,
                      queue='lightserver',
                      no_ack=True)

print(' [*] Waiting for messages. To exit press CTRL+C')
channel.start_consuming()






