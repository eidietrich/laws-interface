import json


def make_bill_key(identifier):
    # Makes URL/filename friendly key from "HB XX"-style identfier
    return identifier.replace(' ', '-').lower()


def write_json(data, path, pretty=True, log=True):
    indent = 4 if pretty else 0
    with open(path, 'w') as f:
        json.dump(data, f, indent=indent)
    if log:
        print('Written to', path)


def read_json(path):
    print('Reading from', path)
    with open(path) as f:
        data = json.load(f)
        return data


def clean_name(raw):
    """
    Ensures standard forms for lawmaker names 

    TODO - implement this as necessary
    """
    replacements = {
        'Johnny B Good': 'John Good'  # Example
    }
    if raw in replacements.keys():
        return replacements[raw]
    return raw
