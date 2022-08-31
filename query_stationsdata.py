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

def reflect(d,v):
    d += 1
    if isinstance(v,dict):
        for k in v.keys():
            print(' '.rjust(d*2),end='')
            print(f'Dict key<{k}>: value={reflect(d+1,v[k])}')
    elif isinstance(v,list):
        for l in v:
            print(' '.rjust(d*2),end='')
            print(f'List element <{reflect(d+1,l)}')

    return f'{type(v)}'

def main():
    sd = read_json_file("out/2022-08-30_17:16:40_stationsdata.json")
    reflect(0,sd)


if __name__ == '__main__':
    main()