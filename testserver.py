#!/usr/bin/env python
import pika
import time, threading


# create a single lock that is used by all threads
hall_lock = threading.Lock()
hall_counter = 0


groups=["hall","bedroom"]

def timehandler(selflocker,  group):
    global hall_counter
    with selflocker:
        if hall_counter == 0:
            print "Error, attempt to decrement zero counter"
        else:
            hall_counter = hall_counter -1
            if hall_counter == 0:
                # this is the last event outstanding so we can turn the group off
               # group.off = True
               print "Counter empty"
            else:
                print("Counter decremented {}".format(hall_counter))





def rabbitcallback(ch, method, properties, body):
    print " [x] Received %r" % body
    # parse the command
    params = body.split()
    group = params[0]
    global hall_counter
    if group in groups:
        # we have a valid group
        print "Group {} found".format(params[0])
        #targetgroup = groups[group]
    elif (params[0] == 'door') | (params[0] == 'pir'):
        with hall_lock:
            print "incrementing counter hall counter {} +1".format(hall_counter)           #hall.on = True
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






