##############################################################################
# Nimble Connection Manager Version Checker by David Richey (City of Conroe) #
#                               v0.1 3/28/2016                               #
##############################################################################

from nimbleapi.nimbleapi import nimbleapi
from subprocess import check_output
import os, sys, time, getpass

ms_initiators = []


def get_inits():
    global ms_initiators
    nimble = nimbleapi(hostname = raw_input("Hostname to connect to: "),
                       username = raw_input("Username: "),
                       password = getpass.getpass())

    nimble.initiator_read()
    if len(nimble.dict_initiators) <= 0:
        print "No initiators were found on array %s or there was an error gathering them!" % (nimble.hostname)
        sys.exit()
    else:
        for i in range(len(nimble.dict_initiators)):
            #print nimble.dict_initiators[i]['initiator_group_name'] + ": " + nimble.dict_initiators[i]['iqn']
            if nimble.dict_initiators[i]['iqn'].find("microsoft") > -1:
                comp_name = nimble.dict_initiators[i]['iqn'].split(":")[1].split(".")[0]
                #print comp_name
                if not comp_name in ms_initiators:
                    #print "YAY!"
                    ms_initiators.append(comp_name)
        
                

def check_ncm_version():           
    global ms_initiators
    if len(ms_initiators) <= 0:
        print "No Microsoft IQNs were found!"
        sys.exit()
    else:
        print "\nStarting checks. This may take some time...\n"
        for computer in ms_initiators:
            cmd = 'wmic /node:\"%s\" product where \"name like \'%%Nimble%%\'\" get name, version' % (computer)
            try:
                print computer
                output = check_output(cmd, shell=True)
                if not output.strip("\r\n"):
                    print "No Instance(s) Found\n"
                else:
                    print output.strip("\r\n")+"\n"
            except:
                print "Couldn't get a return from %s \n" % (computer)
                pass
        

print "########  NCM Version Checker by David Richey (City of Conroe)  ########\n"
starttime = time.time()
get_inits()
check_ncm_version()
print "Total operations took %d seconds!" % (long(time.time() - long(starttime)))
