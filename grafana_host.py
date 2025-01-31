from pprint import pp, pprint

import requests

import utils
from granafa_dashboard_jsons import  GrafanaDicts
from utils import traverse_dict
import copy
import  uuid

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

        self.__zabbix_data = utils.read_from_zabbix_json_data()

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



    def __create_dashboard(self):
        """
            creates dashboard with unserialized tree
            see comments
        :return:
        """
        for host in [self.__zabbix_data[-2]]:
            row_names = set()
            dashboard = copy.deepcopy(self.json_templates.dash_board_dict)
            dashboard["uid"] = str(uuid.uuid4()).split("-")[0]
            for template in host["templateIds"]:

                for item in template["itemlist"]:

                    item_key_dict=self.__parse_item_keys(item)

                    """
                            Alot of magic values but we are trying to deserialize our tree
                            
                            example:
                                :case 1: key.t1: row_name = panel_name = key.t1
                                :case 2: key.t1.t2: row_name = key.t1 , panel_name=t2
                                :case 2: key.t1.t2.t3: row_name = key.t1.t2, panel_name=t3
                            
                            the reason that we are checking if our last index starts with [
                            some key values are stored as key.t1[params], we dont want to create graphs for each params :D
                            
                            for more information please refer to:
                                     https://www.zabbix.com/documentation/current/en/manual/config/items/item/key#key-parameters
    
                    """

                    for key_path, value in traverse_dict(item_key_dict):
                        panel_row_copy = copy.deepcopy(self.json_templates.panel_row)
                        panel_data_time_series = copy.deepcopy(self.json_templates.panel_data_time_series)
                        splitted_key_values = key_path.split(".")

                        if splitted_key_values[-1].startswith("["):
                            splitted_key_values = splitted_key_values[:-1]


                        if len(splitted_key_values) <= 2:
                            row_name = ".".join(splitted_key_values)
                            graph_name = row_name

                        elif len(splitted_key_values) >2:
                            row_name = ".".join(splitted_key_values[:-1])
                            graph_name = splitted_key_values[-1]
                        else:
                            raise  Exception("Something really bad happend")

                        if row_name not in row_names:
                            row_names.add(row_name)

                            if item["value_type"] != "character":
                                panel_data_time_series["pluginVersion"] = self.grafana_version
                                hgroups = "|".join(group["name"] for group in host["groups"])
                                panel_data_time_series["targets"][0]["group"] = {"filter":f"/{hgroups}/"}
                                panel_data_time_series["targets"][0]["host"] = {"filter":host["host"]}
                                panel_data_time_series["targets"][0]["item"] = {"filter":item["name_resolved"]}

                                panel_row_copy["title"] = row_name


                                dashboard["panels"].append(panel_row_copy)
                                dashboard["panels"].append(panel_data_time_series)





            dashboard["title"] = host["host"]+" "+list(item_key_dict.keys())[0]
            utils.write_to_file(dashboard,"api_dashboard.json")
            break




    def __parse_item_keys(self,item):

        """
        https://www.zabbix.com/documentation/current/en/manual/config/items/item/key#key-parameters

        :return:
        """

        temp_list = list()
        final_dict = dict()
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
            Idk why i even asked this function lets but move on
            
            FUNCTION OF SHAME --> CREATED BY GPT
            converts list to tree like structure. It is populating the same keys
            
            for example [docker.example.key,
                        docker.example.key2]
                        
            becomes
            {
                docker: {
                    example:
                        [
                           {key:{}},
                           {key2:{}}
                        ]
                }
            }
    """
        for entry in temp_list:
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

            utils.write_to_file(final_dict,"test.json")
            return final_dict

