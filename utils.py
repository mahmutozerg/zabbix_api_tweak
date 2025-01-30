import json


def raise_if_zabbix_response_error(res,func):
    if res.ok:
        content = res.json()
        if "error" in content:
            raise Exception(content["error"]["message"] + " " + content["error"]["data"])

    else:
        raise Exception(f"failed to send execute {func} function")



def safe_list_index(l, value, default=-1):
  try:
    res = l.index(value)
    return res
  except ValueError:
    return default


def write_to_file(data,file_name="data.json"):
    with open(file_name, "w") as file:
        json.dump(data, file,indent=4)


def read_from_zabbix_json_data(file_name="data.json"):
    with open(file_name, "r", encoding="utf-8") as file:
        data = json.load(file)

    return data

