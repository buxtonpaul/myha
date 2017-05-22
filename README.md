# myha
Simple home automation scripting using various libraries


Depends on limitlesled much of the code is inspired by / lifted from https://github.com/soldag/python-limitlessled.git

and Pika
pip install pika

The receiver will listen for messages and send them on to the limitlessled bridge.
Messages are of the form
either
lightgroup : action <value>
trigger :
Where action can be
    on, off, brightness, temperature, colour (depending on the colour group)


The light groups will simply pass on the commands as provided
The trigger will allow further processing e.g. 
trigger : doorswitch
Would invoke a customer command in the receiver which will turn on a light and then after a number of seconds turn it off. In order to prevent the light toggling off due to multiple triggers


