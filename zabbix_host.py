import json
import time
from pprint import pp
from traceback import print_tb

import pandas as pd
import requests
import utils


from utils import write_to_file


class ZabbixHost:
    def __init__(self,ip,port,auth):
        """


            :param ip: zabbix server ip  http://192.168.0.1
            :param port: zabbix server port 80, 8080 etc
            :param auth: zabbix admin authentication token
        """

        self.__json_rpc_paths = ["/zabbix/api_jsonrpc.php","/api_jsonrpc.php"]
        self.valid_json_rpc_path = ""

        self.__host_addr = str.join(":",[ip,port])

        self.__bearer_token = auth
        self.__host_data = list(dict())

        self.default_authorized_request_header= {'Content-Type': 'application/json-rpc',"Authorization":f"Bearer {self.__bearer_token}"}
        self.default_unauthorized_request_header= {'Content-Type': 'application/json-rpc'}
        self.default_request_body= {"jsonrpc":"2.0","method":"apiinfo.version","params":{},"id":1}


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
        self.zabbix_value_types= {

            0 : "numeric" ,
            1 : "character",
            2 : "log",
            3 : "numeric",
            4 : "text",
            5 : "binary"
        }

        self.rpc_info  = dict()

        self.__test_connection()

        self.start()


    def __test_connection(self):

        """
        Checks for json rpc information
        :return:
        """

        status_codes = list()
        for path in self.__json_rpc_paths:
            res = requests.post(self.__host_addr+path,headers=self.default_unauthorized_request_header,data=json.dumps(self.default_request_body))
            status_codes.append(res.status_code)

            if res.ok:
                utils.raise_if_zabbix_response_error(res,"apiinfo.version")

                res = json.loads(res.content.decode("utf-8"))

                self.rpc_info = res
                self.valid_json_rpc_path = path

                return

        else:
            assert False,f"{list(zip(self.__json_rpc_paths,status_codes))} Failed to find rpc path, path/statuscode"


    def __do_request(self ,method,params=None):


        data =json.dumps({
            "jsonrpc": self.rpc_info["jsonrpc"],
            "method": method,
            "params":  params or {},
            "id": self.rpc_info["id"]
        })

        res = requests.post(self.__host_addr+self.valid_json_rpc_path,headers=self.default_authorized_request_header,data=data)

        content =utils.raise_if_zabbix_response_error(res,method)
        return content["result"]

    def get_hosts(self):

         return self.__do_request(
             method="host.get",
             params={
                "output": [
                    "hostid",
                    "host",
                ],
                 "selectParentTemplates": [
                     "templateid",
                     "name"
                 ],


            })



    def get_groups(self,host_id):
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
        res =self.__do_request(
            method="hostgroup.get"
            ,params={
                "output": ["name"],
                "hostids": host_id,
            })

        return "|".join(group["name"] for group in res)



    def get_items(self,hostids,tids):
        """
        DOCS -> https://www.zabbix.com/documentation/7.0/en/manual/api/reference/item/get?hl=item.get

        hostid in here means template's id
        "Zabbix server health" etc
        """

        from_template_ids_content =self.__do_request(
            method="item.get",
            params={
                "output": ["itemid","name","name_resolved","key_","units","formula","value_type","type","templateid","lastvalue"],
                "templateids":hostids,
                "sortfield": "itemid",
                "selectTags": "extend",
                "inherited":True


            }
        )

        from_template_ids_content_ =self.__do_request(
            method="item.get",
            params={
                "output": ["itemid","name","name_resolved","key_","units","formula","value_type","type","templateid","lastvalue","hostids"],
                "hostids":hostids,
                "sortfield": "itemid",
                "selectTags": "extend",
                "inherited":True


            }
        )

        utils.write_to_file(from_template_ids_content_,"test.json")
        #from_host_ids_content = self.get_item_s_real_templateid(from_template_ids_content,hostids)

        """
        host_dict = {hid["key_"]: hid for hid in from_host_ids_content}

        for tid in from_template_ids_content:
            hid = host_dict.get(tid["key_"])
            if hid:
                tid["name_resolved"] = hid["name_resolved"]
                tid["lastvalue"] = hid["lastvalue"]
                tid["value_type"] = self.zabbix_value_types[int(tid["value_type"])]
                tid["itemDiscovery"] = hid["itemDiscovery"]
                """


        return  from_template_ids_content


    def start(self):

        hosts = self.get_hosts()

        for host in [hosts[2]]:
            host_groups = self.get_groups(host["hostid"])


            items= self.get_items(host["hostid"],list(i["templateid"] for i in host["parentTemplates"]))


            data = {"host":host,"host_groups":host_groups,"items":items}
            write_to_file(data,"./hostdatas/"+host["host"]+".json")







