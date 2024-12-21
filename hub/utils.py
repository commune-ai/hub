
import json
import commune as c
import os

def load_json(file_path, default={}):
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except:
        return default
    

def save_json(file_path, data):
    dir_path = os.path.dirname(file_path)
    if not os.path.isdir(dir_path):
        os.makedirs(dir_path, exist_ok=True)
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

def logs(name):
    return c.logs(name)
    
def save_text(file_path, text):
    dir_path = os.path.dirname(file_path)
    if not os.path.isdir(dir_path):
        os.makedirs(dir_path, exist_ok=True)
    with open(file_path, 'w') as f:
        f.write(text)
    return {"msg": "Text saved", "path": file_path}


def ls(path:str):
    if not os.path.exists(path):
        print('WARNING IN LS --> Path does not exist:', path)
        return []
    path = os.path.abspath(path)
    return c.ls(path)
