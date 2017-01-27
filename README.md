# myha
Simple home automation scripting using various libraries


Depends on limitlesled
pip install git+https://github.com/soldag/python-limitlessled.git

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
easiest way will be to use a semaphore.
E.g.

trigger -> turn on light, increment semaphore, set timer
timer -> decrement semaphore, if 0 turn off light.

Semaphore would be attached to the thing being contolled rather than trigger

