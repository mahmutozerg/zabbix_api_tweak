import requests
import json
from utils import GrafanaPanelUtil
from utils.ResponseFileErrorsUtils import read_from_zabbix_json_data


class GrafanaHost:

    def __init__(self, ip, port, auth):
        self.panel_util = GrafanaPanelUtil.PanelGenerator()
        self.__host_addr = f"{ip}:{port}/api"
        self.__item_key_regex = r"^([^.\[]+)(?:\.([^[]+))?(\[(.*)\])?"

        self.grafana_version = ""

        self.__bearer_token = auth
        self.__api_paths = {
            "api_health": "/health",
            "data_sources": "/datasources",
            "dashboards_add": "/dashboards/db",
            "folder": "/folders",
            "folder_search": "/search?query=",
        }

        self.__zabbix_data_source_info = dict()

        self.default_authorized_request_header = {
            "Accept": "application/json",
            'Content-Type': 'application/json',
            "Authorization": f"Bearer {self.__bearer_token}"
        }

        self.__test_connection()
        self.__check_if_zabbix_datasource_exists()

        self.__api_folder = self.__create_api_folder_if_not_exists()

    def __test_connection(self):
        res = requests.get(self.__host_addr + self.__api_paths["api_health"],
                           headers=self.default_authorized_request_header)
        res.raise_for_status()
        self.grafana_version = res.json()["version"]

    def __check_if_zabbix_datasource_exists(self):
        res = requests.get(self.__host_addr + self.__api_paths["data_sources"],
                           headers=self.default_authorized_request_header)
        res.raise_for_status()

        for datasource in res.json():
            if datasource["name"] == "Zabbix" or datasource["type"] == "alexanderzobnin-zabbix-datasource":
                self.__zabbix_data_source_info = {
                    "uid": datasource["uid"],
                    "name": datasource["name"],
                    "type": datasource["type"],
                    "id": datasource["id"]
                }
                return
        else:
            raise Exception(
                f"Zabbix data source doesnt exists\n No datasource name \"{self.__zabbix_data_source_info.get('name', 'Unknown')}\" or datasource type found")

    def __get_folders(self):
        res = requests.get(self.__host_addr + self.__api_paths["folder"],
                           headers=self.default_authorized_request_header)
        res.raise_for_status()
        return res.json()

    def __get_folders_by_search(self, query):
        res = requests.get(self.__host_addr + self.__api_paths["folder_search"] + query,
                           headers=self.default_authorized_request_header)
        res.raise_for_status()
        return res.json()

    def __get_folder_by_uuid(self, uuid):
        res = requests.get(self.__host_addr + self.__api_paths["folder"] + "/" + uuid,
                           headers=self.default_authorized_request_header)
        res.raise_for_status()
        return res.json()

    def __create_folder_if_not_exists(self, data):
        res = requests.post(self.__host_addr + self.__api_paths["folder"],
                            headers=self.default_authorized_request_header,
                            data=json.dumps(data))

        res.raise_for_status()
        content = res.json()
        folder_info = {"id": content["id"], "title": content["title"], "uid": content["uid"]}
        return folder_info

    def __create_dash_board(self, title, parent_uuid):
        dashboard_payload = {
            "dashboard": {
                "id": None,
                "uid": None,
                "title": title,
                "timezone": "browser",
                "schemaVersion": 16,
            },
            "folderUid": parent_uuid,
            "overwrite": False
        }
        res = requests.post(self.__host_addr + self.__api_paths["dashboards_add"],
                            json=dashboard_payload,
                            headers=self.default_authorized_request_header)

        res.raise_for_status()
        res = res.json()
        res["title"] = title
        return res

    def __create_api_folder_if_not_exists(self):
        folders = self.__get_folders_by_search("MOG_API_Zabbix_Grafana")
        for folder in folders:
            if folder["title"] == "MOG_API_Zabbix_Grafana":
                return folder
        else:
            data = {
                "title": "MOG_API_Zabbix_Grafana",
            }
            return self.__create_folder_if_not_exists(data)

    def __create_host_folders(self, host_name, hostid, templates):
        host_name_folder_name = host_name + "_" + hostid
        folders = self.__get_folders_by_search(host_name_folder_name)

        host_name_folder_info = None
        for folder in folders:
            if folder["title"] == host_name_folder_name and folder.get("folderUid") == self.__api_folder["uid"]:
                host_name_folder_info = {"id": folder["id"], "title": folder["title"], "uid": folder["uid"]}
                break
        else:
            host_name_folder_info = self.__create_folder_if_not_exists(
                data={
                    "title": host_name_folder_name,
                    "parentUid": self.__api_folder["uid"]
                }
            )

        template_db_info = list()
        for _template in templates:
            t_id = _template.get('templateid', '')
            t_name = _template.get('name', '')

            # Dashboard başlığı oluşturma standardı
            template_db_name = f"{hostid}_{t_name}_{t_id}"

            template_dbs = self.__get_folders_by_search(f"{template_db_name}&type=dash-db")

            for template_db in template_dbs:
                if template_db_name == template_db["title"]:
                    template_db_info.append(template_db)
                    break
            else:
                dashboard_info = self.__create_dash_board(title=template_db_name,
                                                          parent_uuid=host_name_folder_info["uid"])
                template_db_info.append(dashboard_info)

        return host_name_folder_info, template_db_info

    def __add_panels_to_dashboard(self, host_folder, host_db_list, host):
        """
        GÜNCELLENMİŞ MANTIK:
        1. Dashboard eşleşmesi için 'parentTemplates' içindeki veriyi kullan.
        2. Itemları grupla ve panelleri oluştur.
        """

        # 1. Dashboard Haritası (TemplateID -> DashboardObj)
        db_map = {}
        host_id = host["host"]["hostid"]
        parent_templates = host["host"].get("parentTemplates", [])

        # Grafana'dan gelen mevcut dashboardları title'a göre indexle
        existing_dbs_by_title = {db["title"]: db for db in host_db_list}

        for tpl in parent_templates:
            t_id = tpl.get("templateid")
            t_name = tpl.get("name")

            # create_host_folders'daki isimlendirme formatının aynısı:
            expected_title = f"{host_id}_{t_name}_{t_id}"

            if expected_title in existing_dbs_by_title:
                db_map[t_id] = existing_dbs_by_title[expected_title]

        # 2. Itemları Template ID'lerine göre ayır
        items_by_template = {}
        all_items = host.get('items', [])

        for item in all_items:
            tid = item.get("templateid")
            if not tid or tid == "0":
                continue

            if tid not in items_by_template:
                items_by_template[tid] = []
            items_by_template[tid].append(item)

        # 3. Her Dashboard için panelleri oluştur
        for tid, items in items_by_template.items():

            target_db = db_map.get(tid)
            if not target_db:
                # Eğer start() metodundaki düzeltmeye rağmen bulunamazsa logla
                print(f"Warning: Dashboard for template {tid} not found in map.")
                continue

            # Generator reset (Her dashboard sol üstten başlasın)
            self.panel_util.reset()

            if "panels" not in target_db:
                target_db["panels"] = []

            # Versiyonu artır
            target_db["version"] = target_db.get("version", 0) + 1

            # Görsel sıralama (Text -> Num -> Gauge)
            def sort_key(i):
                u = (i.get("units") or "").lower()
                vt = i.get("value_type")
                is_unixtime = 1 if u == "unixtime" else 0

                if (vt in ["character", "text"] or u == "unixtime") and u != "b":
                    return 0, is_unixtime
                if vt == "binary" or u == "b":
                    return 1, 0
                if vt == "numeric" and u != "b":
                    return 2, 0
                return 3, 0

            sorted_items = sorted(items, key=sort_key)

            for item in sorted_items:
                panels_list = self.panel_util.create_panel(
                    self.grafana_version,
                    item,
                    host,
                    self.__zabbix_data_source_info
                )
                if panels_list:
                    target_db["panels"].extend(panels_list)

        # 4. Dashboardları Grafana'ya Push et
        for db in host_db_list:
            data = {
                "dashboard": db,
                "folderUid": host_folder["uid"],
                "overwrite": True,
                "message": "Auto-generated via API"
            }
            try:
                res = requests.post(self.__host_addr + self.__api_paths["dashboards_add"],
                                    json=data,
                                    headers=self.default_authorized_request_header)
                res.raise_for_status()
            except Exception as e:
                print(f"Error updating dashboard {db['title']}: {e}")

    def start(self):
        zabbix_host_data = read_from_zabbix_json_data()

        for zhost in zabbix_host_data:
            h_data = zhost.get("host", {})
            host_name = h_data.get("name")
            host_id = h_data.get("hostid")
            items = zhost.get("items", [])

            # --- DÜZELTME: Items içinde olup ParentTemplates'te olmayanları ekle ---
            # Bu kısım, LLD ile gelen ve ID'si değişen ama host'un template listesinde
            # adı yazmayan (47116 gibi) itemlar için dashboard oluşturulmasını sağlar.

            item_tids = set()
            for item in items:
                tid = item.get("templateid")
                if tid and tid != "0":
                    item_tids.add(tid)

            parent_templates = h_data.get("parentTemplates", [])
            known_tids = set(t.get("templateid") for t in parent_templates)

            # Bilinmeyen (Linked/Indirect) template ID'leri bul
            missing_tids = item_tids - known_tids

            for mid in missing_tids:
                # İsim veremediğimiz için ID'ye dayalı bir isim uyduruyoruz
                if mid == "custom_metrics":
                    t_name = "Custom Manual Metrics"
                else:
                    t_name = f"Linked_Template_{mid}"

                # Listeye ekliyoruz ki create_host_folders bunu görsün
                parent_templates.append({"templateid": mid, "name": t_name})

            # Bellekteki host verisini güncelle
            h_data["parentTemplates"] = parent_templates
            # -----------------------------------------------------------------------

            if host_name and host_id:
                # Güncel listeyi gönderiyoruz
                host_folder, host_template_db = self.__create_host_folders(host_name, host_id, parent_templates)
                self.__add_panels_to_dashboard(host_folder, host_template_db, zhost)
                self.panel_util.reset()