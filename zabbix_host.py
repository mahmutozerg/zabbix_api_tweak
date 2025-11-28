import json
import os.path
import requests

# utils kütüphanesinin projenizde olduğunu varsayıyorum
# Eğer yoksa 'write_to_file' ve 'raise_if_zabbix_response_error' fonksiyonlarını
# kendi utils dosyanızdan import etmelisiniz.
from utils.ResponseFileErrorsUtils import *


class ZabbixHost:
    def __init__(self, ip, port, auth):
        """
        :param ip: zabbix server ip (http://192.168.0.1)
        :param port: zabbix server port (80, 8080 etc)
        :param auth: zabbix admin authentication token
        """

        self.__json_rpc_paths = ["/zabbix/api_jsonrpc.php", "/api_jsonrpc.php"]
        self.valid_json_rpc_path = ""

        # IP adresi http/https içermiyorsa ekleyelim
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
            0: "Zabbix agent", 2: "Zabbix trapper", 3: "Simple check", 5: "Zabbix internal",
            7: "Zabbix agent (active)", 10: "External check", 11: "Database monitor", 12: "IPMI agent",
            13: "SSH agent", 14: "TELNET agent", 15: "Calculated", 16: "JMX agent", 17: "SNMP trap",
            18: "Dependent item", 19: "HTTP agent", 20: "SNMP agent", 21: "Script", 22: "Browser"
        }
        self.zabbix_value_types = {
            0: "numeric", 1: "character", 2: "log", 3: "numeric", 4: "text", 5: "binary"
        }

        self.rpc_info = dict()
        self.static_mapping_rules = self.__load_mapping_rules()
        self.__test_connection()

    def __load_mapping_rules(self):
        """
        Proje dizinindeki 'zabbix_mapping_rules.json' dosyasını okur.
        Dosya yoksa boş döner
        """
        filename = "zabbix_mapping_rules.json"
        # Script'in çalıştığı dizini bul
        base_path = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(base_path, filename)

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                print(f"Mapping rules loaded from {filename}")
                return json.load(f)
        except FileNotFoundError:
            print(f"WARNING: {filename} not found! Static grouping will not work.")
            return {}
        except json.JSONDecodeError:
            print(f"ERROR: {filename} is not valid JSON!")
            return {}

    def __test_connection(self):
        """Checks for json rpc information"""
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

    def do_request(self, method, params=None):
        """Public wrapper for request"""
        return self.__do_request(method, params)

    def get_hosts(self):
        return self.__do_request(
            method="host.get",
            params={
                "output": ["hostid", "host", "name"],
                "selectParentTemplates": ["templateid", "name"],
            })

    def get_groups(self, host_id):
        """Gets all groups that host belongs to."""
        res = self.__do_request(
            method="hostgroup.get",
            params={
                "output": ["name"],
                "hostids": host_id,
            })
        return "|".join(group["name"] for group in res)

    def __get_items_with_missing_tids(self, hostids):
        """Fetches items from Zabbix with tags and flags."""
        items_with_missing_tids = self.__do_request(
            method="item.get",
            params={
                "output": ["itemid", "name", "name_resolved", "key_", "units", "formula", "value_type", "type",
                           "templateid", "lastvalue", "hostids", "flags"],
                "hostids": hostids,
                "sortfield": "itemid",
                "selectTags": "extend",
            }
        )

        filtered_items = []
        for item in items_with_missing_tids:
            keep_item = True

            # Remove raw items
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

                filtered_items.append(item)

        return filtered_items

    def __classify_local_items(self, items, parent_templates):
        """
                Template ID'si '0' olan (Local/LLD) itemları analiz eder.
                Item'ın **son etiketini** (Last Tag Wins) baz alarak;
                1. Önce 'zabbix_mapping_rules.json' içindeki statik kurallarla,
                2. Sonra dinamik isim benzerliğiyle (örn: tag='postgres' -> template='PostgreSQL...')

                Host üzerindeki **gerçek** bir şablonla eşleştirmeye çalışır (Smart Merge).
                Eşleşme sağlanamazsa, verinin dağılmaması için 'Local: Tag (Value)' formatında
                sanal bir şablon oluşturup item'ı oraya atar.

                son tag key'inin karsiligi mapping rules dosyamızda var mı diye bakıyoruz


        """

        virtual_templates_map = {}

        for item in items:
            if item.get("templateid") != "0":
                continue

            tags = item.get("tags", [])
            if not tags:
                self.__assign_virtual_template(item, "local_untagged", "Local: Untagged", virtual_templates_map)
                continue

            last_tag = tags[-1]
            t_key = last_tag['tag'].lower()
            t_val = last_tag['value'].lower()

            matched_real_tid = None

            search_keys = [t_key]
            if t_key == "component" or t_key == "class":
                search_keys.append(t_val)

            for key in search_keys:
                if key in self.static_mapping_rules:
                    keywords = self.static_mapping_rules[key]
                    for keyword in keywords:
                        found_tpl = next((tpl for tpl in parent_templates if keyword.lower() in tpl["name"].lower()),
                                         None)
                        if found_tpl:
                            matched_real_tid = found_tpl["templateid"]
                            break
                if matched_real_tid: break

            if not matched_real_tid:
                ignored_dynamic_values = ["zabbix", "agent", "server", "gen", "sys"]
                if t_val not in ignored_dynamic_values:
                    found_tpl = next((tpl for tpl in parent_templates if t_val in tpl["name"].lower()), None)
                    if found_tpl:
                        matched_real_tid = found_tpl["templateid"]

            if matched_real_tid:
                item["templateid"] = matched_real_tid
            else:
                s_key = "".join(c if c.isalnum() else "_" for c in t_key)
                s_val = "".join(c if c.isalnum() else "_" for c in t_val)
                group_key = f"local_{s_key}_{s_val}"
                group_name = f"Local: {last_tag['tag']} ({last_tag['value']})"

                self.__assign_virtual_template(item, group_key, group_name, virtual_templates_map)

        return items, list(virtual_templates_map.values())

    def __assign_virtual_template(self, item, key, name, v_map):
        item["templateid"] = key
        if key not in v_map:
            v_map[key] = {"templateid": key, "name": name}

    def get_items(self, hostids, tids):
        """
        Zabbix'ten itemları çeker ve eğer bir template'e aitse ID'sini günceller.
        """
        # 1. Ham itemları çek
        items_with_missing_tids = self.__get_items_with_missing_tids(hostids)

        # Hızlı erişim için map oluştur
        host_items_map = {item["key_"]: item for item in items_with_missing_tids}

        # 2. Önce hepsini '0' (Local) olarak işaretle
        for item in items_with_missing_tids:
            item["templateid"] = "0"

        # 3. Gerçek Zabbix Template'lerini eşleştir
        # Zabbix API bize 'bu item bu template'de' demez.
        # Biz template ID ile sorgu atıp 'bu key bende var mı?' diye bakarız.
        for tid in tids:
            items_in_template = self.__do_request(
                method="item.get",
                params={
                    "output": ["key_"],
                    "templateids": tid,
                    "sortfield": "itemid"
                }
            )

            for t_item in items_in_template:
                key = t_item["key_"]
                if key in host_items_map:
                    host_items_map[key]["templateid"] = tid

        return items_with_missing_tids

    def start_gathering_host_keys(self, filter_empty_lastvalue=False):
        """
        Zabbix'ten host, group ve item bilgilerini çeker, işler ve JSON olarak kaydeder.
        """
        hosts = self.get_hosts()

        for host in hosts:
            host_groups = self.get_groups(host["hostid"])

            # Host'un mevcut template listesi
            tids = list(i["templateid"] for i in host["parentTemplates"])

            # Itemları çek ve gerçek template'lerle eşleştir
            items = self.get_items(host["hostid"], tids)

            # --- SINIFLANDIRMA ve BİRLEŞTİRME ---
            # Geriye kalan (templateid="0") itemları akıllıca analiz et.
            # Ya mevcut template'lere yamayacak ya da sanal gruplar oluşturacak.
            items, virtual_templates = self.__classify_local_items(items, host["parentTemplates"])

            # Oluşturulan sanal grupları (varsa) host listesine ekle
            if virtual_templates:
                host["parentTemplates"].extend(virtual_templates)
            # ------------------------------------

            if filter_empty_lastvalue:
                original_count = len(items)
                items = [
                    item for item in items
                    if item.get("lastvalue") is not None and item.get("lastvalue") != ""
                ]
                filtered_count = len(items)
                if original_count != filtered_count:
                    print(f"  -> Filtered {original_count - filtered_count} empty items for host {host['name']}")

            # Custom metrics (Opsiyonel)
            has_custom_metrics = any(i["templateid"] == "custom_metrics" for i in items)
            if has_custom_metrics:
                host["parentTemplates"].append({
                    "templateid": "custom_metrics",
                    "name": "Custom Manual Metrics"
                })

            data = {"host": host, "host_groups": host_groups, "items": items}

            abs_path = os.path.abspath("./hostdatas") + os.sep
            if not os.path.exists(abs_path):
                os.makedirs(abs_path, exist_ok=True)

            write_to_file(data, abs_path + host["name"] + ".json")