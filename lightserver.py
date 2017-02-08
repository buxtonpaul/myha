#!/usr/bin/env python
import pika
import time, threading

from  milight import Milightv6bridge,BridgeLight,White,RGBW
maxtries=3
#bridge = Milightbridge(IBOX_IP="192.168.0.34",UDP_MAX_TRY=MAXTRIES)
# parse a config file to get
# Bridges, zones and lights


bridge = Milightv6bridge( UDP_MAX_TRY=maxtries)
nightlight = BridgeLight("nightlight", 1, bridge)
spareroom = White("spareroom",1,bridge)
landinglight = RGBW("landinglight",2,bridge)
bedroom = RGBW("bedroom",1,bridge)

#create a dictionary storing names vs light objects
lights={"nightlight":nightlight, "spareroom":spareroom, "landinglight":landinglight, "bedroom":bedroom}

# create a single lock that is used by all threads
hall_lock = threading.Lock()
hall_counter = 0

def timehandler(selflocker,  group):
    global hall_counter
    global landinglight
    with selflocker:
        if hall_counter == 0:
            print "Error, attempt to decrement zero counter"
        else:
            hall_counter = hall_counter -1
            if hall_counter == 0:
                # this is the last event outstanding so we can turn the group off
               # group.off = True
               landinglight.off()
               print "Counter empty"
            else:
                print("Counter decremented {}".format(hall_counter))


def rabbitcallback(ch, method, properties, body):
    print " [x] Received %r" % body
    # parse the command
    params = body.split()
    if len(params) == 0:
        print "Empty Command string received"
        return
    group = params[0]

    global lights
    global landinglight
    global hall_counter
    if group in lights:
        # we have a valid group
        if len(params) <2:
            print "No parameters provided for group {}".format(params[0])
            return
        targetgroup = lights[group]
        if params[1] == 'on':
            targetgroup.lighton()
        elif params[1] == 'off':
            targetgroup.off()
        else:
            # Let the light handle calls it knows about!
            targetgroup.docommand(params[1:])
    elif (params[0] == 'door') | (params[0] == 'pir'):
        with hall_lock:
            print "incrementing counter hall counter {} +1".format(hall_counter)
            landinglight.lighton()
            # set a timer to go off after 15 seconds
            hall_counter = hall_counter + 1
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






