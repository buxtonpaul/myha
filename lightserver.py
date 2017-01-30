#!/usr/bin/env python
import pika
import time, threading

from limitlessled.bridge import Bridge
from limitlessled.group.rgbw import RGBW
from limitlessled.group.white import WHITE

bridge = Bridge('192.168.0.34')
bedroom  =bridge.add_group(1, 'bedroom', RGBW)
# A group number can support two groups as long as the types differ
nightlight = bridge.add_group(1, 'nightlight', BRIDGE_LED)
hall = bridge.add_group(2, 'hall', RGBW)
spare_room = bridge.add_group(2, 'spare_room', WHITE)


# create a single lock that is used by all threads
hall_lock = threading.Lock()
hall_counter = 0

def timehandler(selflocker,  group):
    global hall_counter
    global hall
    with selflocker:
        if hall_counter == 0:
            print "Error, attempt to decrement zero counter"
        else:
            hall_counter = hall_counter -1
            if hall_counter == 0:
                # this is the last event outstanding so we can turn the group off
               # group.off = True
               hall.On=False
               print "Counter empty"
            else:
                print("Counter decremented {}".format(hall_counter))


def rabbitcallback(ch, method, properties, body):
    print " [x] Received %r" % body
    # parse the command
    params = body.split()
    group = params[0]
    global hall
    if group in bridge.groups:
        # we have a valid group
        targetgroup = bridge.groups[group]
        if params[1] == 'on':
            targetgroup.on = True
        elif params[1] == 'off':
            targetgroup.on = False
        else:
            # we assume this is probably a brightness call
            if params[1] == 'brightness':
                targetgroup.brightness = params[2]/100.0 #incoming brighness is done as a percentage
    elif (params[0] == 'door') | (params[0] == 'pir'):
        with hall_lock:
            print "incrementing counter hall counter {} +1".format(hall_counter)           
            hall.on = True
            # set a timer to go off after 15 seconds
            hall_counter=hall_counter + 1
            threading.Timer(15.0, timehandler, args=(hall_lock, group)).start()
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






