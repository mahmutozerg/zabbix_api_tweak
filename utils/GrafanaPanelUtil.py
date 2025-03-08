from copy import deepcopy

import granafa_dashboard_jsons


class PanelGenerator:
    def __init__(self):
        self.max_x = 22
        self.curr_x=1
        self.curr_y= 0

    def create_panel(self,grafana_version:str,item : dict,host:dict,source_info:dict):
        if item["value_type"] == "character":
            db = granafa_dashboard_jsons.GrafanaDicts.stat_single_value.copy()
            db["pluginVersion"] = grafana_version
            db["targets"][0]["group"]["filter"] = f"/{host['host_groups']}/"
            db["targets"][0]["host"]["filter"] = host['host']['name']
            db["targets"][0]["item"]["filter"] = item["name"]
            db["datasource"]["type"] = source_info["type"]
            db["datasource"]["uid"] = source_info["uid"]
            db["title"] = item["name"]


        else:
            db = granafa_dashboard_jsons.GrafanaDicts.stat_single_value.copy()
            db["pluginVersion"] = grafana_version
            db["targets"][0]["group"]["filter"] = f"/{host['host_groups']}/"
            db["targets"][0]["host"]["filter"] = host['host']['name']
            db["targets"][0]["item"]["filter"] = item["name"]
            db["datasource"]["type"] = source_info["type"]
            db["datasource"]["uid"] = source_info["uid"]
            db["title"] = item["name"]

        if (self.curr_x % self.max_x) == 0:
            self.curr_y += 1
            self.curr_x = 1

        db["gridPos"]["x"] = self.curr_x - 1
        db["gridPos"]["y"] = self.curr_y

        self.curr_x += db["gridPos"]["w"]

        return deepcopy(db)