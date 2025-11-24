from copy import deepcopy
import json
import math
# varsayalım granafa_dashboard_jsons modülü Grafana şablonlarını içeriyor
import granafa_dashboard_jsons


class PanelGenerator:
    def __init__(self):
        self.max_x = 24
        self.curr_x = 0
        self.curr_y = 0
        self.panel_id_counter = 1
        self.last_panel_group = None

    def reset(self):
        self.max_x = 24
        self.curr_x = 0
        self.curr_y = 0
        self.panel_id_counter = 1
        self.last_panel_group = None

    def _is_unixtime(self, item):
        """Öğenin unixtime birimi kullanıp kullanmadığını kontrol eder."""
        return (item.get("units") or "").lower() == "unixtime"

    def _is_stat_panel_type(self, item):
        """Öğenin Stat Panel (Tek Değer) tipi olup olmadığını kontrol eder."""
        return item["value_type"] in ["character", "text"] or self._is_unixtime(item)

    def _is_time_series_type(self, item):
        """Öğenin Zaman Serisi (Time Series) tipi olup olmadığını kontrol eder."""
        return item["value_type"] == "numeric" and (item.get("units") or "").lower() != "b" and not self._is_unixtime(
            item)

    def _is_gauge_type(self, item):
        """Öğenin Gauge/Binary (Ölçer) tipi olup olmadığını kontrol eder."""
        return item["value_type"] == "binary" or (item.get("units") or "").lower() == "b"

    def _get_panel_group(self, item):
        if self._is_stat_panel_type(item):
            return "System Information"
        elif self._is_time_series_type(item):
            return "Time Series Metrics"
        elif self._is_gauge_type(item):
            return "Usage Gauges"
        return "Other"

    def _get_smart_width(self, item):
        unit = (item.get("units") or "").lower()

        if self._is_time_series_type(item):
            return 12
        if self._is_gauge_type(item) or self._is_unixtime(item):
            # Gauge ve unixtime'ı küçük panellere aldık
            return 4

        # Metin/Karakter türleri için eski mantık
        last_value = str(item.get("lastvalue", ""))
        length = len(last_value)

        if length == 0: return 6
        if length <= 10:
            return 4
        elif length <= 25:
            return 6
        elif length <= 60:
            return 12
        else:
            return 24

    def _create_separator(self, title):
        if self.curr_x > 0:
            self.curr_x = 0
            # Aynı grupta olmasalar bile, ayraç öncesi yeni satır yapıyoruz
            self.curr_y += 1

        separator = {
            "id": self.panel_id_counter,
            "title": "",
            "type": "text",
            "gridPos": {"h": 2, "w": 24, "x": 0, "y": self.curr_y},
            "transparent": True,
            "options": {
                "mode": "markdown",
                "content": f"## 📌 {title}"
            }
        }
        self.panel_id_counter += 1
        self.curr_y += 2
        self.curr_x = 0
        return separator

    def _configure_stat_panel(self, item, panel):
        """Stat (Tek Değer) panelini yapılandırır."""
        if "options" not in panel: panel["options"] = {}
        if "reduceOptions" not in panel["options"]: panel["options"]["reduceOptions"] = {}

        panel["options"]["reduceOptions"]["calcs"] = ["lastNotNull"]
        # Varsayılan olarak item'ın resolved adını kullan
        panel["options"]["reduceOptions"]["fields"] = item["name_resolved"]
        panel["options"]["textMode"] = "value"
        panel["options"]["colorMode"] = "none"
        panel["options"]["graphMode"] = "none"
        panel["options"]["justifyMode"] = "auto"

        # 🎯 İSTENEN UNİXTIME GÜNCELLEMESİ
        if self._is_unixtime(item):
            panel["options"]["reduceOptions"]["values"] = False
            panel["options"]["reduceOptions"]["fields"] = "/^Time$/"  # Unix time için istenen regex filtre

        if "fieldConfig" not in panel: panel["fieldConfig"] = {"defaults": {}}
        if "defaults" not in panel["fieldConfig"]: panel["fieldConfig"]["defaults"] = {}

        # unixtime için 'dateTimeAsIso' birimini kullanmak daha uygun olabilir
        if self._is_unixtime(item):
            panel["fieldConfig"]["defaults"]["unit"] = "dateTimeAsIso"
        else:
            panel["fieldConfig"]["defaults"]["unit"] = "none"

        panel["fieldConfig"]["defaults"]["thresholds"] = {
            "mode": "absolute", "steps": [{"color": "transparent", "value": None}]
        }
        return panel

    def _configure_time_series_panel(self, item, panel):
        """Zaman Serisi panelini yapılandırır."""
        if "options" not in panel:
            panel["options"] = {}
        if "tooltip" not in panel["options"]:
            panel["options"]["tooltip"] = {}
        panel["options"]["tooltip"]["value_type"] = "single"

        zabbix_unit = (item.get("units") or "").lower()

        if "fieldConfig" not in panel:
            panel["fieldConfig"] = {"defaults": {}}
        if "defaults" not in panel["fieldConfig"]:
            panel["fieldConfig"]["defaults"] = {}

        if zabbix_unit == "uptime":
            panel["fieldConfig"]["defaults"]["unit"] = "dtdurations"
        elif zabbix_unit == "s":
            panel["fieldConfig"]["defaults"]["unit"] = "s"
        elif zabbix_unit == "%":
            panel["fieldConfig"]["defaults"]["unit"] = "percent"
        else:
            panel["fieldConfig"]["defaults"]["unit"] = zabbix_unit if zabbix_unit else "none"

        return panel

    def _configure_gauge_panel(self, item, panel):
        """Gauge (Ölçer) panelini yapılandırır."""
        if "options" not in panel: panel["options"] = {}
        if "reduceOptions" not in panel["options"]: panel["options"]["reduceOptions"] = {}
        panel["options"]["reduceOptions"]["calcs"] = ["lastNotNull"]
        panel["options"]["reduceOptions"]["fields"] = ""
        return panel

    def _update_grid_position(self, panel, item, current_group):
        """Panel genişliğini ve ızgara konumunu (x, y) ayarlar."""

        panel_width = self._get_smart_width(item)
        panel["gridPos"]["w"] = panel_width

        # Yüksekliği belirle
        if self._is_stat_panel_type(item):
            panel["gridPos"]["h"] = 4
        elif self._is_time_series_type(item):
            panel["gridPos"]["h"] = 8
        else:  # Gauge/Binary
            panel["gridPos"]["h"] = 6

        # Konumu belirle
        if self.curr_x + panel_width > self.max_x:
            self.curr_x = 0
            # Yükseklik hesaplamasını gruplara göre yap
            if current_group == "System Information":
                row_height = 4
            elif current_group == "Usage Gauges":
                row_height = 6
            else:  # Time Series
                row_height = 8

            self.curr_y += row_height

        panel["gridPos"]["x"] = self.curr_x
        panel["gridPos"]["y"] = self.curr_y
        self.curr_x += panel_width

        return panel

    def _configure_zabbix_target(self, panel, item, host, source_info):
        """Zabbix hedef (target) yapılandırmasını ayarlar."""

        ds_object = {"type": source_info["type"], "uid": source_info["uid"]}

        zabbix_target = {
            "refId": "A",
            "datasource": ds_object,
            "group": {"filter": f"/{host['host_groups']}/"},
            "host": {"filter": host['host']['name']},
            "item": {"filter": item["name_resolved"]},
            "options": {
                "showDisabledItems": False,
                "skipEmptyValues": True,
                "disableDataAlignment": False,
                "useZabbixValueMapping": False
            },
            "tags": [], "functions": []
        }

        # Stat panelleri (Metin/Karakter) için özel yapılandırma
        if self._is_stat_panel_type(item) and not self._is_unixtime(item):
            if item["value_type"] in ["character", "text"]:
                zabbix_target["queryType"] = "2"  # Değerleri Al
                zabbix_target["textFilter"] = ".*"
                zabbix_target["resultFormat"] = "time_series"
                zabbix_target["options"]["disableDataAlignment"] = True
                zabbix_target["itemids"] = str(item.get("itemid", ""))
                zabbix_target["application"] = {"filter": ""}
                zabbix_target["itemTag"] = {"filter": ""}
                zabbix_target["macro"] = {"filter": ""}
                zabbix_target["trigger"] = {"filter": ""}
                zabbix_target["proxy"] = {"filter": ""}
            else:
                zabbix_target["queryType"] = "0"
                zabbix_target["resultFormat"] = "time_series"

        # Diğer türler (Numeric, Binary, Unixtime)
        else:
            zabbix_target["queryType"] = "0"  # Trendleri Al
            zabbix_target["resultFormat"] = "time_series"

        panel["targets"] = [zabbix_target]
        return panel

    def create_panel(self, grafana_version: str, item: dict, host: list, source_info: dict):

        generated_panels = []
        current_group = self._get_panel_group(item)

        # Ayraç Ekleme
        if self.last_panel_group is None or self.last_panel_group != current_group:
            generated_panels.append(self._create_separator(current_group))

        self.last_panel_group = current_group

        panel = None

        # Panel Tipi Seçimi ve Yapılandırma
        if self._is_stat_panel_type(item):
            # Unixtime ve Metin/Karakter aynı paneli kullanır
            panel = deepcopy(granafa_dashboard_jsons.GrafanaDicts.stat_single_value)
            panel = self._configure_stat_panel(item, panel)

        elif self._is_time_series_type(item):
            panel = deepcopy(granafa_dashboard_jsons.GrafanaDicts.time)
            panel = self._configure_time_series_panel(item, panel)

        elif self._is_gauge_type(item):
            panel = deepcopy(granafa_dashboard_jsons.GrafanaDicts.gauge)
            panel = self._configure_gauge_panel(item, panel)

        else:
            # Tanımlanmamış türler
            return []

        # Ortak Ayarlar
        panel = self._update_grid_position(panel, item, current_group)

        panel["id"] = self.panel_id_counter
        self.panel_id_counter += 1
        panel["title"] = item["name_resolved"]

        # Veri Kaynağı ve Hedef
        ds_object = {"type": source_info["type"], "uid": source_info["uid"]}
        panel["datasource"] = ds_object
        panel = self._configure_zabbix_target(panel, item, host, source_info)

        generated_panels.append(panel)

        return generated_panels