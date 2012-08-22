#!/usr/bin/python
# -*- coding: utf-8 -*-

# tamaserver.py
# This file is part of TAMA
# 
# Copyright (C) 2012 - Enrico Polesel
# 
# TAMA is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# any later version.
# 
# tama is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with tama. If not, see <http://www.gnu.org/licenses/>.

#~ import os
#~ import thread
#~ import socket
#~ import signal
#~ import subprocess
import datetime
#~ import time
#~ import sqlalchemy
#~ import sqlalchemy.orm
import ConfigParser
import argparse
import sys

TAMA_CONFIG_FILE = "/etc/tama/tama.ini"


tama_config = ConfigParser.ConfigParser()
tama_config.read(TAMA_CONFIG_FILE)
try:
    debug = tama_config.getint("default","debug")
    #tama_dir = tama_config.get("default","tama_dir")

except:
    print "[tamaquery] error while parsing "+free_policy_file
    print "[tamaquery] exiting..."

try:
    import tamascommon as tama
except:
    print "[tamaquery] error while importing tamascommon"
    exit(2)

def debug_message (level, msg):
    if level <=debug:
        print "[Tamaquery - debug] "+str(msg)
    

def listclient(options):
    """
    List information about all clients
    
    """

    clients = tama.session.query(tama.Client).all()
    
    out=""
    out2=""
    if options.id:
        out += "%3s|" %("id")
        out2 += "%3s|" %("")
        
    out += "%-16s" % ("Name")
    out2 += "%-16s" % ("")
    if options.ip:
        out += "|%-16s" % ("IP")
        out2 += "|%-16s" % ("")
    if options.mac:
        out += "|%-18s" % ("mac")
        out2 += "|%-18s" % ("")
    if options.users:
        out += "|%-6s" % ("Users")
        out2 += "|%-6s" % ("")
    if options.state:
        out += "|%-50s" % ("Client state")
        out2 += "|%-50s" % ("")
    print out
    print out2
    
    for client in clients:
        out=""
        if options.id:
            out += "%3d|" %(client.id)
        out += "%-16s" % (client.name)
        if options.ip:
            out+="|%-16s" % (client.ip)
        if options.mac:
            out+="|%-18s" % (client.mac)
        
        
        if options.users:
            out+= "|%-6d" % (client.users_human())
        if options.state:
            out+= "|%-40s" % (client.str_state())
        
        print out
        
    

def examine(options):
    """
    Print all informations about one client
    
    """
    try:
        client = tama.session.query(tama.Client).\
                filter(tama.Client.name==options.name).one()
    except:
        print "Unable to find a client named "+options.name
        exit(1)
    else:
        print "I have this information about this client: "
        print "%-16s %s" % ("id", str(client.id))
        print "%-16s %s" % ("name", str(client.name))
        print "%-16s %s" % ("ip", str(client.ip))
        print "%-16s %s" % ("mac", str(client.mac))
        print "%-16s %d" % ("users", client.users_human())
        print "%-16s %s" % ("state", client.str_state())
        print "%-16s %s" % ("auto_on", str(client.auto_on))
        print "%-16s %s" % ("last_off", str(client.last_off))
        print "%-16s %s" % ("always_on", str(client.always_on))
        print "%-16s %s" % ("count", str(client.count))
        print "%-16s %s" % ("last_on", str(client.last_on))
        print "%-16s %s" % ("auto_off", str(client.auto_off))
        print "%-16s %d°C @ %s" % ("last temperature", 
                                    client.temperatures[-1].measure,
                                    client.temperatures[-1].date)
        print
    

def refresh(options):
    tama.refresh_data()

def temperatures(options):
    output=[]
    if options.fromdate!=None:
        try:
            fromdate = datetime.datetime(options.fromdate[0],
                                        options.fromdate[1],
                                        options.fromdate[2],
                                        options.fromdate[3],
                                        options.fromdate[4])
        except:
            print "Invalid date!"
            return 
        else:
            temperatures=[]
            for client, temperature in  tama.session.query(tama.Client, 
                                        tama.Temperature).\
                                        filter(tama.Client.id==tama.Temperature.client_id).\
                                        filter(tama.Client.name==options.name).\
                                        filter(tama.Temperature.date >= fromdate).\
                                        order_by(tama.Temperature.date).all():
                temperatures.append(temperature)
            output = temperatures[:options.number]
    else:
        if options.todate==None:
            todate=datetime.datetime.now()
        else:
            try:
                todate = datetime.datetime(options.todate[0],
                                            options.todate[1],
                                            options.todate[2],
                                            options.todate[3],
                                            options.todate[4])
            except:
                print "Invalid date!"
                return
        temperatures=[]
        for client, temperature in  tama.session.query(tama.Client, 
                                    tama.Temperature).\
                                    filter(tama.Client.id==tama.Temperature.client_id).\
                                    filter(tama.Client.name==options.name).\
                                    filter(tama.Temperature.date <= todate).\
                                    order_by(tama.Temperature.date.desc()).all():
            temperatures.append(temperature)
        output = temperatures[:options.number]
        output.reverse()
    
    for temperature in output:
        print "%-32s %4d°C" % (temperature.date, temperature.measure)
    

def switchon(options):
    """
    Try to switch on one client
    
    """
    try:
        client = tama.session.query(tama.Client).\
                        filter(tama.Client.name==options.name).one()
    except:
        print "Unable to find a client named "+options.name
        return
    else:
        if client.state > 4:
            print "The client is already on!"
            if not options.force:
                return
            else:
                print "Forcing switch on"
        if client.state == 4:
            print "I don't manage this client!"
            if not options.force:
                return
            else:
                print "Forcing switch on"
        if options.wait:
            client.switch_on()
        else:
            client.switch_on_simple()
    

def string_to_bool(string):
    """
    Convert a string (True/False) in a boolean value
    
    """
    string = string.lower().strip()
    if string in [ "true", "1", "yes" ]:
        return True
    elif string in [ "false", "0", "no" ]:
        return False
    else:
        raise Exception ("Invalid bool string")

def validate_ip(string):
    """
    Return string if string is a IP, else raise an exception
    
    """
    ip = string.split(".")
    if len(ip)!=4:
        raise Exception("Invalid IP")
    for i in range(4):
        try:
            num = int(ip[i])
        except:
            raise Exception("Invalid IP")
        else:
            if num<0 or num>255:
                raise Exception("Invalid IP")
    return string

def validate_mac(string):
    """
    Return string if string is a MAC address, else raise an exception
    
    """
    mac = string.split(":")
    if len(mac)!=6:
        raise Exception("Invalid MAC address")
    for i in range(6):
        try:
            num = int(mac[i],16)
        except:
            raise Exception("Invalid MAC address")
        else:
            if num<0 or num>255:
                raise Exception("Invalid MAC address")
    return string

def get_bool(description="Insert a boolean value",default=None):
    """
    Get a boolean value asking for description
    
    If default is given and the user insert nothing then default is returned
    If user give an invalid bool then the funciton will ask again for a bool
    
    """
    if default is None:
        request = ""
    elif default not in [ True, False ]:
        try:
            defaultB = string_to_bool(default)
        except:
            debug_message(2,"get_bool: invalid default argument, not boolean!")
            default = None
            request = ""
        else:
            request = "("+default+") "
    else:
        default = str(default)
        request = "("+default+") "
    while(1):
        string = raw_input(description+""+request)
        if default is not None and string == "":
            string = default
        try:
            bool = string_to_bool(string)
        except:
            print "Please insert a valid boolean value"
        else:
            break
    return bool

def get_name(default=None):
    """
    Get the name of a client

    If default is given and the user insert no name then default is retured
    Else it will ask again for the client name

    """
    if default is None:
        request = ""
    else:
        request = "("+default+") "
    while(1):
        name = raw_input("Name: "+request).strip()
        if default is not None:
            if name == "":
                name = default
        if name != "":
            break
        else:
            print "Please insert a name"
    return name

def get_ip(default=None):
    """
    Get an IP address
    
    If default is given and the user insert nothing then default is returned
    If user give an invalid IP then the funciton will ask again for a IP
    
    """
    if default is None:
        request = ""
    else:
        try:
            validate_ip(default)
        except:
            debug_message(2,"get_ip: invalid ip as argument")
            default = None
            request = ""
        else:
            request = "("+default+") "
    while(1):
        ip = raw_input("IP: "+request).strip()
        if default is not None and ip == "":
            ip = default
        try:
            validate_ip(ip)
        except:
            print "Please insert a valid IP address"
        else:
            break
    return ip

def get_mac(default=None):
    """
    Get an MAC address
    
    If default is given and the user insert nothing then default is returned
    If user give an invalid MAC then the funciton will ask again for a MAC
    
    """
    if default is None:
        request = ""
    else:
        try:
            validate_mac(default)
        except:
            debug_message(2,"get_mac: invalid mac as argument")
            default = None
            request = ""
        else:
            request = "("+default+") "
    while(1):
        mac = raw_input("MAC address: "+request).strip()
        if default is not None and mac == "":
            mac = default
        try:
            validate_mac(mac)
        except:
            print "Please insert a valid MAC address"
        else:
            break
    return mac

def get_state(default=None):
    """
    Get a state
    
    If default is given and the user insert nothing then default is returned
    If user give an invalid state then the funciton will ask again for a state
    
    """
    if default is None:
        request = ""
    else:
        try:
            defaultN = int(default)
        except:
            debug_message(2,"get_state: invalid state as argument")
            default = None
            request = ""
        else:
            request = "("+str(default)+") "
    print "List of valid states by number:"
    print "0: morto (manuale)"
    print "1: spento, accensione remota non funzionante"
    print "2: spento (non da tamaserver)"
    print "3: spento da tamaserver"
    print "4: non gestito da tamaserver"
    print "5: acceso, tamaclient non funzionante"
    print "7: acceso"
    while (1):
        state = raw_input("State number "+request).strip()
        if default is not None and state=="":
            state = default
        try:
            stateN = int(state)
        except:
            print "Please insert an integer"
        else:
            if stateN in [ 0, 1, 2 ,3 ,4, 5, 7]:
                break
            else:
                print "Please insert a valid numeber"
    return stateN


def addclient_string(dataString):
    """
    Add a new client in the database taking data from a string
    
    dataString contain comma separeted values in this order:
    - name
    - ip
    - mac
    - state (Number)
    - auto_on (True/False)
    - auto_off (True/False)
    - always_on (True/Flase)
    - count (True/False)
    
    """
    dataArray = dataString.split(",")
    name = dataArray[0]
    ip = validate_ip(dataArray[1])
    mac = validate_mac(dataArray[2])
    state = int(dataArray[3])
    auto_on = string_to_bool(dataArray[4])
    auto_off = string_to_bool(dataArray[5])
    always_on = string_to_bool(dataArray[6])
    count = string_to_bool(dataArray[7])

    tama.session.add(tama.Client(name, ip, mac, state, auto_on, auto_off, always_on, count))
    tama.session.commit()
    print "Client "+name+" added"

def addclient_file(clientFile):
    """
    Add client from file, one client at line
    
    each line contains comma separeted values in this order:
    - name
    - ip
    - mac
    - state (Number)
    - auto_on (True/False)
    - auto_off (True/False)
    - always_on (True/Flase)
    - count (True/False)
    
    """
    
    for line in clientFile:
        if line.strip()=="":
            continue
        if line.startswith("#"):
            print line.lstrip("#").strip()
            continue
        addclient_string(line)

def addclient_interactive():
    """
    Add a new client asking information from terminal
    
    """
    name = get_name()
    ip = get_ip()
    mac = get_mac()
    state = get_state()
    auto_on = get_bool("Auto on",True)
    auto_off = get_bool("Auto off",True)
    always_on = get_bool("Always on",False)
    count = get_bool("Count",True)
    
    tama.session.add(tama.Client(name, ip, mac, state, auto_on, auto_off, always_on, count))
    tama.session.commit()

def addclient(options):
    """
    Main function for the addclient option
    
    This function choose and call the right function between:
    - addclient_interactive
    - addclient_file
    
    """
    if options.file is None:
        addclient_interactive()
    else:
        addclient_file(options.file)
        options.file.close()


# Parser definitions
mainParser = argparse.ArgumentParser(description="A tool to query tama database")
mainParser.add_argument("action",
                        choices=["listclient",
                                    "examine",
                                    "refresh",
                                    "temperatures",
                                    "switchon",
                                  #  "switchoff",
                                    "addclient",
                                    ],
                        help="What tamaquery have to do")
mainParser.add_argument("args",
                        nargs=argparse.REMAINDER,
                        help="Arguments for the action")

listclientParser = argparse.ArgumentParser(description="List information\
                                    about all clients",
                                    prog=sys.argv[0]+" listclient")
listclientParser.add_argument("--state", 
                            help="Print the state of clients",
                            action="store_true")
listclientParser.add_argument("--users",
                            help="Print the number of user for client",
                            action="store_true")
listclientParser.add_argument("--ip",
                            help="Print the ip address of the client",
                            action="store_true")
listclientParser.add_argument("--mac",
                            help="Print the mac address of the client",
                            action="store_true")
listclientParser.add_argument("--id",
                            help="Print the id of the client",
                            action="store_true")

examineParser = argparse.ArgumentParser(description="Examine all \
                                        informations about a client",
                                        prog = sys.argv[0]+" examine")
examineParser.add_argument("name",
                            help="The name of the client to query about")

refreshParser = argparse.ArgumentParser(description="Refresh the main\
                                        database",
                                        prog = sys.argv[0]+" refresh")

temperaturesParser = argparse.ArgumentParser(description="Print the\
                                        temperatures recorded for a client",
                                        prog = sys.argv[0]+" temperatures")
temperaturesParser.add_argument("name",
                            help="The name of the client to query about")
temperaturesParser.add_argument("--number","-n",
                            help="The number of record to show",
                            type=int,
                            default=20)
temperaturesParserDateGroup = temperaturesParser.add_mutually_exclusive_group()
temperaturesParserDateGroup.add_argument("--fromdate",
                            help="The begin date",
                            metavar=("yyyy","mm","dd","hh","mm"),
                            type=int,
                            nargs=5
                            )
temperaturesParserDateGroup.add_argument("--todate",
                            help="The end date",
                            metavar=("yyyy","mm","dd","hh","mm"),
                            type=int,
                            nargs=5
                            )

switchonParser = argparse.ArgumentParser(description="Switch on a client",
                                        prog = sys.argv[0]+" switchon")
switchonParser.add_argument("name",
                            help="The name of the client to query about"
                            )
switchonParser.add_argument("--wait", "-w",
                            help="Wait to complete switch on",
                            action="store_true")
switchonParser.add_argument("--force","-f",
                            help="Force to switch on the client",
                            action="store_true")

addclientParser = argparse.ArgumentParser(description="Add a new client in the database",
                                          prog = sys.argv[0]+" addclient")
addclientParser.add_argument("--file", "-f",
                             help="Load client data from file (one client for line)",
                             type=argparse.FileType('r')
                            )

mainNS = mainParser.parse_args()
debug_message(4,"action: "+mainNS.action)
debug_message(4,"args: "+str(mainNS.args))
if mainNS.action=="listclient":
    listclientNS = listclientParser.parse_args(mainNS.args)
    listclient(listclientNS)
elif mainNS.action=="examine":
    examineNS = examineParser.parse_args(mainNS.args)
    examine(examineNS)
elif mainNS.action=="refresh":
    refreshNS = refreshParser.parse_args(mainNS.args)
    refresh(refreshNS)
elif mainNS.action=="temperatures":
    temperaturesNS = temperaturesParser.parse_args(mainNS.args)
    temperatures(temperaturesNS)
elif mainNS.action=="switchon":
    switchonNS = switchonParser.parse_args(mainNS.args)
    switchon(switchonNS)
elif mainNS.action=="addclient":
    addclientNS = addclientParser.parse_args(mainNS.args)
    addclient(addclientNS)


