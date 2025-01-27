import sys

import zabbix_host


def main():
    if len(sys.argv) != 4:
        print("Usage: python sys_args_input.py <zabbix server ip> <zabbix server port> <auth token>")
        return


    zabbix_host_class = zabbix_host.ZabbixHost(sys.argv[1],sys.argv[2],sys.argv[3])
    zabbix_host_class.get_hosts()
    zabbix_host_class.get_templates()
    zabbix_host_class.get_items()
if __name__ == "__main__":
    main()
