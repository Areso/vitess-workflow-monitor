from time import sleep
from threading import Thread
import subprocess
import json
from flask import Flask

app = Flask(__name__)

shards_states = ""
shards_tps = ""


def get_shard_tablet(shard_obj):
    shard = shard_obj["PrimaryReplicationStatuses"][0]["Shard"]
    vttablet = shard_obj["PrimaryReplicationStatuses"][0]["Tablet"]
    return shard + '/' + vttablet


def get_short_shardname(shard):
    delimiter_pos = shard.find("/")
    shard_short = shard[:delimiter_pos]
    return shard_short


def get_output_from_cli(workflow_to_check, ctl_host):
    command = "vtctlclient --server %vtctlhost:15999 Workflow %arg1 show"
    command = command.replace("%arg1", workflow_to_check)
    command = command.replace("%vtctlhost", ctl_host)
    p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    workflow_show2 = (p.communicate())
    workflow_obj = json.loads(workflow_show2[0])
    shards = list(workflow_obj["ShardStatuses"].keys())
    if len(shards_pos) == 0:
        for every_shard in shards:
            shards_pos[every_shard] = []
        #print(shards_pos)
    fail_bl = False
    global i
    global shards_states
    shards_states = ""
    for every_shard in shards:
        shard_details = workflow_obj["ShardStatuses"][every_shard]
        shard_tablet = get_shard_tablet(shard_details)
        shard_state   = shard_details["PrimaryReplicationStatuses"][0]["State"]
        shard_gtids   = shard_details["PrimaryReplicationStatuses"][0]["Pos"]
        shards_pos[every_shard].append(shard_gtids.split(','))
        if shard_state == "Error":
            fail_bl = True
        shard_message = shard_details["PrimaryReplicationStatuses"][0]["Message"]
        if shard_state == "Error":
            shards_states += shard_tablet + " " + "0" + "\n"
        if shard_state == "Copying":
            shards_states += shard_tablet + " " + "1" + "\n"
        if shard_state == "Running":
            shards_states += shard_tablet + " " + "2" + "\n"
        if fail_bl:
            print(shard_tablet, shard_state, shard_message)
            pass
    return fail_bl


def check_gtids():
    status = []
    global shards_tps
    shards_tps = ""
    for every_shard in list(shards_pos.keys()):
        list_pos = shards_pos[every_shard]
        if (len(list_pos)) >= 11:
            current_state  = list_pos[len(list_pos)-1]
            previous_state = list_pos[len(list_pos)-11]
            the_diff = find_diff(current_state, previous_state)
            the_diff = the_diff
            shard = get_short_shardname(every_shard)
            status.append({shard: the_diff})
            shards_tps += every_shard + " " + str(the_diff) + "\n"
        else:
            shards_tps += every_shard + " " + str(0) + "\n"


def find_diff(actual_list, db_list):
    s = set(db_list)
    temp3 = [x for x in actual_list if x not in s]
    flag1 = False
    flag2 = False
    if len(temp3) != 0:
        gtid_start_pos = str(temp3).rfind('-')
        new_gtid       = str(temp3)[gtid_start_pos+1:-2]
        flag1 = True
    s2 = set(actual_list)
    temp4 = [x for x in db_list if x not in s2]
    if len(temp4) != 0:
        gtid_start_pos = str(temp4).rfind('-')
        old_gtid = str(temp4)[gtid_start_pos+1:-2]
        flag2 = True
    if flag1 and flag2:
        try:
            total_diff = int(round((int(new_gtid)-int(old_gtid))/60, 0))
        except ValueError:
            total_diff = 0
    else:
        total_diff = 0
    return total_diff


def routined_task(workflow_name, host):
    if workflow_name is None:
        command = "vtctlclient --server %host:15999 Workflow user listall"
        command = command.replace("%host", host)
        p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
        workflow_list_cli_return_bytes = p.communicate() # returns tuple, where second value is None
        workflow_list_cli_return = workflow_list_cli_return_bytes[0].decode(encoding='utf8')
        # Following workflow(s) found in keyspace user: move2vitess21
        delimiter = ":"
        list_start_pos     = workflow_list_cli_return.find(":")
        keyspace_start_pos = workflow_list_cli_return.rfind(" ", 0, list_start_pos)
        keyspace = workflow_list_cli_return[keyspace_start_pos+1:list_start_pos]
        workflow_list_str = workflow_list_cli_return[list_start_pos+1:]
        workflow_list_str = workflow_list_str.replace('\n', ' ').replace('\r', '')
        workflow_list_str = workflow_list_str.replace(" ", "")
        workflow_list = workflow_list_str.split(",")
        workflow_name = keyspace+"."+workflow_list[0]
    global i
    while True:
        anyerrors = get_output_from_cli(workflow_name, host)
        if anyerrors:
            pass
        else:
            pass
        sleep(6)  # in seconds
        if i % 10 == 0:
            print("=====")
            check_gtids()
        i += 1


def find_vtctl():
    command_find_ip = "ip a show eth0 | grep inet | awk '{print $2}' | cut -d/ -f1"
    p1 = subprocess.Popen(command_find_ip, stdout=subprocess.PIPE, shell=True)
    myipaddress = p1.communicate()  # returns tuple, where second value is None
    myipaddress = myipaddress[0].decode(encoding='utf8').rstrip()

    command_find_vtctl = "nmap -sP %myipaddress/23 | grep vtctl | awk '{print $6}'"
    command_find_vtctl = command_find_vtctl.replace("%myipaddress", myipaddress)
    p2 = subprocess.Popen(command_find_vtctl, stdout=subprocess.PIPE, shell=True)
    vtctl_host = p2.communicate()  # returns tuple, where second value is None
    vtctl_host = vtctl_host[0].decode(encoding='utf8').rstrip()
    # (10.11.73.59)
    vtctl_host = vtctl_host.replace("(", "").replace(")", "").replace(" ", "")
    return vtctl_host




if __name__ == "__main__":
    # if __name__ == '__main__':
    # workflow_name = args.workflow
    i = 0
    shards_pos = {}
    vtctl_host = find_vtctl()
    workflow_checker_routine = Thread(target=routined_task,
                                      args=[None, vtctl_host])
    workflow_checker_routine.start()
    app.run(host='0.0.0.0', port=5000)


@app.route("/metrics")
def metrics():
    global shards_states
    global shards_tps
    return shards_states+shards_tps

