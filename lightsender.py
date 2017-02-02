#!/usr/bin/env python
import pika

connection = pika.BlockingConnection(pika.ConnectionParameters(
        host='localhost'))
channel = connection.channel()

channel.queue_declare(queue='lightserver')

channel.basic_publish(exchange='',
                      routing_key='lightserver',
                      body='bedroom BRIGHT 50')
print(" [x] Sent 'Hello World!'")
connection.close()

