#!/usr/bin/env python
import pika
import sys





line_count = 0

def sendcommand(line):
    global line_count
    line_count += 1
    channel.basic_publish(exchange='',
                          routing_key='lightserver', body=line.rstrip())
    print " [x] Sent {}".format(line.rstrip())

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
    if '-' in sys.argv:
        read_from_stdin()
    else:
        prompt_user()

connection.close()
