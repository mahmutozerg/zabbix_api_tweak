import json
import requests
import utils

import time
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

        self.get_hosts()
        self.get_templates()
        self.get_groups()
        self.get_items()

        utils.write_to_file(self.__host_data)

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

    def get_hosts(self):
        """
        DOCS -> https://www.zabbix.com/documentation/7.0/en/manual/api/reference/host/get?hl=host.get

        Gets all hosts, includes ip of them
        output consist of host,hostid and interface ip
         example:

            "hostid": "10655",
            "host": "WordpressKali",
            "interfaces": [
                {
                    "ip": "192.168.0.20"
                }
        :return:
        """



        data =json.dumps({
            "jsonrpc": self.rpc_info["jsonrpc"],
            "method": "host.get",
            "params": {
                "output": [
                    "hostid",
                    "host",
                ],
                "selectInterfaces": [
                    "ip"
                ]
            },
            "id": self.rpc_info["id"]
        })


        res = requests.post(self.__host_addr+self.valid_json_rpc_path,headers=self.default_authorized_request_header,data=data)



        utils.raise_if_zabbix_response_error(res,"host.get")

        content = res.json()
        content = content["result"]

        self.__host_data.extend(content)


    def get_groups(self):
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
        for host in self.__host_data:
            data =json.dumps({
                "jsonrpc": self.rpc_info["jsonrpc"],
                "method": "hostgroup.get",
                "params": {
                    "output": ["name"],
                    "hostids": host["hostid"],
                },
                "id": self.rpc_info["id"]
            })
            res = requests.post(self.__host_addr + self.valid_json_rpc_path, headers=self.default_authorized_request_header,data=data)

            utils.raise_if_zabbix_response_error(res, "hostgroup.get")
            host["groups"] = res.json()["result"]



    def get_templates(self):
        """
        DOCS -> https://www.zabbix.com/documentation/7.0/en/manual/api/reference/template/get?hl=template.get

        gets all templates that host's belong to
        output consist of only templateid and name parameters
        example :
            templateIds:
                [
                    {"templateid": "x", name": "Docker by Zabbix agent 2"  },
                    {"templateid": "yy","name": "Zabbix server health" }
                ]

        :return:
        """
        for host in self.__host_data:

            data =json.dumps({
                "jsonrpc": self.rpc_info["jsonrpc"],
                "method": "template.get",
                "params": {
                    "output": ["templateid", "name"],
                    "hostids": host["hostid"],
                },
                "id": self.rpc_info["id"]
            })

            res = requests.post(self.__host_addr+self.valid_json_rpc_path,headers=self.default_authorized_request_header,data=data)

            utils.raise_if_zabbix_response_error(res, "template.get")

            host["templateIds"] = list(dict())

            content = res.json()
            content = content["result"]

            for i in content:
                host["templateIds"].append(i)


    def get_items(self):
        """
        DOCS -> https://www.zabbix.com/documentation/7.0/en/manual/api/reference/item/get?hl=item.get

        gets all items from templates that host's belong to and adds it into template information under the key of itemlist
        skips items that has no lastvalue

        output consist of itemid,name,name_resolved,parameters,key_,delay,units,formula,type,value_type

        example :
            templateIds:
                [
                    {"templateid": "x", name": "Docker by Zabbix agent 2" ,itemlist: [{},{}] },
                    {"templateid": "yy","name": "Zabbix server health",itemlist: [{},{}] }
                ]

        :return:
        """
        for host in self.__host_data:
            for templateId in host["templateIds"]:
                data =json.dumps({
                    "jsonrpc": self.rpc_info["jsonrpc"],
                    "method": "item.get",
                    "params": {
                        "output": ["itemid","name","name_resolved","lastvalue","key_","delay","units","formula","type","value_type"],
                        "templateid": templateId,
                        "hostids": host["hostid"],
                        "sortfield": "key_"
                    },
                    "id": self.rpc_info["id"]
                })

                res = requests.post(self.__host_addr+self.valid_json_rpc_path,headers=self.default_authorized_request_header,data=data)

                utils.raise_if_zabbix_response_error(res,"item.get")

                content = res.json()

                ##removing the empty last values
                content = [i for i in content["result"] if i["lastvalue"] is not None and i["lastvalue"].strip() != ""]

                for i in content:
                    i["value_type"] = self.zabbix_value_types[int(i["value_type"])]
                    i["type"] = self.zabbix_item_types[int(i["type"])]



                templateId["itemlist"] = content





