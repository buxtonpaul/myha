#!/usr/bin/python
import pika
import sys
import string



codes={

    "87344":"doorbell",
    "5592405":"pir",
    "5332048":"door"
}


line_count = 0

def sendcommand(line):
    
    credentials = pika.PlainCredentials(user, passwd)
    connection = pika.BlockingConnection(pika.ConnectionParameters(
                                          host=host,credentials=credentials))
    channel = connection.channel()
    channel.queue_declare(queue=rabqueue)
   
    retries = 3
    while retries > 0:
        retries =retries -1
        try:
            channel.basic_publish(exchange='', routing_key=rabqueue, body=line.rstrip())
        except:
            print "Something wasn't happy :-("
        else:
            print " [x] Sent {}".format(line.rstrip())
            break
    connection.close()

def read_from_stdin():
# If there's input ready, do something, else do something
# else. Note timeout is zero so select won't block at all.
    while True:
        line = sys.stdin.readline()
        print "Debug {}".format(line)
        messge=line.split()
        if (messge[1] in codes):
           print "Found {}".format(messge[1])
           sendcommand(codes[messge[1]])
        else:
	           print "not found {}".format(messge[1])
       

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




if __name__ == "__main__":
    if '-' in sys.argv:
        read_from_stdin()
    elif '+' in sys.argv:
        prompt_user()
    line=string.join(sys.argv[1:])
    sendcommand(line)
