import sys

import zabbix_host
import argparse

def main():
    parser = argparse.ArgumentParser(description="Usage: python main.py <zabbix server ip> <zabbix server port> <auth token>")

    parser.add_argument("-ip", type=str, required=True, help="zabbix server ip")
    parser.add_argument("-port", type=str, required=True, help="zabbix server port")
    parser.add_argument("-auth", type=str,required=True, help="your admin auth token")
    args = parser.parse_args()


    zabbix_host_class = zabbix_host.ZabbixHost(args.ip,args.port,args.auth)
    zabbix_host_class.get_hosts()
    zabbix_host_class.get_templates()
    zabbix_host_class.get_items()
    zabbix_host_class.write()


if __name__ == "__main__":
    main()
