from audioop import reverse
from pprint import pp

import requests
import utils
from collections import defaultdict

class GrafanaHost:

    def __init__(self,ip,port,auth):

        self.__host_addr_list= [ip,port]
        self.__host_addr = str.join(":",self.__host_addr_list)+"/api"
        self.__item_key_regex = r"^([^.\[]+)(?:\.([^[]+))?(\[(.*)\])?"


        self.__bearer_token = auth
        self.__api_paths= {
            "api_health":"/health",
            "data_sources":"/datasources",

        }

        self.__zabbix_data_source_info = dict()
        self.default_authorized_request_header= {'Content-Type': 'application/json-rpc',"Authorization":f"Bearer {self.__bearer_token}"}


        self.__test_connection()
        self.__check_if_zabbix_datasource_exists()
        self.__zabbix_data = utils.read_from_zabbix_json_data()
        self.__create_dashboard()

    def __test_connection(self):

        res =requests.get(self.__host_addr+self.__api_paths["api_health"],headers=self.default_authorized_request_header)
        res.raise_for_status()

    def __check_if_zabbix_datasource_exists(self):

        res = requests.get(self.__host_addr+self.__api_paths["data_sources"],headers=self.default_authorized_request_header)
        res.raise_for_status()

        for datasource in res.json():
            if datasource["name"] == "Zabbix" or datasource["type"] == "alexanderzobnin-zabbix-datasource":
                self.__zabbix_data_source_info = {"uid":datasource["uid"],"name":datasource["name"],"type":datasource["type"],"id":datasource["id"]}
                return
        else:
            raise  Exception(f"Zabbix data source doesnt exists\n No datasource name \"{self.__zabbix_data_source_info['name']}\" or datasource type \"{self.__zabbix_data_source_info['type']}\" found")



    def __create_dashboard(self):
        for host in self.__zabbix_data:
            for template in host["templateIds"]:

                item_key_dict =self.__parse_item_keys(template["itemlist"])
                print(item_key_dict)

            break




    def __parse_item_keys(self,items):

        """
        https://www.zabbix.com/documentation/current/en/manual/config/items/item/key#key-parameters

        :return:
        """
        final_dict = dict()


        for item in items:
            key = item["key_"]

            b_bracket_index = utils.safe_list_index(key,"[")
            e_bracket_index = utils.safe_list_index(key,"]")

            b_dot_index = utils.safe_list_index(key,".")


            if (b_dot_index < b_bracket_index) or (b_dot_index !=-1 and b_bracket_index == -1):
                if key[:b_dot_index] not in final_dict.keys():
                    final_dict.setdefault(key[:b_dot_index],[])

                else:
                    final_dict[key[:b_dot_index]].append(key[b_dot_index+1:])
            else:
                if key[:b_bracket_index] not in final_dict.keys():
                    final_dict.setdefault(key[:b_bracket_index+1],[])

                else:
                    final_dict[key[:b_bracket_index]].append(key[b_dot_index+1:])


        return final_dict