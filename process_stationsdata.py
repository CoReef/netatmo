import json

# Reading the content of the given JSON encoded file; returns a dictionary
def read_json_file(filename):
    with open(filename) as f:
        return json.load(f)

def find_path_step(keys,d):
    if not(keys):
        return d
    key = keys[0]
    if isinstance(d,dict):
        if key in d:
            return find_path_step(keys[1:],d[key])
        else:
            return []
    elif isinstance(d,list):
        r = []
        for list_elem in d:
            v = find_path_step(keys,list_elem)
            if v:
                r.append(v)
        return r
    else:
        return f'Unkown type <{type(d)}'

def find_path(p,d):
    keys = p.split('.')
    return find_path_step(keys,d)

def recursive_flatten(l,fl):
    for element in l:
        if isinstance(element,list):
            recursive_flatten(element,fl)
        else:
            fl.append(element)

def flatten(l):
    result = []
    recursive_flatten(l,result)
    return result

def print_dashboards(d):
    for dashboard in d:
        for k in dashboard.keys():
            print(f"{k} = {dashboard[k]}")
        print()

def main():
    sd = read_json_file("2022-07-14_16:51:11_stationsdata.json")
    dashboards = find_path('body.devices.dashboard_data',sd)
    dashboards.append(find_path('body.devices.modules.dashboard_data',sd))
    print_dashboards(flatten(dashboards))
    batteries = find_path('body.devices.modules.battery_percent',sd)
    print(batteries)


if __name__ == '__main__':
    main()
      