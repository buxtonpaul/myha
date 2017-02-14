#!/usr/bin/python
''' utility modiule'''
def dolog(msg):
    ''' Log a message'''
    print "DEBUG: {}".format(msg)

def hexstr(vals, sep=', '):
    ''' Print the provided list as a hex string, using
    the optional seperator to determine how they are seperated'''
    return'[{}]'.format(sep.join(hex(x) for x in vals))
