import json
import os.path
import requests
# utils kutuphanesinin projenizde oldugunu varsayiyorum
from utils.ResponseFileErrorsUtils import *


class ZabbixHost:
    def __init__(self, ip, port, auth):
        """


            :param ip: zabbix server ip  http://192.168.0.1
            :param port: zabbix server port 80, 8080 etc
            :param auth: zabbix admin authentication token
        """

        self.__json_rpc_paths = ["/zabbix/api_jsonrpc.php", "/api_jsonrpc.php"]
        self.valid_json_rpc_path = ""

        # IP adresi http/https icermiyorsa ekleyelim
        base_ip = ip if ip.startswith("http") else f"http://{ip}"
        self.__host_addr = f"{base_ip}:{port}"

        self.__bearer_token = auth
        self.__host_data = list(dict())

        self.default_authorized_request_header = {
            'Content-Type': 'application/json-rpc',
            "Authorization": f"Bearer {self.__bearer_token}"
        }
        self.default_unauthorized_request_header = {'Content-Type': 'application/json-rpc'}

        self.default_request_body = {"jsonrpc": "2.0", "method": "apiinfo.version", "params": {}, "id": 1}

        self.zabbix_item_types = {
            0: "Zabbix agent",
            2: "Zabbix trapper",
            3: "Simple check",
            5: "Zabbix internal",
            7: "Zabbix agent (active)",
            10: "External check",
            11: "Database monitor",
            12: "IPMI agent",
            13: "SSH agent",
            14: "TELNET agent",
            15: "Calculated",
            16: "JMX agent",
            17: "SNMP trap",
            18: "Dependent item",
            19: "HTTP agent",
            20: "SNMP agent",
            21: "Script",
            22: "Browser"
        }
        self.zabbix_value_types = {
            0: "numeric",
            1: "character",
            2: "log",
            3: "numeric",
            4: "text",
            5: "binary"
        }

        self.rpc_info = dict()

        self.__test_connection()

    def __test_connection(self):
        """
        Checks for json rpc information
        :return:
        """
        status_codes = list()
        for path in self.__json_rpc_paths:
            try:
                url = self.__host_addr + path
                res = requests.post(url,
                                    headers=self.default_unauthorized_request_header,
                                    data=json.dumps(self.default_request_body))
                status_codes.append(res.status_code)

                if res.ok:
                    raise_if_zabbix_response_error(res, "apiinfo.version")
                    res_json = json.loads(res.content.decode("utf-8"))
                    self.rpc_info = res_json
                    self.valid_json_rpc_path = path
                    return
            except requests.exceptions.RequestException:
                status_codes.append(0)
                continue
        else:
            assert False, f"{list(zip(self.__json_rpc_paths, status_codes))} Failed to find rpc path, path/statuscode"

    def __do_request(self, method, params=None):
        rpc_ver = self.rpc_info.get("jsonrpc", "2.0")
        rpc_id = self.rpc_info.get("id", 1)

        data = json.dumps({
            "jsonrpc": rpc_ver,
            "method": method,
            "params": params or {},
            "id": rpc_id
        })

        url = self.__host_addr + self.valid_json_rpc_path
        res = requests.post(url, headers=self.default_authorized_request_header, data=data)

        content = raise_if_zabbix_response_error(res, method)
        return content["result"]

    def get_hosts(self):
        return self.__do_request(
            method="host.get",
            params={
                "output": ["hostid", "host", "name"],
                "selectParentTemplates": ["templateid", "name"],
            })

    def get_groups(self, host_id):
        """
        DOCS -> https://www.zabbix.com/documentation/7.0/en/manual/api/reference/hostgroup/get?hl=hostgroup.get

        gets all groups that host's belong to
        output consist of only name of the group
        example :
        "groups": [
            {
                "name": "Zabbix servers"
            },
            {
                "name": "Applications"
            },
            {
                "name": "Linux servers"
            },
            {
                "name": "Databases"
            }
        :return:
        """
        res = self.__do_request(
            method="hostgroup.get",
            params={
                "output": ["name"],
                "hostids": host_id,
            })

        return "|".join(group["name"] for group in res)

    def __get_items_with_missing_tids(self, hostids):
        items_with_missing_tids = self.__do_request(
            method="item.get",
            params={
                "output": ["itemid", "name", "name_resolved", "key_", "units", "formula", "value_type", "type",
                           "templateid", "lastvalue", "hostids"],
                "hostids": hostids,
                "sortfield": "itemid",
                "selectTags": "extend",
            }
        )
        """
            removing the raw data type since it is not processed
        """
        filtered_items_with_missing_tids = []
        for item in items_with_missing_tids:
            keep_item = True

            tags = item.get("tags", [])
            for item_tag in tags:
                if item_tag.get("value") == "raw":
                    keep_item = False
                    break

            if keep_item:
                try:
                    vt = int(item["value_type"])
                    item["value_type"] = self.zabbix_value_types.get(vt, "numeric")
                except (ValueError, KeyError):
                    item["value_type"] = "numeric"

                filtered_items_with_missing_tids.append(item)

        return filtered_items_with_missing_tids

    def get_items(self, hostids, tids):
        """
        DOCS -> https://www.zabbix.com/documentation/7.0/en/manual/api/reference/item/get?hl=item.get

        will look into template ids that are 0 (they are prototypes?)

        What we are doing here is simple...

        when you get  items with hostids you can't control templateid, they don't actually represent the template's id that item is inherited
        when you get items with templateids you can't control hostid's, they don't actually represent the host's id that item is owned by

        so we are combining them, The reason why you can't batch request the tids request is, zabbix api always returns templateid = '0' since you just asked for them
        zabbix assumes that you know that which item comes from which template


        """

        items_with_missing_tids = self.__get_items_with_missing_tids(hostids)

        # Hizli erisim icin map olusturuyoruz
        host_items_map = {item["key_"]: item for item in items_with_missing_tids}

        # --- TID 0 HANDLING ---
        # Zabbix'ten gelen 'templateid' aslinda inherit edilen item'in ID'sidir, template'in degil.
        # Bu yuzden once butun itemlarin templateid'sini '0' (Local/Host Item) olarak set ediyoruz.
        # Eger asagidaki dongude bir template ile eslesirse guncellenecek, eslesmezse '0' olarak kalacak.
        # Bu sayede Grafana tarafinda 'bulunamayan template' hatasini onlemis oluruz.

        for item in items_with_missing_tids:
            item["templateid"] = "0"
        # ----------------------

        for tid in tids:
            # Bu template'e ait item key'lerini cek
            items_in_template = self.__do_request(
                method="item.get",
                params={
                    "output": ["key_"],
                    "templateids": tid,
                    "sortfield": "itemid"
                }
            )

            # Eger host uzerindeki item key'i bu template icinde varsa,
            # item'in templateid'sini guncelliyoruz.
            for t_item in items_in_template:
                key = t_item["key_"]
                if key in host_items_map:
                    host_items_map[key]["templateid"] = tid

        return items_with_missing_tids

    def start_gathering_host_keys(self, filter_empty_lastvalue=False):
        """
        Zabbix'ten host, group ve item bilgilerini çeker ve JSON olarak kaydeder.

        :param filter_empty_lastvalue: True ise, 'lastvalue' alanı boş olan itemları kaydetmez.
        """

        hosts = self.get_hosts()

        for host in hosts:
            host_groups = self.get_groups(host["hostid"])

            # Template ID'lerini al
            tids = list(i["templateid"] for i in host["parentTemplates"])

            # Itemları çek ve eşleştir
            items = self.get_items(host["hostid"], tids)

            # --- YENİ EKLENEN FİLTRELEME MANTIĞI ---
            if filter_empty_lastvalue:
                original_count = len(items)
                # Zabbix'te lastvalue string döner.
                # "0" verisi doludur, "" veya None boştur.
                # Python'da "0" True, "" False döner. Bu yüzden direkt kontrol yeterli.
                items = [
                    item for item in items
                    if item.get("lastvalue") is not None and item.get("lastvalue") != ""
                ]
                filtered_count = len(items)
                if original_count != filtered_count:
                    # Bilgi amaçlı print atabiliriz (Opsiyonel)
                    # print(f"  -> Filtered {original_count - filtered_count} empty items for host {host['name']}")
                    pass
            # ---------------------------------------

            # Custom Metrics kontrolü (Önceki konuşmamızdan kalan logic)
            has_custom_metrics = any(i["templateid"] == "custom_metrics" for i in items)

            if has_custom_metrics:
                host["parentTemplates"].append({
                    "templateid": "custom_metrics",
                    "name": "Custom Manual Metrics"
                })

            data = {"host": host, "host_groups": host_groups, "items": items}
            abs_path = os.path.abspath("./hostdatas") + "\\"

            write_to_file(data, abs_path + host["name"] + ".json")