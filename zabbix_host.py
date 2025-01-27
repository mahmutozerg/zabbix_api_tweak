import json
import pprint

import requests


class ZabbixHost:
    def __init__(self,ip,port,auth):
        self.__json_rpc_paths = ["/zabbix/api_jsonrpc.php","/api_jsonrpc.php"]
        self.valid_json_rpc_path = ""

        self.__host_addr_list= [ip,port]
        self.__host_addr = str.join(":",self.__host_addr_list)

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

    def __test_connection(self):
        status_codes = list()
        for path in self.__json_rpc_paths:
            res = requests.post(self.__host_addr+path,headers=self.default_unauthorized_request_header,data=json.dumps(self.default_request_body))
            status_codes.append(res.status_code)
            if res.ok:
                res = json.loads(res.content.decode("utf-8"))
                self.rpc_info = res
                self.valid_json_rpc_path = path
                return

        else:
            assert False,f"{list(zip(self.__json_rpc_paths,status_codes))} Failed to find rpc path, path/statuscode"

    def get_hosts(self):
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

        if res.ok:
            content = res.json()

            if "error" in content:
                raise Exception(content["error"]["message"] + " " + content["error"]["data"])

            content = content["result"]

            self.__host_data.extend(content)
        else:
            raise Exception("failed to send execute host.get function")


    def get_templates(self):
        for host in self.__host_data:

            data =json.dumps({
                "jsonrpc": self.rpc_info["jsonrpc"],
                "method": "template.get",
                "params": {
                    "output":"templateid",
                    "hostids": host["hostid"],
                },
                "id": self.rpc_info["id"]
            })

            res = requests.post(self.__host_addr+self.valid_json_rpc_path,headers=self.default_authorized_request_header,data=data)

            host["templateid"] = list(dict())

            if res.ok:
                content = res.json()
                if "error" in content:
                    raise Exception(content["error"]["message"] + " " + content["error"]["data"])

                content = content["result"]
                for i in content:
                    host["templateid"].append(i)
            else:
                raise Exception("failed to send execute template.get function")

    def get_items(self):

        for host in self.__host_data:
            data =json.dumps({
                "jsonrpc": self.rpc_info["jsonrpc"],
                "method": "item.get",
                "params": {
                    "output": ["itemid","name","name_resolved","parameters","key_","delay","units","formula","type","value_type"],
                    "hostids": host["hostid"],
                    "sortfield": "name"
                },
                "id": self.rpc_info["id"]
            })

            res = requests.post(self.__host_addr+self.valid_json_rpc_path,headers=self.default_authorized_request_header,data=data)

            if res.ok:
                content = res.json()
                if "error" in content:
                    raise Exception(content["error"]["message"] + " " + content["error"]["data"])

                content = content["result"]

                for i in content:
                    i["value_type"] = self.zabbix_value_types[int(i["value_type"])]
                    i["type"] =  self.zabbix_item_types[int(i["type"])]
                host["itemlist"]=content

            else:
                raise Exception("failed to send execute item.get function")

        for i in self.__host_data[:1]:
            print(i["host"],"***************************\n")

            for j in i["itemlist"]:
                print(j["name_resolved"],j["units"],j["value_type"])


    def write(self):
        with open("data.json", "w") as file:
            json.dump(self.__host_data, file,indent=4)