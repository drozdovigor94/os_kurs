import sys
from netmiko import ConnectHandler
from getpass import getpass
import time
import multiprocessing
import re

start_time = time.time()

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def doRouter(connection_data):

    ip_address = connection_data[0]
    username = connection_data[1]
    password = connection_data[2]

    ip_check = re.findall("^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$", ip_address)
    if ip_check == []:
        print (f'{bcolors.FAIL}Invalid IP - {ip_address}{bcolors.ENDC}')
        return ip_address

    device = {
        'device_type': 'cisco_ios',
        'ip': ip_address.strip(),
        'username': username,
        'password': password,
        'port': 22, }
    try:
        config_ok = True

        net_connect = ConnectHandler(**device)

        cli_response = net_connect.send_command("sh dmvpn | i Interface")
        cli_response = cli_response.replace("Interface: ", "")
        cli_response = cli_response.replace(", IPv4 NHRP Details", "").strip()
        if cli_response != "Tunnel1":
            print (f'{ip_address}{bcolors.WARNING} - WARNING - DMVPN not on Tunnel1. {cli_response} {bcolors.ENDC}')
            config_ok = False

        cli_response2=net_connect.send_command("sh run | i ip route 1.1.1.1 255.255.255.255")
        if cli_response2.strip() == "":
            print (f'{ip_address}{bcolors.WARNING} - WARNING - couldnot find static route to 8.8.8.8 {bcolors.ENDC}')
            config_ok = False

        ip_next_hop = ""
        if cli_response2 != "":
            ip_next_hop = cli_response2.split(" ")[4]

        if ip_next_hop == "":
            print (f'{bcolors.FAIL}WARNING - couldnot find next-hop IP address {ip_address}{bcolors.ENDC}')
            config_ok = False


        if config_ok == True:
            config_commands = ['ip route 1.1.1.1 255.255.255.255 '+ip_next_hop, 'ip route 2.2.2.2 255.255.255.255 '+ip_next_hop]
            net_connect.send_config_set(config_commands)
            print (f'{ip_address} - Static routes added')
        else:
            print (f'{bcolors.FAIL}Invalid IP - {ip_address}{bcolors.ENDC}')
            return ip_address

        if config_ok:
            net_connect.send_command_expect('write memory')
            print (f'{ip_address} - Config saved')
            net_connect.disconnect ()

    except:
        print (f'{ip_address} {bcolors.FAIL} - Cannot connect to this device. {bcolors.ENDC}')
        return ip_address
    print (f'{bcolors.FAIL} {ip_address}  - Router configured sucessfully {bcolors.ENDC}')

if __name__ == '__main__':
    '''
    # Enter valid username and password. Note password is blanked out using the getpass library
    global_username = input("Enter Username: ")
    global_password = getpass()
    ip_file = 'ip.txt'
    '''

    global_username = sys.argv[1]
    global_password = sys.argv[2]
    ip_file = sys.argv[3]

    try:
        f = open(ip_file)
        connection_data=[]
        filelines = f.read().splitlines()
        for line in filelines:
            if line == "": continue
            if line[0] == "#": continue
            conn_data = line.split(',')
            ipaddr=conn_data[0].strip()
            username=global_username
            password=global_password
            if len(conn_data) > 1 and conn_data[1].strip() != "": username = conn_data[1].strip()
            if len(conn_data) > 2 and conn_data[2].strip() != "": password = conn_data[2].strip()
            connection_data.append((ipaddr, username, password))
        f.close()
    except:
        sys.exit("Couldn't open or read file ip.txt")

    multiprocessing.set_start_method("spawn")
    with multiprocessing.Pool(maxtasksperchild=10) as process_pool:
        # doRouter - function, iplist - argument
        routers_with_issues = process_pool.map(doRouter, connection_data, 1)
        process_pool.close()
        process_pool.join()

    print("\n")
    print("#These routers weren't configured#")

    failed_file = open('fail.txt', 'w')
    for item in routers_with_issues:
        if item != None:
          failed_file.write("%s\n" % item)
          print(item)

    #Completing the script and print running time
    print("\n")
    print("#This script has now completed#")
    print("\n")
    print("--- %s seconds ---" % (time.time() - start_time))

