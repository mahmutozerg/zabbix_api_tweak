import requests
import json
from utils import GrafanaPanelUtil
from utils.ResponseFileErrorsUtils import read_from_zabbix_json_data


class GrafanaHost:

    def __init__(self, ip, port, auth):
        self.panel_util = GrafanaPanelUtil.PanelGenerator()
        # URL birlestirmeyi daha temiz hale getirdim
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

        # start() fonksiyonunu buradan kaldirdim. Sinifi orneklendirdikten sonra (instance)
        # manuel olarak .start() cagirmalisiniz. Bu daha guvenlidir.

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
            "folderUid": parent_uuid,  # Assign to specific folder
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
            # folderUid kontrolü hata verebilir cunku search sonuclarinda bazen folderUid donmez
            # Bu yuzden .get() kullandim
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
            # Template ID kontrolü: Dict'ten guvenli okuma
            t_id = _template.get('templateid', '')
            t_name = _template.get('name', '')
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

    def __group_items(self, host):
        """
            So this is very weird function,
            simply I am grouping the item's by their type,
            I will use this information to dynamically set the width of the panels,
            this is needed because grafana has negative gravity

        :param host:
        :return:
        """
        group1_list = list()
        group2_list = list()
        group3_list = list()
        grouped = list()

        # Host items kontrolu
        items = host.get('items', [])

        for item in items:
            if item.get("templateid") == "0":
                continue

            # Guvenli erisim ve kucuk harf donusumu
            unit = (item.get("units") or "").lower()
            val_type = item.get("value_type")

            if val_type in ["text", "character"] and unit != "b":
                group1_list.append(item)
            elif unit == "b":
                group2_list.append(item)
            else:
                group3_list.append(item)

        # Lambda key hatasi vermemesi icin int/str donusumu gerekebilir ama simdilik biraktim
        if group1_list:
            grouped.append(sorted([i for i in group1_list if i.get("templateid") != "0"],
                                  key=lambda x: x.get("templateid", "")))
        if group2_list:
            grouped.append(sorted([i for i in group2_list if i.get("templateid") != "0"],
                                  key=lambda x: x.get("templateid", "")))
        if group3_list:
            grouped.append(sorted([i for i in group3_list if i.get("templateid") != "0"],
                                  key=lambda x: x.get("templateid", "")))
        return grouped

    def __add_panels_to_dashboard(self, host_folder, host_db_list, host):
        """
        Düzeltilmiş Mantık:
        1. Item'ları TemplateID'lerine göre grupla.
        2. Her Template (Dashboard) için Generator'ı SIFIRLA (Reset).
        3. Item'ları görsel sıra için (Text -> Num -> Gauge) sırala.
        4. Panelleri oluştur.
        """

        # 1. Dashboard Haritası Oluştur (Hızlı erişim için)
        # Dashboard title formatın: "{hostid}_{templatename}_{templateid}"
        db_map = {}
        for db in host_db_list:
            try:
                tid = db["title"].split("_")[-1]  # Son parça template ID
                db_map[tid] = db
            except:
                continue

        # 2. Itemları Template ID'lerine göre ayır
        items_by_template = {}
        all_items = host.get('items', [])

        for item in all_items:
            tid = item.get("templateid")
            # Template ID'si olmayan veya 0 olanları (eğer manuel dashboard yoksa) atla
            # Not: Eğer manuel itemlar için sanal dashboard yaptıysak onun ID'si gelir, sorun olmaz.
            if not tid or tid == "0":
                continue

            if tid not in items_by_template:
                items_by_template[tid] = []
            items_by_template[tid].append(item)

        # 3. Her Dashboard için ayrı işlem yap
        for tid, items in items_by_template.items():

            target_db = db_map.get(tid)
            if not target_db:
                print(f"Warning: Dashboard for template {tid} not found.")
                continue

            # --- KRİTİK NOKTA: HER DASHBOARD İÇİN GENERATOR SIFIRLANMALI ---
            # Böylece her dashboard en üstten (0,0) başlar ve separator mantığı karışmaz.
            self.panel_util.reset()

            if "panels" not in target_db:
                target_db["panels"] = []

            # Versiyon güncelleme
            if "version" not in target_db:
                target_db["version"] = 0
            else:
                target_db["version"] += 1

            # --- SIRALAMA (GÖRSEL DÜZEN İÇİN) ---
            # Itemları Text -> Numeric -> Gauge sırasına sokuyoruz ki
            # Separator'lar düzgün çıksın.
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

            # 4. Panelleri oluştur ve ekle
            for item in sorted_items:
                panels_list = self.panel_util.create_panel(
                    self.grafana_version,
                    item,
                    host,
                    self.__zabbix_data_source_info
                )

                if panels_list:
                    target_db["panels"].extend(panels_list)

        # 5. Dashboardları Grafana'ya Push et
        for db in host_db_list:
            # Boş dashboardları göndermek istemezsen buraya if db["panels"] ekleyebilirsin
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
                # print(f"Dashboard updated: {db['title']}")
            except Exception as e:
                print(f"Error updating dashboard {db['title']}: {e}")
    def start(self):
        # Bu fonksiyonun import edildigini varsayiyoruz
        zabbix_host_data = read_from_zabbix_json_data()

        for zhost in zabbix_host_data:
            # zhost["host"] erisimi icin guvenlik kontrolu
            h_data = zhost.get("host", {})
            host_name = h_data.get("name")
            host_id = h_data.get("hostid")

            # parentTemplates bir liste olmali
            templates = list(h_data.get("parentTemplates", []))

            if host_name and host_id:
                host_folder, host_template_db = self.__create_host_folders(host_name, host_id, templates)
                self.__add_panels_to_dashboard(host_folder, host_template_db, zhost)
                self.panel_util.reset()