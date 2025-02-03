import json
import urllib.parse
from pprint import pp
from tempfile import template

import requests
import utils


class GrafanaHost:

    def __init__(self,ip,port,auth):

        self.__host_addr_list= [ip,port]
        self.__host_addr = str.join(":",self.__host_addr_list)+"/api"
        self.__item_key_regex = r"^([^.\[]+)(?:\.([^[]+))?(\[(.*)\])?"

        self.grafana_version = ""

        self.__bearer_token = auth
        self.__api_paths= {
            "api_health":"/health",
            "data_sources":"/datasources",
            "dashboard_add":"/dashboards/db",
            "folder":"/folders",
            "folder_search":"/search?query="

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



    def __create_host_folders(self,host_name,hostid,template_folder):

        host_name_folder_info = dict()

        folders = self.__get_folders_by_search(host_name+hostid)
        for folder in folders:
            if folder["title"] == host_name+hostid and folder["folderUid"] == self.__api_folder["uid"]:
                host_name_folder_info = {"id":folder["id"],"title":folder["title"],"uid":folder["uid"]}
                break


        else:
            host_name_folder_info = self.__create_folder_if_not_exists(
                data = {
                    "title": host_name+hostid,
                    "parentUid": self.__api_folder["uid"]

                }
            )


        template_folder_info= list(dict())
        for _template in template_folder:
            folders = self.__get_folders_by_search(_template)

            for folder in folders:
                if (_template + hostid) == folder["title"]:
                    template_folder_info.append({"id":folder["id"],"title":folder["title"],"uid":folder["uid"]})
                    break

            else:
                folder_info=self.__create_folder_if_not_exists( data = {
                        "title": _template + hostid,
                        "parentUid": host_name_folder_info["uid"]

                    })
                template_folder_info.append(folder_info)

        return host_name_folder_info,template_folder_info




    def start(self):
        zabbix_host_data = utils.read_from_zabbix_json_data()
        for zhost in [zabbix_host_data[2]]:
            host_name,host_id =zhost["host"]["host"] , zhost["host"]["hostid"]
            template_names = list(i["name"] for i in zhost["host"]["parentTemplates"])

            host_folder,template_folder = self.__create_host_folders(host_name,host_id,template_names)

            print(host_folder,template_folder)







