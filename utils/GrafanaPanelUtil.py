from copy import deepcopy

import granafa_dashboard_jsons


class PanelGenerator:
    def __init__(self):
        self.max_x = 24
        self.curr_x=0
        self.curr_y= 0
    def reset(self):
        self.max_x = 24
        self.curr_x=0
        self.curr_y= 0

    def create_panel(self,grafana_version:str,item : dict,host:dict,source_info:dict):

        if item["value_type"] == "character" or item["value_type"] == "text":
            db = granafa_dashboard_jsons.GrafanaDicts.stat_single_value.copy()

        elif item["value_type"]== "numeric" and item["units"].lower()!="b" :
            db = granafa_dashboard_jsons.GrafanaDicts.time.copy()

        elif item["value_type"]== "binary" or item["units"].lower()=="b":
            db = granafa_dashboard_jsons.GrafanaDicts.gauge.copy()

        else:
            return  None

        if item["units"]:
            print(item["units"])
        if self.curr_x+db["gridPos"]["w"]>self.max_x:
            self.curr_x = 0
            self.curr_y= db["gridPos"]["h"]+1


        db["gridPos"]["x"] = self.curr_x
        db["gridPos"]["y"] = self.curr_y

        self.curr_x += db["gridPos"]["w"]


        db["pluginVersion"] = grafana_version
        db["targets"][0]["group"]["filter"] = f"/{host['host_groups']}/"
        db["targets"][0]["host"]["filter"] = host['host']['name']
        db["targets"][0]["item"]["filter"] = item["name_resolved"]
        db["datasource"]["type"] = source_info["type"]
        db["datasource"]["uid"] = source_info["uid"]
        db["title"] = item["name_resolved"]


        return deepcopy(db)