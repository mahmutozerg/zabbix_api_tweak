import json
import os
from pprint import pp, pprint
import requests
import utils
from granafa_dashboard_jsons import  GrafanaDicts


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
            "dashboard_add":"/dashboards/db"

        }

        self.__zabbix_data_source_info = dict()

        self.default_authorized_request_header= {'Content-Type': 'application/json-rpc',"Authorization":f"Bearer {self.__bearer_token}"}


        self.__test_connection()
        self.__check_if_zabbix_datasource_exists()
        self.json_templates = GrafanaDicts()
        self.__set_datasource_to_json_templates()

        self.__zabbix_host_data = list(dict())
        self.__get_zabbix_hosts()
        self.__create_dashboard()


    def __set_datasource_to_json_templates(self):
        self.json_templates.panel_data_time_series["datasource"]["type"] = self.__zabbix_data_source_info["type"]
        self.json_templates.panel_data_time_series["datasource"]["uid"] = self.__zabbix_data_source_info["uid"]

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


    def __get_zabbix_hosts(self):
        for host in os.listdir("./hostdatas"):
            if host.endswith(".json"):
                 self.__zabbix_host_data.append(utils.read_from_zabbix_json_data("./hostdatas/"+host))

    def __create_dashboard(self):

        for host in [self.__zabbix_host_data[-2]]:
            for item_group in host["items"]:
                template_id,template_name = item_group["template"].split("**")
                items = item_group["items"]
                for item in items:
                    print(f"Grup {host['host_groups']}\t{host['host']['host']}/{template_name}/{item['key_'].split('.')[:2]} TAGS {item['tags']}, Name {item['key_']}")


            break
        return




    def __parse_item_keys(self,item):

        """
        https://www.zabbix.com/documentation/current/en/manual/config/items/item/key#key-parameters

        :return:
        """

        return
