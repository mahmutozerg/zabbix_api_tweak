


class GrafanaDicts:

  stat_single_value = {
  "id": 4,
  "type": "stat",
  "title": "Total memory",
  "gridPos": {
    "x": 0,
    "y": 2,
    "h": 3,
    "w": 3
  },
  "fieldConfig": {
    "defaults": {
      "mappings": [],
      "thresholds": {
        "mode": "absolute",
        "steps": [
          {
            "color": "dark-blue",
            "value": None
          }
        ]
      },
      "color": {
        "mode": "thresholds"
      }
    },
    "overrides": []
  },
  "pluginVersion": "11.4.0",
  "targets": [
    {
      "application": {
        "filter": ""
      },
      "countTriggersBy": "",
      "evaltype": "0",
      "functions": [],
      "group": {
        "filter": ""
      },
      "host": {
        "filter": ""
      },
      "item": {
        "filter": ""
      },
      "itemTag": {
        "filter": ""
      },
      "macro": {
        "filter": ""
      },
      "options": {
        "count": False,
        "disableDataAlignment": False,
        "showDisabledItems": False,
        "skipEmptyValues": False,
        "useTrends": "default",
        "useZabbixValueMapping": False
      },
      "proxy": {
        "filter": ""
      },
      "queryType": "0",
      "refId": "A",
      "resultFormat": "time_series",
      "schema": 12,
      "table": {
        "skipEmptyValues": False
      },
      "tags": {
        "filter": ""
      },
      "textFilter": "",
      "trigger": {
        "filter": ""
      }
    }
  ],
  "datasource": {
    "type": "",
    "uid": ""
  },
  "options": {
    "reduceOptions": {
      "values": False,
      "calcs": [
        "lastNotNull"
      ],
      "fields": ""
    },
    "orientation": "auto",
    "textMode": "auto",
    "wideLayout": True,
    "colorMode": "background",
    "graphMode": "none",
    "justifyMode": "auto",
    "showPercentChange": False,
    "percentChangeColorMode": "standard"
  }
}