##############################################################################
# Nimble Connection Manager Version Checker by David Richey (City of Conroe) #
#                             v0.2.2 4/6/2016                                #
##############################################################################

from nimbleapi.nimbleapi import nimbleapi
from subprocess import check_output
import os, sys, time, getpass, signal

ms_initiators = []


def log_out(message):
    try:
        outputfile.write(message)
    except:
        pass

def get_inits():
    global ms_initiators
    nimble = nimbleapi(hostname = raw_input("Hostname to connect to: "),
                       username = raw_input("Username: "),
                       password = getpass.getpass())

    nimble.initiator_read()
    if len(nimble.dict_initiators) <= 0:
        print "No initiators were found on array %s or there was an error gathering them!" % (nimble.hostname)
        time.sleep(2)
        sys.exit()
    else:
        
        for initiator in nimble.dict_initiators:
            #print nimble.dict_initiators[i]['initiator_group_name'] + ": " + nimble.dict_initiators[i]['iqn']
            if nimble.dict_initiators[initiator]['iqn'].find("microsoft") > -1:
                comp_name = nimble.dict_initiators[initiator]['iqn'].split(":")[1].split(".")[0]
                #print comp_name
                if not comp_name in ms_initiators:
                    #print "YAY!"
                    ms_initiators.append(comp_name.encode('ascii'))
        
def check_ncm_version():           
    global ms_initiators
    if len(ms_initiators) <= 0:
        print "No Microsoft IQNs were found!"
        time.sleep(2)
        sys.exit()
    else:
        print "\nInitiators Found: %s" % (ms_initiators)
        log_out("Initiators that we found and are checking: %s\n" % (ms_initiators))
        print "\nStarting checks. This may take some time...\n"
        
        for computer in ms_initiators:
            cmd = 'wmic /node:\"%s\" product where \"name like \'%%Nimble%%\'\" get name, version' % (computer)
            try:
                print "*** %s ***" % (computer)
                log_out("*** %s ***\n" % (computer))
                output = check_output(cmd, shell=True)

                if not output.strip("\r\n"):
                    print "No Instance(s) Found\n"
                    log_out("No Instance(s) Found\n")
                else:
                    print output.strip("\r\n")+"\n"
                    log_out(output)
            except:
                print "Couldn't get a return from %s \n" % (computer)
                
                log_out("Couldn't get a return from %s \n" % (computer))
                pass

if __name__ == '__main__':

    print "########  NCM Version Checker by David Richey (City of Conroe)  ########\n"
    starttime = time.time()
    get_inits()
    try:
        outputfile = open(time.strftime("%Y-%m-%d %H-%M-%S"+".txt"), "w")
    except:
        print "Could not create file for logging " + sys.exc_info()[0]
        
    check_ncm_version()
    outputfile.close()
    print "Total operations took %d seconds!" % (long(time.time() - long(starttime)))
