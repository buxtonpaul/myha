#!/usr/bin/env python
import pika
import sys
import string





line_count = 0

def sendcommand(line):
    global line_count
    retries = 3
    global connection,channel   
    while retries > 0:
        retries =retries -1
        
        line_count += 1
        try:
            channel.basic_publish(exchange='',
                                  routing_key='lightserver', body=line.rstrip())
        except pika.exceptions.ConnectionClosed:
            print "Connection was closed, retrying..."
            connection = pika.BlockingConnection(pika.ConnectionParameters(
host='localhost'))
            channel = connection.channel()
        else:
            print " [x] Sent {}".format(line.rstrip())
            break
def read_from_stdin():
    global line_count
    for line in sys.stdin:
        sendcommand(line)

def prompt_user():
    print 'Type "quit" to exit.'
    while (True):
        line = raw_input('PROMPT> ')
        if line == 'quit':
            sys.exit()
        sendcommand(line)


connection = pika.BlockingConnection(pika.ConnectionParameters(
        host='localhost'))
channel = connection.channel()

channel.queue_declare(queue='lightserver')

if __name__ == "__main__":
#    if '-' in sys.argv:
#        read_from_stdin()
#    else:
#        prompt_user()
    line=string.join(sys.argv[1:])
    sendcommand(line)
connection.close()
