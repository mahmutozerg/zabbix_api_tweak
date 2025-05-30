import sys
import time

import grafana_host
import utils
import zabbix_host
import argparse




def main():
    parser = argparse.ArgumentParser(description="Usage: python main.py -zip http://xxx.xxx.xxx.xxx -zport zabbix server port -zauth zabbix auth token -gip http://xxx.xxx.xxx.xxx  -gport grafana server port -gauth grafana auth token" )

    parser.add_argument("-zip", type=str, required=True, help="zabbix server ip")
    parser.add_argument("-zport", type=str, required=True, help="zabbix server port")
    parser.add_argument("-zauth", type=str,required=True, help="your zabbix auth token")

    parser.add_argument("-gip", type=str, required=True, help="grafana server ip")
    parser.add_argument("-gport", type=str, required=True, help="grafana server port")
    parser.add_argument("-gauth", type=str,required=True, help="your grafana auth token")
    args = parser.parse_args()


    ztime = time.time()
    zabbix_host.ZabbixHost(args.zip,args.zport,args.zauth)
    print("zabbix data toplama işlemi için geçen süre ",time.time()-ztime)

    gtime = time.time()
    grafana_host.GrafanaHost(args.gip,args.gport,args.gauth)
    print("Grafana panelleri oluşturma işlemi için geçen süre ",time.time()-gtime)



if __name__ == "__main__":
    main()
