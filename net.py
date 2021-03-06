import json
import requests
import requests_cache
import urllib3

urllib3.disable_warnings()

# use requests_cache for testing
# requests_cache.install_cache(expire_after=600)

site = 'http://my.onapp.server'

r = requests.Session()

r.headers = {
    'Accept': 'application/json',
    'Content-type': 'application/json'
}

# Api credentials
r.auth = 'onapp_api', 'onapp_pass'


def get_stuff(url):
    s = r.get(url, verify=False)
    data = s.json()
    return data


class Networks:

    def __init__(self, **kwargs):
        # construct based on the bits that we need from networks.json
        self.id = kwargs['network']['id']
        self.label = kwargs['network']['label']
        self.identifier = kwargs['network']['identifier']
        self.network_group_id = kwargs['network']['network_group_id']

    def get_hv_id(self):
        # we only want vcenters get Hypervisor ID using target_join_id in network_joins.json this will be used to remove add/join
        hypervisors = get_stuff(f'{site}/settings/hypervisors.json')
        hvs = []
        for each in hypervisors:
            if each['hypervisor']['hypervisor_type'] == 'vcenter':
                hvs.append(each['hypervisor']['id'])
        for each in hvs:
            data = get_stuff(
                f'{site}/settings/hypervisors/{each}/network_joins.json')
            for each in data:
                if self.id == each['network_join']['network_id']:
                    return each['network_join']['target_join_id']

    def get_join_id(self):
        # same as above but this time we are pulling in the join id, this will be used later to remove/add the join
        hypervisors = get_stuff(f'{site}/settings/hypervisors.json')
        hvs = []
        for each in hypervisors:
            if each['hypervisor']['hypervisor_type'] == 'vcenter':
                hvs.append(each['hypervisor']['id'])

        for each in hvs:
            data = get_stuff(
                f'{site}/settings/hypervisors/{each}/network_joins.json')
            for each in data:
                if self.id == each['network_join']['network_id']:
                    return each['network_join']['id']


# Select the Network Zone that we want to split so we only get that network zone data
select_network_zone = get_stuff(f'{site}/settings/network_zones.json')
for each in select_network_zone:
    if each['network_group']['server_type'] == "virtual":
        print(
            f"Network Zone : {each['network_group']['label']} -- DataCenter ID : {each['network_group']['datacenter_id']} -- ID : {each['network_group']['id']}")


# Confirm Network Zone
nz_id = input('Please enter the Network Zone ID:\n')
nz_id = int(nz_id)

# Store Datacenter ID somewhere to use in zone creation
datacenter = get_stuff(f'{site}/settings/network_zones/{nz_id}.json')
dc_id = datacenter['network_group']['datacenter_id']
print(dc_id)


# Initialize empty dics to store relevant information so we dont keep on going back and forth re-reading
working_dicts = []
my_stuff = get_stuff(f'{site}/settings/networks.json')

# TEll me for only the network zone that I want
for each in my_stuff:
    data = Networks(**each)
    if data.network_group_id == nz_id and data.get_join_id() != None:
        print(f' Network ID : {data.id} and Network_Zone_id : {data.network_group_id} and Label : {data.label} and Network_Join ID : {data.get_join_id()} and Hypervisor ID : {data.get_hv_id()} and Datacenter ID : {dc_id}')
        working_dicts.append({'label': data.label, 'network_id': data.id, 'join_id': data.get_join_id(
        ), 'network_zone_id': data.network_group_id, 'hv_id': data.get_hv_id(), 'dc_id': dc_id})


print(working_dicts)

for each in working_dicts:
    remove_from_hv = r.delete(
        f"{site}/settings/hypervisors/{each['hv_id']}/network_joins/{each['join_id']}.json")
    if remove_from_hv.status_code == 204:
        remove_from_zone = r.post(
            f"{site}/settings/network_zones/{each['network_zone_id']}/networks/{each['network_id']}/detach.json")
        if remove_from_zone.status_code == 200:
            create_network_zone = r.post(
                f'{site}/settings/network_zones.json', json={"network_group": {"label": each['label'], "datacenter_id": each['dc_id']}})
            new_network_zone_id = create_network_zone.json()[
                'network_group']['id']
            if create_network_zone.status_code == 201:
                attach_to_new_zone = r.post(
                    f"{site}/settings/network_zones/{new_network_zone_id}/networks/{each['network_id']}/attach.json")
                if attach_to_new_zone.status_code == 200:
                    attach_to_hv = r.post(f"{site}/settings/hypervisors/{each['hv_id']}/network_joins.json", json={
                                          "network_join": {"network_id": each['network_id'], "interface": "vlan"}})
                    if attach_to_hv.status_code == 201:
                        print(
                            f"finished attaching network {each['network_id']}")
                    else:
                        print(f'FAILED Please check')
                else:
                    print(
                        f"unable to attach Network {each['network_id']} to zone {new_network_zone_id}")
            else:
                print('Unable to create new network zone')
        else:
            print(
                f"unable to detach {each['network_id']} from {each['network_zone_id']} ")

    else:
        print(
            f"unable to remove Network join {each['join_id']}from HV {each['hv_id']} ")
