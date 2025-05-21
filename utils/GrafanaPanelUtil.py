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

    def create_panel(self,grafana_version:str,item :dict,host:list,source_info:dict):

        if item["value_type"] in ["character","text"]:
            panel = granafa_dashboard_jsons.GrafanaDicts.stat_single_value.copy()

        elif item["value_type"]== "numeric" and item["units"].lower()!="b" :
            panel = granafa_dashboard_jsons.GrafanaDicts.time.copy()

        elif item["value_type"]== "binary" or item["units"].lower()=="b":
            panel = granafa_dashboard_jsons.GrafanaDicts.gauge.copy()

        else:
            return None


        if self.curr_x+panel["gridPos"]["w"]>self.max_x:
            self.curr_x = 0
            self.curr_y= panel["gridPos"]["h"]+1


        panel["gridPos"]["x"] = self.curr_x
        panel["gridPos"]["y"] = self.curr_y

        self.curr_x += panel["gridPos"]["w"]


        panel["pluginVersion"] = grafana_version
        panel["targets"][0]["group"]["filter"] = f"/{host['host_groups']}/"
        panel["targets"][0]["host"]["filter"] = host['host']['name']
        panel["targets"][0]["item"]["filter"] = item["name_resolved"]
        panel["datasource"]["type"] = source_info["type"]
        panel["datasource"]["uid"] = source_info["uid"]
        panel["title"] = item["name_resolved"]

        return deepcopy(panel)