


class GrafanaDicts:

    dash_board_dict = {
    "annotations": {
        "list": [
            {
                "builtIn": 1,
                "datasource": {
                    "type": "grafana",
                    "uid": "-- Grafana --"
                },
                "enable": True,
                "hide": True,
                "iconColor": "rgba(0, 211, 255, 1)",
                "name": "Annotations & Alerts",
                "type": "dashboard"
            }
        ]
    },
    "editable": True,
    "fiscalYearStartMonth": 0,
    "graphTooltip": 1,
    "id": None,
    "links": [],
      "panels": [],
      "time": {
        "from": "now-6h",
        "to": "now"
      },
      "timepicker": {
        "refresh_intervals": []
      },
      "templating": {
        "list": []
      },

      "refresh": "5s",
      "schemaVersion": 17,
      "version": 0,
    }


    panel_row = {

        "collapsed":True,
        "gridPos": {
          "x": 0,
          "y": 0,
          "w": 12, #1,24
          "h": 9 # *30
        },
        "id":None,
        "panels":[],
        "title":"",
        "type":"row"
      }

    panel_data_time_series= {
        "datasource": {
            "type": "",
            "uid": ""
        },
        "fieldConfig": {
            "defaults": {
              "color": {
                "mode": "palette-classic"
              },
              "custom": {
                "axisBorderShow": False,
                "axisCenteredZero": False,
                "axisColorMode": "text",
                "axisLabel": "",
                "axisPlacement": "auto",
                "barAlignment": 0,
                "barWidthFactor": 0.6,
                "drawStyle": "line",
                "fillOpacity": 0,
                "gradientMode": "none",
                "hideFrom": {
                  "legend": False,
                  "tooltip": False,
                  "viz": False
                },
                "insertNulls": False,
                "lineInterpolation": "linear",
                "lineWidth": 1,
                "pointSize": 5,
                "scaleDistribution": {
                  "type": "linear"
                },
                "showPoints": "auto",
                "spanNulls": False,
                "stacking": {
                  "group": "A",
                  "mode": "none"
                },
                "thresholdsStyle": {
                  "mode": "off"
                }
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
                    "value": 90
                  },
                    {
                        "color": "yellow",
                        "value": 80
                    }
                ]
              }
            },
            "overrides": []
          },

        "collapsed":True,
        "gridPos": {
          "x": 0,
          "y": 0,
          "w": 12, #1,24
          "h": 9 # *30
        },

        "id":None,
        "options": {
            "legend": {
                "calcs": [],
                "displayMode": "list",
                "placement": "bottom",
                "showLegend": True
            },
            "tooltip": {
                "mode": "single",
                "sort": "none"
            },

        },
        "pluginVersion": "11.4.0",
        "targets":  [{
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
            "filter": "/read/"
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
        "itemids": "",

           "type":"timeseries"

    }

