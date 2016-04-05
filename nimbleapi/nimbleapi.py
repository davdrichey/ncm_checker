#################################################################
###
### Nimble Storage API wrapper
### 

import sys
import re
import time
import json
import logging

logging.basicConfig(format='%(asctime)s -- %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.DEBUG)

import requests
# DO YOU TRUST YOUR  CERTS?
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings()
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


class nimbleapi(object):

    #################################################################
    ###
    ### INIT
    ### 

    def __init__(self, hostname = 'testnimble.something.com', username = 'readonly', password = 'readonly', port = 5392, version = 'v1'):
        # INIT VARIABLES / SET DEFAULTS
        self.hostname = hostname
        self.port = port
        self.version = version
        self.username = username
        self.password = password
        
        logging.debug('setting up connection to: %s, with username: %s', self.hostname, self.username)

        # CONNECT TO NIMBLE AND GET TOKEN
        request_data = {'data':{'password':self.password,'username':self.username}}
        request_json = self.query(request_type = 'create', request_endpoint = 'tokens', request_data = request_data)
        self.session = request_json['data']['session_token']
        
        logging.debug('connection successful, session_token: %s', self.session)

        # INIT DICTIONARIES
        self.dict_access_control_records = {} 
        self.dict_arrays = {}
        self.dict_audit_log = {}
        self.dict_initiator_groups = {}
        self.dict_initiators = {}
        self.dict_performance_policies = {}
        self.dict_pools = {}
        self.dict_protection_schedules = {}
        self.dict_protection_templates = {}
        self.dict_replication_partners = {}
        self.dict_snapshot_collections = {}
        self.dict_snapshots = {}
        self.dict_volume_collections = {}
        self.dict_volumes = {}

    #################################################################
    ###
    ### MISC FUNCTIONS
    ### 

    def raise_error(self,description):
        # SIMPLE ERROR FUNCTION
        logging.info('RAISE ERROR: %s', description)
        sys.exit(1)

    def b_to_gb(self,size_bytes):
        # MAKE OUR SIZES HUMAN READABLE
        try:
            size_gb = (size_bytes/1024/1024/1024)
        except TypeError:
            size_gb = 0
        return size_gb

    def epoch_to_datetime(self, the_datetime):
        try:
            tmp_datetime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(the_datetime))
        except ValueError:
            tmp_datetime = '0000-00-00 00:00:00'
        return tmp_datetime

    def check_string(self,the_string):
        # MAKE SURE WE HAVE A STRING
        if the_string == '':
            self.raise_error('empty string')
        # MAKE SURE IT ONLY CONTAINS VALID CHARACTERS FOR NIMBLE
        matcher = re.match('^[a-zA-Z0-9\.:-]+$',the_string)
        if matcher is not None:
            return the_string
        else:
            self.raise_error(the_string + ' invalid string characters')

    def check_string_description(self,the_string):
        # MAKE SURE WE HAVE A STRING
        if the_string == '':
            self.raise_error('empty string')    
        # MAKE SURE IT ONLY CONTAINS VALID CHARACTERS FOR NIMBLE
        matcher = re.match('^[\sa-zA-Z0-9\.:-]+$',the_string)
        if matcher is not None:
            return the_string
        else:
            self.raise_error(the_string + ' invalid string characters')

    def check_bool(self,the_bool):
        # MAKE SURE WE HAVE A BOOLEAN
        if the_bool != True and the_bool != False:
            self.raise_error('expected boolean True or False')
        return the_bool

    def check_int(self,the_int):
        # MAKE SURE WE HAVE AN INT
        try:
            the_int = int(the_int)
        except TypeError:
            self.raise_error(the_int + ' is not an integer')
        return the_int

    #################################################################
    ###
    ### NIMBLE COMMUNICATIONS
    ### 

    def query(self, request_type, request_endpoint, request_data = '', expect_error = False):
        # SETUP NIMBLE URL
        nimble_url = 'https://%s:%s/%s/%s' % (self.hostname, self.port, self.version, request_endpoint)

        try:
            # OUR TYPE OF COMMUNICATIONS WITH OR WITHOUT DATA
            logging.debug('start query') 
            logging.debug('     type: %s', request_type)
            logging.debug('     endpoint: %s', request_endpoint)
            logging.debug('     data: %s', request_data)

            if request_type == 'create':
                if request_endpoint == 'tokens':
                    req = requests.post(nimble_url, data = json.dumps(request_data), verify=False)
                else:
                    req = requests.post(nimble_url, data = json.dumps(request_data), headers = {'X-Auth-Token': self.session}, verify=False)
                expect = 201
            elif request_type == 'update':
                req = requests.put(nimble_url, data = json.dumps(request_data), headers = {'X-Auth-Token': self.session}, verify=False)
                expect = 200
            elif request_type == 'read':
                req = requests.get(nimble_url, headers = {'X-Auth-Token': self.session}, verify=False)
                expect = 200
            elif request_type == 'delete':
                req = requests.delete(nimble_url, headers = {'X-Auth-Token': self.session}, verify=False)
                expect = 200
            else:
                self.raise_error('unknown query request type')

            # MAKE SURE WE GET A POSITIVE RESPONSE CODE OR STOP PROCESSING
            if req.status_code != expect and expect_error == False:
                error_info = req.json()
                print request_endpoint
                self.raise_error(error_info)

            #logging.debug('return data: %s', req.json())

            # RETURN ALL OF THE RETURNED JSON DATA
            return req.json()

        # REQUESTS MODULE ERRORS
        except requests.exceptions.RequestException as e:
            self.raise_error(str(request_endpoint) + 'Exception: ' + str(e))

    #################################################################
    ###
    ### ACCESS CONTROL RECORDS
    ### 

    def access_control_records_read(self):
        request_json = self.query(request_type = 'read', request_endpoint = 'access_control_records/detail')
        self.dict_access_control_records = request_json['data']
        
    def access_control_records_create(self, volume_name, initiator_group_name, boot_volume = False):
        volume_name = self.check_string(volume_name)
        initiator_group_name = self.check_string(initiator_group_name)

        # UPDATE DATA
        self.access_control_records_read()
        self.initiator_group_read()
        self.volume_read()

        # MAKE SURE VOLUME EXISTS
        if volume_name not in self.dict_volumes:
            self.raise_error('volume does not exist')

        vol_id = self.dict_volumes[volume_name]['id']

        # CHECK RECORDS
        if self.dict_volumes[volume_name]['access_control_records'] != None:
            if len(self.dict_volumes[volume_name]['access_control_records']) > 0:
                # WE LOOP THROUGH ALL OF THE KNOWN ACR TO MAKE SURE IT DOESN'T EXIST
                for item in self.dict_volumes[volume_name]['access_control_records']:
                    if item['initiator_group_name'] == initiator_group_name:
                        print 'initiator_group_name already exists'
                        return

        # GET INITIATOR_GROUP_ID
        if initiator_group_name not in self.dict_initiator_groups:
            self.raise_error('initiator group does not exist')

        initiator_group_id = self.dict_initiator_groups[initiator_group_name]['id']

        # WE NEED TO DETERMINE THE NEXT LUN ID FOR THE INITIATOR GROUP
        next_lun_id = 1

        # ALSO TRACK IF THE BOOT LUN ID IS ALREADY USED
        used_lun_id_zero = False

        # LOOP AND FIND IF INITIATOR GROUP IS APPLIED TO OTHER VOLUMES, INCREMENT 1
        for item in self.dict_access_control_records:
            if initiator_group_name == item['initiator_group_name']:
                if next_lun_id < item['lun']:
                    next_lun_id = item['lun'] + 1

                if item['lun'] == 0:
                    used_lun_id_zero = True

        # IF WE ARE TRYING TO MAKE A BOOT LUN
        if boot_volume == True:
            if used_lun_id_zero == False:
                next_lun_id = 0
            else:
                self.raise_error('lun id 0 has already been used')

        # CREATE ACR FOR VOLUME & INITIATOR_GROUP
        request_data = {'data':{'vol_id':vol_id,'initiator_group_id':initiator_group_id,'apply_to':'both','lun':int(next_lun_id)}}
        request_json = self.query(request_type = 'create', request_endpoint = 'access_control_records', request_data = request_data)

        # UPDATE DATA
        self.access_control_records_read()

        # RETURN THE ID, INCASE WE WANT TO USE IT FOR SOMETHING?
        return request_json['data']['id']


    def access_control_records_delete(self, volume_name, initiator_group_name):
        volume_name = self.check_string(volume_name)
        initiator_group_name = self.check_string(initiator_group_name)

        # UPDATE DATA
        self.access_control_records_read()
        self.initiator_group_read()
        self.volume_read()

        # IF THE VOLUME EXISTS
        if volume_name not in self.dict_volumes:
            self.raise_error('volume does not exist')

            # IF THE VOLUME HAS ANY ACCESS CONTROL RECORDS
            if len(self.dict_volumes[volume_name]['access_control_records']) > 0:

                # WE LOOP THROUGH ALL OF THE KNOWN ACR TO MAKE SURE IT EXISTS
                for item in self.dict_volumes[volume_name]['access_control_records']:
                    if item['initiator_group_name'] == initiator_group_name:

                        # IF WE FIND WHAT WE ARE LOOKING FOR, DELETE IT
                        request_json = self.query(request_type = 'delete', request_endpoint = 'access_control_records/' + item['acl_id'])

                        # UPDATE DATA
                        self.access_control_records_read()
                        self.initiator_group_read()
                        self.volume_read()

                        return
                

    #################################################################
    ###
    ### ARRAYS
    ### 

    def arrays_read(self):
        request_json = self.query(request_type = 'read', request_endpoint = 'arrays/detail')
        self.dict_arrays = request_json['data']
    
    #################################################################
    ###
    ### AUDIT LOG
    ### 

    def audit_log_read(self):
        request_json = self.query(request_type = 'read', request_endpoint = 'audit_log/detail')
        self.dict_audit_log = request_json['data']

    #################################################################
    ###
    ### INITIATOR GROUPS
    ### 

    def initiator_group_read(self):
        request_json = self.query(request_type = 'read', request_endpoint = 'initiator_groups/detail')
        for item in request_json['data']:
            self.dict_initiator_groups[item['full_name']] = item

    def initiator_group_create(self,initiator_group_name):
        initiator_group_name = self.check_string(initiator_group_name)

        # UPDATE DATA
        self.initiator_group_read()

        # GET INITIATOR_GROUP_ID
        if initiator_group_name in self.dict_initiator_groups:
            self.raise_error('initiator group already exists')

        request_data = {'data':{'name':initiator_group_name,'access_protocol':'fc'}}
        request_json = self.query(request_type = 'create', request_endpoint = 'initiator_groups', request_data = request_data)

        # UPDATE DATA
        self.initiator_group_read()
        # RETURN ID, IN CASE WE WANT TO USE IT
        return request_json['data']['id']

    def initiator_group_delete(self, initiator_group_name):
        # UPDATE DATA
        self.initiator_group_read()

        # GET INITIATOR_GROUP_ID
        if initiator_group_name not in self.dict_initiator_groups:
            self.raise_error('initiator group does not exist')

        initiator_group_id = self.dict_initiator_groups[initiator_group_name]['id']

        # DELETE
        request_json = self.query(request_type = 'delete', request_endpoint = 'initiator_groups/' + initiator_group_id)
        # UPDATE DATA
        self.initiator_group_read()
        return

    #################################################################
    ###
    ### INITIATOR
    ###

    def initiator_read(self):
        request_json = self.query(request_type = 'read', request_endpoint = 'initiators/detail')
        for item in request_json['data']:
            if not item['alias']:
                self.dict_initiators[item['id']] = item
            else:
                self.dict_initiators[item['alias']] = item

    def initiator_create(self,initiator_group_name,alias,wwpn):
        initiator_group_name = self.check_string(initiator_group_name)
        alias = self.check_string(alias)
        wwpn = self.check_string(wwpn)

        # UPDATE DATA
        self.initiator_read()
        self.initiator_group_read()

        # GET INITIATOR_GROUP_ID
        if initiator_group_name not in self.dict_initiator_groups:
            self.raise_error('initiator group does not exist')

        initiator_group_id = self.dict_initiator_groups[initiator_group_name]['id']

        # CREATE
        request_data = {'data':{'initiator_group_id':initiator_group_id,'access_protocol':'fc','wwpn':wwpn,'alias':alias}}
        request_json = self.query(request_type = 'create', request_endpoint = 'initiators', request_data = request_data)

        # UPDATE DATA
        self.initiator_read()

        # RETURN THE ID
        return request_json['data']['id']

    
    def initiator_delete(self,initiator_group_name,alias):
        initiator_group_name = self.check_string(initiator_group_name)
        alias = self.check_string(alias)

        # UPDATE DATA
        self.initiator_read()
        self.initiator_group_read()

        if initiator_group_name not in self.initiator_groups:
            self.raise_error('initiator group does not exist')

        if alias not in self.initiators:
            self.raise_error('alias does not exist')

        initiator_id = self.initiators[alias]['id']

        # DELETE
        request_json = self.query(request_type = 'delete', request_endpoint = 'initiators/' + initiator_id)

        # UPDATE DATA
        self.initiator_read()
        self.initiator_group_read()

    
    #################################################################
    ###
    ### PERFORMANCE POLICIES
    ### 

    def performance_policies_read(self):
        request_json = self.query(request_type = 'read', request_endpoint = 'performance_policies/detail')
        for item in request_json['data']:
            self.dict_performance_policies[item['full_name']] = item

    def performance_policies_create(self, name, description, block_size, compress, cache, cache_policy, space_policy):
        name = self.check_string(name) # give it a name (we will append on to this?)
        description = self.check_string_description(description) # give it a description (we will append on to this?)
        block_size = self.check_int(block_size) # Example: '4096' == 4KB
        compress = self.check_bool(compress) # True or False
        cache = self.check_bool(cache) # True or False
        cache_policy = self.check_string(cache_policy) # Possible values: 'normal', 'aggressive'.
        space_policy = self.check_string(space_policy) # Possible values: 'offline', 'non_writable'.

        # UPDATE DATA
        self.performance_policies_read()

        # CHECK TO MAKE SURE NAME IS NOT USED
        if name in self.dict_performance_policies:
            self.raise_error('the name of your performance policy is already in use')

        # IF WE MADE IT HERE, CREATE
        request_data = { 'data' : { 'space_policy' : space_policy, 'block_size' : block_size, 'compress' : compress, 'cache_policy' : cache_policy, 'name' : name, 'description' : description, 'cache' : cache}}

        request_json = self.query(request_type = 'create', request_endpoint = 'performance_policies', request_data = request_data)

        # UPDATE DATA
        self.performance_policies_read()

        # RETURN THE ID
        return request_json['data']['id']

    def performance_policies_delete(self,name):
        name = self.check_string(name)

        # UPDATE DATA
        self.performance_policies_read()

        # MAKE SURE IT EXISTS
        if name not in self.dict_performance_policies:
            self.raise_error('that performance policy does not exist')

        # GRAB ID
        performance_policy_id = self.dict_performance_policies[name]['id']

        # MAKE SURE POLICY IS NOT APPLIED TO ANY VOLUMES
        for item in self.dict_volumes:
            if performance_policy_id == self.dict_volumes[item]['perfpolicy_id']:
                self.raise_error('this performance policy is associated with at least one volume' + item)

        # IF WE MADE IT HERE, WE CAN DELETE
        request_json = self.query(request_type = 'delete', request_endpoint = 'performance_policies/' + performance_policy_id)

        # UPDATE DATA
        self.performance_policies_read()


    #################################################################
    ###
    ### POOLS
    ### 

    def pools_read(self):
        request_json = self.query(request_type = 'read', request_endpoint = 'pools/detail')
        self.dict_pools = request_json

    #################################################################
    ###
    ### PROTECTION SCHEDULES
    ### 

    def protection_schedules_read(self):
        request_json = self.query(request_type = 'read', request_endpoint = 'protection_schedules/detail')
        for item in request_json['data']:
            self.dict_protection_schedules[item['id']] = item

    def protection_schedules_create(self, name, description, volcoll_or_prottmpl_id, period, period_unit, num_retain, downstream_partner, num_retain_replica):
        
        # variables we are enforcing
        volcoll_or_prottmpl_type = 'volume_collection'
        repl_alert_thres = 21600
        replicate_every = 1
        name = self.check_string(name) # give it a name
        description = self.check_string_description(description) # give it a description
        volcoll_or_prottmpl_id = self.check_string(volcoll_or_prottmpl_id) # id of the volume collection
        period = self.check_int(period) # how much time between snapshots
        period_unit = self.check_string(period_unit) # minutes / hours / days / etc
        num_retain = self.check_int(num_retain) # how many snapshots to retain
        downstream_partner = self.check_string(downstream_partner) # pick your replication target
        num_retain_replica = self.check_int(num_retain_replica) # how many snapshots are we keeping at replication target

        # UPDATE DATA
        self.protection_schedules_read()

        # IF WE MADE IT HERE, CREATE
        request_data = { 'data' : { 'replicate_every' : replicate_every, 'volcoll_or_prottmpl_type' : volcoll_or_prottmpl_type, 'volcoll_or_prottmpl_id' : volcoll_or_prottmpl_id, 'name' : name, 'description' : description, 'period' : period, 'period_unit' : period_unit, 'num_retain' : num_retain, 'downstream_partner' : downstream_partner, 'num_retain_replica' : num_retain_replica, 'repl_alert_thres' : repl_alert_thres }}
        request_json = self.query(request_type = 'create', request_endpoint = 'protection_schedules',request_data = request_data)

        # UPDATE DATA
        self.protection_schedules_read()

    def protection_schedules_delete(self, protection_schedule_id):
        # MAKE SURE IT EXISTS

        # UPDATE DATA
        self.protection_schedules_read()

        if protection_schedule_id not in self.dict_protection_schedules:
            self.raise_error('that protection schedule does not exist')

        # IF WE MADE IT HERE, WE CAN DELETE?
        request_json = self.query(request_type = 'delete', request_endpoint = 'protection_schedules/' + protection_schedule_id)

        # UPDATE DATA
        self.protection_schedules_read()


    #################################################################
    ###
    ### PROTECTION TEMPLATES
    ### 

    def protection_templates_read(self):
        request_json = self.query(request_type = 'read', request_endpoint = 'protection_templates/detail')
        for item in request_json['data']:
            self.dict_protection_templates[item['name']] = item

    
    def protection_templates_create(self, name, description):
        name = self.check_string(name) # give it a name (we will append on to this?)
        description = self.check_string(description) # give it a description (we will append on to this?)

        # UPDATE DATA
        self.protection_templates_read()

        # CHECK TO MAKE SURE NAME IS NOT USED
        if name in self.dict_protection_templates:
            self.raise_error('the name of your protection template is already in use')

        # IF WE MADE IT HERE, CREATE
        request_data = { 'data' : { 'name' : name, 'description' : description }}
        request_json = self.query(request_type = 'create', request_endpoint = 'protection_templates',request_data = request_data)

        # UPDATE DATA
        self.protection_templates_read()

        # RETURN THE ID
        return request_json['data']['id']

    def protection_templates_delete(self, name):
        name = self.check_string(name)

        # UPDATE DATA
        self.protection_templates_read()

        # CHECK TO MAKE SURE NAME EXISTS
        if name not in self.dict_protection_templates:
            self.raise_error('that protection template does not exist')

        # IF WE MADE IT HERE, DELETE
        request_json = self.query(request_type = 'delete', request_endpoint = 'protection_templates/' + protection_template_id)

        # UPDATE DATA
        self.protection_templates_read()
    

    #################################################################
    ###
    ### REPLICATION PARTNERS
    ### 

    def replication_partners_read(self):
        request_json = self.query(request_type = 'read',request_endpoint = 'replication_partners/detail')
        self.dict_replication_partners = request_json['data']

    #################################################################
    ###
    ### SNAPSHOT COLLECTIONS
    ### 

    def snapshot_collections_read(self):
        request_json = self.query(request_type = 'read', request_endpoint = 'snapshot_collections/detail')

        build_dict = {}

        for item in request_json['data']:
            # OUR KEYS
            volume_name = item['volcoll_name']
            snapshot_collection_id = item['id']
            snapshot_collection_name = item['name']

            # WE WANT TO ADD A HUMAN READABLE DATETIME TO THE DICTIONARY
            item['human_datetime'] = self.epoch_to_datetime(item['creation_time'])

            # MAKE SURE WE HAVE THE VOLUME AS A KEY
            if volume_name not in build_dict:
                build_dict[volume_name] = {}

            # ADD OUR INFO
            build_dict[volume_name][snapshot_collection_name] = item

        self.dict_snapshot_collections = build_dict

    def snapshot_collections_create(self, volume_collection_name, replicate, name, description):
        volume_collection_name = self.check_string(volume_collection_name)
        name = self.check_string(name)
        description = self.check_string_description(description)
        replicate = self.check_bool(replicate)

        # UPDATE DATA
        self.volume_collections_read()
        self.snapshot_collections_read()

        if volume_collection_name not in self.dict_volume_collections:
            self.raise_error('volume collection does not exist')

        # GET THE VOLCOLL_ID
        volume_collection_id = self.dict_volume_collections[volume_collection_name]['id']

        # IF WE MADE IT HERE, CREATE
        request_data = { 'data' : { 'volcoll_id' : volume_collection_id, 'name' : name, 'description' : description, 'replicate' : replicate }}
        request_json = self.query(request_type = 'create', request_endpoint = 'snapshot_collections',request_data = request_data)

        # UPDATE DATA
        self.volume_collections_read()
        self.snapshot_collections_read()

        # RETURN THE ID
        return request_json['data']['id']

    def snapshot_collections_delete(self, volume_collection_name, snapshot_collection_name):
        volume_collection_name = self.check_string(volume_collection_name)
        snapshot_collection_name = self.check_string(snapshot_collection_name)

        # UPDATE DATA
        self.volume_collections_read()
        self.snapshot_collections_read()

        # MAKE SURE THE VOLUME COLLECTION EXISTS
        if volume_collection_name not in self.dict_volume_collections:
            self.raise_error('volume collection does not exist')

        # GET THE VOLCOLL_ID
        volume_collection_id = self.dict_volume_collections[volume_collection_name]['id']
        snapshot_collection_id = None
        for item in self.dict_snapshot_collections[volume_collection_name]:
            if snapshot_collection_name in self.dict_snapshot_collections[volume_collection_name][item]['name']:
                snapshot_collection_id = self.dict_snapshot_collections[volume_collection_name][item]['id']

        if snapshot_collection_id == None:
            self.raise_error('snapshot_collection does not exist for volume collection')

        # IF WE MADE IT HERE, WE CAN DELETE
        request_json = self.query(request_type = 'delete', request_endpoint = 'snapshot_collections/' + snapshot_collection_id)

        # UPDATE DATA
        self.volume_collections_read()
        self.snapshot_collections_read()

    #################################################################
    ###
    ### SNAPSHOTS
    ### 

    def snapshots_read(self, volume_name = None):
        # YOU HAVE TO LOOK THROUGH EVERY SINGLE VOLUME TO GET SNAPSHOT INFORMATION
        # THEY DO NOT HAVE A DETAIL ENDPOINT (YET).
        # REQUESTED RFE

        # UPDATE DATA
        self.volume_read()

        # FOR SPEED THIS MAY NEED TO BE REDUCED TO REGULAR INSTEAD OF DETAIL INFO
        if volume_name == None:
            for item in self.dict_volumes:
                volume_id = self.dict_volumes[item]['id']
                request_json = self.query(request_type = 'read', request_endpoint = 'snapshots/detail?vol_id=' + volume_id)
                self.dict_snapshots[item] = request_json['data']
        else:
            volume_name = self.check_string(volume_name)
            if volume_name not in self.dict_volumes:
                self.raise_error('volume does not exist')

            volume_id = self.dict_volumes[volume_name]['id']
            request_json = self.query(request_type = 'read', request_endpoint = 'snapshots/detail?vol_id=' + volume_id)
            self.dict_snapshots[volume_name] = request_json['data']

    def snapshots_create(self, volume_name, snapshot_name):
        volume_name = self.check_string(volume_name)
        snapshot_name = self.check_string(snapshot_name)

        # UPDATE DATA
        self.volume_read()
        self.snapshots_read(volume_name)

        if volume_name not in self.dict_volumes:
            self.raise_error('volume does not exist')

        volume_id = self.dict_volumes[volume_name]['id']

        snap_id = 0
        for item in self.dict_snapshots[volume_name]:
            if snapshot_name == item['name']:
                snap_id = item['id']

        if snap_id != 0:
            self.raise_error('snapshot with that name already exists')

        # IF WE MADE IT HERE, CREATE
        request_data = { 'data' : { 'name' : snapshot_name, 'vol_id' : volume_id } }
        request_json = self.query(request_type = 'create', request_endpoint = 'snapshots',request_data = request_data)

        # UPDATE DATA
        self.volume_read()
        self.snapshots_read(volume_name)

        # RETURN THE ID
        return request_json['data']['id']

    def snapshots_delete(self, volume_name, snapshot_name):
        volume_name = self.check_string(volume_name)
        snapshot_name = self.check_string(snapshot_name)

        # UPDATE DATA
        self.volume_read()
        self.snapshots_read(volume_name)

        # IF THE VOLUME EXISTS
        if volume_name not in self.dict_volumes:
            self.raise_error('volume does not exist')

        volume_id = self.dict_volumes[volume_name]['id']

        snap_id = 0

        for item in self.dict_snapshots[volume_name]:
            if snapshot_name == item['name']:
                snap_id = item['id']

        if snap_id == 0:
            self.raise_error('unable to find that snapshot')

        # IF WE MADE IT HERE, WE CAN DELETE
        request_json = self.query(request_type = 'delete', request_endpoint = 'snapshots/' + snap_id)

        # UPDATE DATA
        self.volume_read()
        self.snapshots_read(volume_name)

    def snapshots_lookup_by_id(self, snapshot_id):
        request_json = self.query(request_type = 'read', request_endpoint = 'snapshots/detail?id=' + snapshot_id, expect_error = True)
        if 'data' in request_json:
            return request_json['data']
        else:
            return False

    #################################################################
    ###
    ### VOLUME COLLECTIONS
    ### 

    def volume_collections_read(self):
        request_json = self.query(request_type = 'read', request_endpoint = 'volume_collections/detail')
        for item in request_json['data']:
            self.dict_volume_collections[item['name']] = item

    def volume_collections_create(self, name, description):
        name = self.check_string(name)
        description = self.check_string_description(description)

        # UPDATE DATA
        self.volume_collections_read()

        # CHECK TO MAKE SURE NAME IS NOT USED
        if name in self.dict_volume_collections:
            self.raise_error('the name of your volume collection is already in use')

        # IF WE MADE IT HERE, CREATE
        request_data = { 'data' : { 'name' : name, 'description' : description}}
        request_json = self.query(request_endpoint = 'volume_collections',request_data = request_data,request_type = 'create')

        # UPDATE DATA
        self.volume_collections_read()

        # RETURN THE ID
        return request_json['data']['id']

    def volume_collections_delete(self, name):
        name = self.check_string(name)

        # UPDATE DATA
        self.volume_collections_read()

        # MAKE SURE THAT THE VOLUME COLLECTION EXISTS
        if name not in self.dict_volume_collections:
            self.raise_error('that volume collection does not exist')

        volume_collection_id = self.dict_volume_collections[name]['id']

        # MAKE SURE THAT NO VOLUMES ARE INSIDE THE VOLUME COLLECTION
        for item in self.dict_volumes:
            if volume_collection_id == self.dict_volumes[item]['volcoll_id']:
                self.raise_error('there is at least one volume in this volume collection: ' + item)

        # IF WE MADE IT HERE, WE CAN DELETE
        request_json = self.query(request_endpoint = 'volume_collections/' + volume_collection_id, request_type = 'delete')

        # UPDATE DATA
        self.volume_collections_read()

    def volume_collection_promote(self):
        self.raise_error('sorry, not implemented yet')

    def volume_collection_demote(self):
        self.raise_error('sorry, not implemented yet')

    #################################################################
    ###
    ### VOLUMES
    ### 

    def volume_read(self):
        request_json = self.query(request_type = 'read', request_endpoint = 'volumes/detail')
        for item in request_json['data']:
            self.dict_volumes[item['name']] = item

    def volume_create(self, volume_name, volume_size = 0, performance_policy_name = 'default', volume_clone = False, volume_base_snap_id = None):
        volume_name = self.check_string(volume_name)

        # UPDATE DATA
        self.volume_read()
        self.performance_policies_read()

        # MAKE SURE WE CANNOT FIND THE VOLUME
        if volume_name in self.dict_volumes:
            self.raise_error('this volume already exists')

        if volume_clone == True or volume_base_snap_id != None:
            # WE ARE TRYING TO TAKE A CLONE
            # WE NEED TO CHECK THAT THE VOLUME_BASE_SNAP_ID ACTUALLY EXISTS BEFORE TRYING TO PASS THE CREATE REQUEST
            snapshot_check = self.dict_snapshots_lookup_by_id(volume_base_snap_id)
            if snapshot_check == False:
                self.raise_error('that snapshot does not exist') 
            
            request_data = {'data':{'name':volume_name, 'clone':True, 'base_snap_id':volume_base_snap_id}}

        else:
            # STANDARD VOLUME CREATE    
            volume_size = self.check_int(volume_size)

            # MAKE SURE THE PERFORMANCE POLICY EXISTS
            if performance_policy_name not in self.dict_performance_policies:
                self.raise_error('that performance policy does not exist')

            # GET THE PERFORMANCE POLICY ID
            performance_policy_id = self.dict_performance_policies[performance_policy_name]['id']

            request_data = {'data':{'name':volume_name, 'size':volume_size, 'perfpolicy_id':performance_policy_id}}

        request_json = self.query(request_type = 'create', request_endpoint = 'volumes',request_data = request_data)

        # UPDATE DATA
        self.volume_read()

        # RETURN OUR VOLUME ID
        return request_json['data']['id']

    def volume_delete(self, volume_name):
        volume_name = self.check_string(volume_name)

        # UPDATE DATA
        self.volume_read()

        # MAKE SURE WE CAN FIND THE VOLUME
        if volume_name not in self.dict_volumes:
            self.raise_error('this volume does not exist')

        volume_id = self.dict_volumes[volume_name]['id']

        # MAKE SURE THAT THE VOLUME IS OFFLINE
        if self.dict_volumes[volume_name]['online'] == True:
            self.raise_error('the volume is still online, cannot delete')

        # IF WE MADE IT HERE, WE CAN DELETE
        request_json = self.query(request_endpoint = 'volumes/' + volume_id, request_type = 'delete')
        
        # UPDATE DATA
        self.volume_read()
    
    def volume_update(self, volume_name, **kwargs):
        volume_name = self.check_string(volume_name)

        # UPDATE DATA
        self.volume_read()

        # MAKE SURE WE CAN FIND THE VOLUME
        if volume_name not in self.dict_volumes:
            self.raise_error('this volume does not exist')
        volume_id = self.dict_volumes[volume_name]['id']

        # BUILDING OUR VOLUME UPDATE
        build_json = {}
        build_json['data'] = {}

        # THIS IS MESSY (OR MAYBE LAZY), BUT I REALLY ONLY CARE ABOUT A FEW VOLUME SETTINGS, BUT ADD AS NEEDED
        possible_keys = 'description', 'perfpolicy_id', 'online', 'volcoll_id'

        for key, value in kwargs.items():
            if key == 'description' or key == 'perfpolicy_id' or key == 'volcoll_id':
                tmp_value = self.check_string(value)
            elif key == 'online':
                tmp_value = self.check_bool(value)
            else:
                self.raise_error('unknown vairable ' + str(key) + ' possible keys: ' + str(possible_keys))

            build_json['data'][key] = tmp_value
        
        # IF WE MADE IT HERE, UPDATE
        request_json = self.query(request_type = 'update', request_endpoint = 'volumes/' + volume_id, request_data = build_json)

        # UPDATE DATA
        self.volume_read()

    def volume_snapshot_restore(self, volume_name, snapshot_name):
        self.raise_error('sorry, not implemented yet')