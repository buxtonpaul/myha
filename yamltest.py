# -*- coding: utf-8 -*-
"""
Created on Tue Feb 14 12:47:25 2017

@author: paul.buxton
"""

import yaml

sections={}

with open ("config.yml",'r') as ymlfile:
    cfg=yaml.load(ymlfile)
    ymlfile.close()
    
    
    if cfg["bridges"]:
        for bridgekey,bridgeval in cfg["bridges"].items():
            # check if the bridge is one we can handle then add it!
            if bridgeval["bridgetype"] == "mifi6":
                print "Bridge {} @ {}".format(bridgekey,bridgeval["bridgeip"])
                for key,val in bridgeval.items():
                    if key == "rgbw":
                        print "Found RGBW lights {}".format(val)
                        for bulb,zone in val.items():
                            zonenum=int(zone)
                            print " Bulb {} with zone {} added to bridge {}".format(bulb,zonenum,bridgekey)
                    if key == "white":
                        print "Found White lights {}".format(val)
                        for bulb,zone in val.items():
                            zonenum=int(zone)
                            print " Bulb {} with zone {} added to bridge {}".format(bulb,zonenum,bridgekey)
                        
                    if key == "bridge":
                        print "Found bridge light {}".format(val)
                        for bulb,zone in val.items():
                            zonenum=int(zone)
                            print " Bulb {} with zone {} added to {}".format(bulb,zonenum,bridgekey)

            else:
                print "Unknown bridgetype {}".format(bridgeval["bridgetype"])