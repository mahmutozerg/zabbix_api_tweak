
import requests
from utils import GrafanaPanelUtil
from utils.ResponseFileErrorsUtils import *


class GrafanaHost:

    def __init__(self,ip,port,auth):
        self.panel_util = GrafanaPanelUtil.PanelGenerator()
        self.__host_addr_list= [ip,port]
        self.__host_addr = str.join(":",self.__host_addr_list)+"/api"
        self.__item_key_regex = r"^([^.\[]+)(?:\.([^[]+))?(\[(.*)\])?"

        self.grafana_version = ""

        self.__bearer_token = auth
        self.__api_paths= {
            "api_health":"/health",
            "data_sources":"/datasources",
            "dashboards_add":"/dashboards/db",
            "folder":"/folders",
            "folder_search":"/search?query=",

        }

        self.__zabbix_data_source_info = dict()

        self.default_authorized_request_header= {"Accept": "application/json",'Content-Type': 'application/json',"Authorization":f"Bearer {self.__bearer_token}"}


        self.__test_connection()
        self.__check_if_zabbix_datasource_exists()

        self.__api_folder= self.__create_api_folder_if_not_exists()

        self.start()

    def __test_connection(self):

        res =requests.get(self.__host_addr+self.__api_paths["api_health"],headers=self.default_authorized_request_header)
        res.raise_for_status()
        self.grafana_version= res.json()["version"]
    def __check_if_zabbix_datasource_exists(self):

        res = requests.get(self.__host_addr+self.__api_paths["data_sources"],headers=self.default_authorized_request_header)
        res.raise_for_status()

        for datasource in res.json():
            if datasource["name"] == "Zabbix" or datasource["type"] == "alexanderzobnin-zabbix-datasource":
                self.__zabbix_data_source_info = {"uid":datasource["uid"],"name":datasource["name"],"type":datasource["type"],"id":datasource["id"]}

                return
        else:
            raise  Exception(f"Zabbix data source doesnt exists\n No datasource name \"{self.__zabbix_data_source_info['name']}\" or datasource type \"{self.__zabbix_data_source_info['type']}\" found")

    def __get_folders(self):
        res = requests.get(self.__host_addr+self.__api_paths["folder"],headers=self.default_authorized_request_header)
        res.raise_for_status()
        return res.json()

    def __get_folders_by_search(self,query):
        res = requests.get(self.__host_addr+self.__api_paths["folder_search"]+query,headers=self.default_authorized_request_header)
        res.raise_for_status()
        return res.json()



    def __get_folder_by_uuid(self,uuid):
        res = requests.get(self.__host_addr+self.__api_paths["folder"]+"/"+uuid,headers=self.default_authorized_request_header)
        res.raise_for_status()
        return res.json()

    def __create_folder_if_not_exists(self,data):
        res = requests.post(self.__host_addr + self.__api_paths["folder"],
                            headers=self.default_authorized_request_header,
                            data=json.dumps(data))

        res.raise_for_status()

        content = res.json()

        folder_info = {"id": content["id"], "title": content["title"], "uid": content["uid"]}
        return folder_info
    def __create_dash_board(self, title,parent_uuid):

        dashboard_payload = {
            "dashboard": {
                "id": None,
                "uid": None,
                "title":title ,
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

        folders  = self.__get_folders_by_search("MOG_API_Zabbix_Grafana")
        for folder in folders:
            if folder["title"] == "MOG_API_Zabbix_Grafana":
                return folder
        else:
            data = {
                "title": "MOG_API_Zabbix_Grafana",

            }
            return self.__create_folder_if_not_exists(data)



    def __create_host_folders(self,host_name,hostid,templates):

        host_name_folder_name= host_name+"_"+hostid
        folders = self.__get_folders_by_search(host_name_folder_name)
        for folder in folders:
            if folder["title"] == host_name_folder_name and folder["folderUid"] == self.__api_folder["uid"]:
                host_name_folder_info = {"id":folder["id"],"title":folder["title"],"uid":folder["uid"]}
                break

        else:
            host_name_folder_info = self.__create_folder_if_not_exists(
                data = {
                    "title": host_name_folder_name,
                    "parentUid": self.__api_folder["uid"]

                }
            )


        template_db_info= list(dict())
        for _template in templates:
            template_db_name = hostid+"_"+_template["name"]+"_"+_template['templateid']

            template_dbs = self.__get_folders_by_search(f"{template_db_name}&type=dash-db")


            for template_db in template_dbs:
                if template_db_name == template_db["title"]:
                    template_db_info.append(template_db)
                    break

            else:
                dashboard_info=self.__create_dash_board(title=template_db_name,parent_uuid=host_name_folder_info["uid"])
                template_db_info.append(dashboard_info)

        return host_name_folder_info,template_db_info

    def __group_items(self,host):
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

        for item in host['items']:
            if item["templateid"] == "0":
                continue

            if item["value_type"] in ["text", "character"] and item["units"].lower()!="b":
                group1_list.append(item)
            elif item["units"].lower()== "b":
                group2_list.append(item)

            else:
                group3_list.append(item)

        if group1_list:
            grouped.append(sorted([i for i in group1_list if i["templateid"] != "0"],key=lambda x: (x["templateid"])))

        if group2_list:
            grouped.append(sorted([i for i in group2_list if i["templateid"] != "0"],key=lambda x: (x["templateid"])))

        if group3_list:
            grouped.append(sorted([i for i in group3_list if i["templateid"] != "0"],key=lambda x: (x["templateid"])))
        return grouped

    def __add_panels_to_dashboard(self, host_folder, host_db, host):

        target_db =None
        ## checking if the current host's current item has a template id different from "0"
        ##if so we are creating our template folder name

        sorted_item_groups = self.__group_items(host)

        for item_group in sorted_item_groups:
            for item in item_group:
                for i in host_db:
                    if i["slug"] != "" and i["slug"].endswith(item["templateid"]):
                        target_db = list(i for i in host_db if i["slug"].endswith(item["templateid"]))[0]
                    else:
                        target_db = list(i for i in host_db if i["title"].endswith(item["templateid"]))[0]

                if target_db:
                    if "panels" not in target_db:
                        target_db["panels"] = []
                    ## create or update the version number
                    if "version" not in target_db:
                        target_db["version"] = 0
                    else:
                        target_db["version"] += 1

                    panels = self.panel_util.create_panel(self.grafana_version, item, host,self.__zabbix_data_source_info)
                    if panels:
                        target_db["panels"].append(panels)
            
        for db in  host_db:
            data = {
                "dashboard": db,
                "folderUid": host_folder["uid"],
                "overwrite": True,
                "message":"initial"
            }
            res = requests.post(self.__host_addr + self.__api_paths["dashboards_add"],
                                json=data,
                                headers=self.default_authorized_request_header)

            res.raise_for_status()





    def start(self):
        zabbix_host_data = read_from_zabbix_json_data()
        for zhost in zabbix_host_data:
            host_name,host_id =zhost["host"]["name"] , zhost["host"]["hostid"]
            templates = list(i for i in zhost["host"]["parentTemplates"])

            host_folder, host_template_db = self.__create_host_folders(host_name,host_id,templates)

            self.__add_panels_to_dashboard(host_folder,host_template_db,zhost)
            self.panel_util.reset()










