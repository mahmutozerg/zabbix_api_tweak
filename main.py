import sys
import time
import argparse
import grafana_host
import utils
import zabbix_host


def main():
    parser = argparse.ArgumentParser(description="Zabbix to Grafana Dashboard Generator")

    # Zabbix Arguments
    parser.add_argument("-zip", type=str, required=True, help="Zabbix server IP (e.g. http://192.168.0.43)")
    parser.add_argument("-zport", type=str, required=True, help="Zabbix server port")
    parser.add_argument("-zauth", type=str, required=True, help="Zabbix auth token")

    # Grafana Arguments
    parser.add_argument("-gip", type=str, required=True, help="Grafana server IP")
    parser.add_argument("-gport", type=str, required=True, help="Grafana server port")
    parser.add_argument("-gauth", type=str, required=True, help="Grafana auth token")

    # NEW ARGUMENT: Last Value Filter
    # Eğer bu flag verilirse (True), lastvalue'su olmayan itemlar elenir.
    parser.add_argument("-lval", action="store_true",
                        help="Only fetch items that have a lastvalue (Ignore empty items)")

    args = parser.parse_args()

    # --- ZABBIX STAGE ---
    ztime = time.time()
    print(f"[*] Connecting to Zabbix at {args.zip}:{args.zport}...")

    a = zabbix_host.ZabbixHost(args.zip, args.zport, args.zauth)

    # Argümanı buraya gönderiyoruz
    a.start_gathering_host_keys(filter_empty_lastvalue=args.lval)

    print(f"[+] Zabbix data collected in {time.time() - ztime:.2f} seconds.")

    # --- GRAFANA STAGE ---
    gtime = time.time()
    print(f"[*] Connecting to Grafana at {args.gip}:{args.gport}...")

    b = grafana_host.GrafanaHost(args.gip, args.gport, args.gauth)
    b.start()

    print(f"[+] Grafana panels created in {time.time() - gtime:.2f} seconds.")


if __name__ == "__main__":
    main()