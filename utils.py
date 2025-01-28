import json


def raise_if_zabbix_response_error(res,func):
    if res.ok:
        content = res.json()
        if "error" in content:
            raise Exception(content["error"]["message"] + " " + content["error"]["data"])

    else:
        raise Exception(f"failed to send execute {func} function")



def write_to_file(data):
    with open("data.json", "w") as file:
        json.dump(data, file,indent=4)