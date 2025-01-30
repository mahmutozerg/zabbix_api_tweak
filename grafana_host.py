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
        self.parse_item_keys()

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

    def parse_item_keys(self):

        """
        https://www.zabbix.com/documentation/current/en/manual/config/items/item/key#key-parameters

        :return:
        """

        temp_list = list()
        final_dict = dict()
        for host in self.__zabbix_data:
            for template in host["templateIds"]:
                for item in template["itemlist"]:
                    key = item["key_"]
                    b_bracket_index = utils.safe_list_index(key,"[")
                    e_bracket_index = utils.safe_list_index(key,"]")

                    bracket_splitted_values = ""
                    if e_bracket_index != -1 and b_bracket_index != -1:

                        dot_splitted_values= key[:b_bracket_index].split(".")
                        bracket_splitted_values = key[b_bracket_index:e_bracket_index+1]

                    else:
                        dot_splitted_values= key.split(".")


                    dot_splitted_values.append(bracket_splitted_values)

                    temp_list.append(dot_splitted_values)


            """
                    FUNCTION OF SHAME --> CREATED BY GPT
                    it converts list to a dict with removing the duplicate values
            """
            for entry in temp_list:
                # Start with the outermost key ('docker' in this case)
                current_dict = final_dict

                # Iterate over the elements in each sublist, except the last one
                for part in entry[:-1]:
                    # If the current part doesn't exist in the dictionary, create a new sub-dictionary
                    if part not in current_dict:
                        current_dict[part] = {}

                    # Move the reference to the next level in the dictionary
                    current_dict = current_dict[part]

                # The last element in the list is used as a key, with the corresponding value
                if entry[-1] != "":
                    current_dict[entry[-1]] = entry[-1]  # Store the value in the last element itself


            break

        utils.write_to_file(final_dict,"test2.json")