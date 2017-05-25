#!/usr/bin/python
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
                                  routing_key=rabqueue, body=line.rstrip())
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



import os
path=os.path.dirname(os.path.abspath(__file__))
configfile=path+"/rabbitsettings.txt"

conf= open(configfile,'r')
params=(conf.readline()).split()
user=params[0]
passwd=params[1]
host=params[2]
rabqueue=params[3]


credentials = pika.PlainCredentials(user, passwd)
connection = pika.BlockingConnection(pika.ConnectionParameters(
        host=host,credentials=credentials))

channel = connection.channel()

channel.queue_declare(queue=rabqueue)

if __name__ == "__main__":
    if '-' in sys.argv:
        read_from_stdin()
    elif '+' in sys.argv:
        prompt_user()
    line=string.join(sys.argv[1:])
    sendcommand(line)
connection.close()
