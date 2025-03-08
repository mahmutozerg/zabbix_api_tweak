

"""
w: Width of the panel, ranging from 1 to 24 (as the dashboard width is divided into 24 columns)
h: Height of the panel in grid units, where each unit represents 30 pixels
x: The x-coordinate (horizontal position) of the panel, using the same unit as w
y: The y-coordinate (vertical position) of the panel, using the same unit as h

"""
class GrafanaDicts:

  stat_single_value = {
  "id": 4,
  "type": "stat",
  "title": "Total memory",
  "gridPos": {
    "x": 0,
    "y": 0,
    "h": 3,
    "w": 3
  },
  "fieldConfig": {
    "defaults": {
      "mappings": [],
      "thresholds": {
        "mode": "percentage",
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
        "useZabbixValueMapping": True,
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
        "lastNotNone"
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

  time = {
  "id": 1,
  "type": "timeseries",
  "title": "",
  "gridPos": {
    "x": 0,
    "y": 0,
    "h": 8,
    "w": 12
  },
  "fieldConfig": {
    "defaults": {
      "custom": {
        "drawStyle": "line",
        "lineInterpolation": "linear",
        "barAlignment": 0,
        "barWidthFactor": 0.6,
        "lineWidth": 1,
        "fillOpacity": 0,
        "gradientMode": "none",
        "spanNones": False,
        "insertNones": False,
        "showPoints": "auto",
        "pointSize": 5,
        "stacking": {
          "mode": "none",
          "group": "A"
        },
        "axisPlacement": "auto",
        "axisLabel": "",
        "axisColorMode": "text",
        "axisBorderShow": False,
        "scaleDistribution": {
          "type": "linear"
        },
        "axisCenteredZero": False,
        "hideFrom": {
          "tooltip": False,
          "viz": False,
          "legend": False
        },
        "thresholdsStyle": {
          "mode": "off"
        }
      },
      "color": {
        "mode": "palette-classic"
      },
      "mappings": [],
      "thresholds": {
        "mode": "percentage",
        "steps": [
          {
            "color": "green",
            "value": None
          },
          {
            "color": "red",
            "value": 80
          }
        ]
      }
    },
    "overrides": []
  },
  "pluginVersion": "11.4.0",
  "targets": [
    {
      "schema": 12,
      "queryType": "0",
      "group": {
        "filter": ""
      },
      "host": {
        "filter": ""
      },
      "application": {
        "filter": ""
      },
      "itemTag": {
        "filter": ""
      },
      "item": {
        "filter": ""
      },
      "macro": {
        "filter": ""
      },
      "functions": [],
      "trigger": {
        "filter": ""
      },
      "countTriggersBy": "",
      "tags": {
        "filter": ""
      },
      "proxy": {
        "filter": ""
      },
      "textFilter": "",
      "evaltype": "0",
      "options": {
        "showDisabledItems": False,
        "skipEmptyValues": False,
        "disableDataAlignment": False,
        "useZabbixValueMapping": True,
        "useTrends": "default",
        "count": False
      },
      "table": {
        "skipEmptyValues": False
      },
      "datasource": {
        "type": "alexanderzobnin-zabbix-datasource",
        "uid": "dear3yqvb25mob"
      },
      "refId": "A",
      "resultFormat": "time_series"
    }
  ],
  "datasource": {
    "type": "alexanderzobnin-zabbix-datasource",
    "uid": "dear3yqvb25mob"
  },
  "options": {
    "tooltip": {
      "mode": "single",
      "sort": "none"
    },
    "legend": {
      "showLegend": True,
      "displayMode": "list",
      "placement": "bottom",
      "calcs": [
        "max",
        "mean",
        "median",
        "min"
      ]
    }
  }
}
  
  gauge ={
    "id": 1,
    "type": "gauge",
    "title": "Panel Title",
    "gridPos": {
      "x": 0,
      "y": 0,
      "h": 6,
      "w": 6
    },
    "fieldConfig": {
      "defaults": {
        "mappings": [],
        "thresholds": {
          "mode": "percentage",
          "steps": [
            {
              "color": "green",
              "value": None
            },
            {
              "color": "red",
              "value": 80
            }
          ]
        },
        "color": {
          "mode": "thresholds"
        },
        "unit": "gbytes"
      },
      "overrides": []
    },
    "pluginVersion": "11.4.0",
    "targets": [
      {
        "schema": 12,
        "queryType": "0",
        "group": {
          "filter": "Applications"
        },
        "host": {
          "filter": "Zabbix server"
        },
        "application": {
          "filter": ""
        },
        "itemTag": {
          "filter": ""
        },
        "item": {
          "filter": "Accepted connections per second"
        },
        "macro": {
          "filter": ""
        },
        "functions": [],
        "trigger": {
          "filter": ""
        },
        "countTriggersBy": "",
        "tags": {
          "filter": ""
        },
        "proxy": {
          "filter": ""
        },
        "textFilter": "",
        "evaltype": "0",
        "options": {
          "showDisabledItems": False,
          "skipEmptyValues": False,
          "disableDataAlignment": False,
          "useZabbixValueMapping": True,
          "useTrends": "default",
          "count": False
        },
        "table": {
          "skipEmptyValues": False
        },
        "datasource": {
          "type": "alexanderzobnin-zabbix-datasource",
          "uid": "dear3yqvb25mob"
        },
        "refId": "A",
        "resultFormat": "time_series"
      }
    ],
    "datasource": {
      "type": "alexanderzobnin-zabbix-datasource",
      "uid": "dear3yqvb25mob"
    },
    "options": {
      "reduceOptions": {
        "values": False,
        "calcs": [
          "lastNotNone"
        ],
        "fields": ""
      },
      "orientation": "auto",
      "showThresholdLabels": False,
      "showThresholdMarkers": True,
      "sizing": "auto",
      "minVizWidth": 75,
      "minVizHeight": 75
    }
  }