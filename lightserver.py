#!/usr/bin/env python
''' A module to expose control of the milightv6 bridge'''
import pika
import time, threading

from  milightv6 import Milightv6bridge
MAXTRIES = 3
#bridge = Milightv6bridge(IBOX_IP="192.168.0.34",UDP_MAX_TRY=MAXTRIES)
# parse a config file to get
# Bridges, zones and lights


BRIDGE = Milightv6bridge(UDP_MAX_TRY=MAXTRIES)
BRIDGE.addbulb("BRIDGE", "nightlight", 1)
BRIDGE.addbulb("WHITE", "spareroom", 1)
BRIDGE.addbulb("RGBW", "bedroom", 1)
LANDINGLIGHT = BRIDGE.addbulb("RGBW", "landinglight", 2)

LIGHTS = BRIDGE.bulbs

# create a single lock that is used by all threads
HALL_LOCK = threading.Lock()
HALL_COUNTER = 0

def timehandler(selflocker, group):
    ''' function to handle timer event'''
    with selflocker:
        if HALL_COUNTER == 0:
            print "Error, attempt to decrement zero counter"
        else:
            global HALL_COUNTER #  we update the gobal count hall counter here
            HALL_COUNTER = HALL_COUNTER -1
            if HALL_COUNTER == 0:
                # this is the last event outstanding so we can turn the group off
                # group.off = True
                LANDINGLIGHT.off()
                print "Counter empty"
            else:
                print "Counter decremented {}".format(HALL_COUNTER)


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
    elif (params[0] == 'door') | (params[0] == 'pir'):
        with HALL_LOCK:
            global HALL_COUNTER #  we will be updating the hall counter here
            print "incrementing counter hall counter {} +1".format(HALL_COUNTER)
            LANDINGLIGHT.lighton()
            # set a timer to go off after 15 seconds
            HALL_COUNTER = HALL_COUNTER + 1
            threading.Timer(15.0, timehandler, args=(HALL_LOCK,group)).start()
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






