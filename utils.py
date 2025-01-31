import copy
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


def traverse_dict(d, path=""):


    if isinstance(d, dict):
        if not d:  # Check if the dictionary is empty

            yield path, {}  # Yield the empty dictionary
        for key, value in d.items():
            new_path = f"{path}.{key}" if path else key
            yield from traverse_dict(value, new_path)
    else:
        yield path, d


def update_panel_json(current_panel,key_path_splitted,dashboard):
    current_panel["type"] = "row"
    current_panel["title"] = key_path_splitted[0]


    dashboard["panels"].append(current_panel)



def tqdm_update(pbar,message):
    pbar.set_postfix({"Stage":message})
    pbar.update(1)