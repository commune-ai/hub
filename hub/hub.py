from fastapi import FastAPI, HTTPException
import uvicorn
import os
import json
from pydantic import BaseModel
from typing import Dict, Optional, Union
import commune as c 
import requests
from .utils import load_json, save_json, logs, ls

class Hub:
    server_port = 8000
    app_port = 3000
    model='anthropic/claude-3.5-sonnet'
    endpoints = ['modules', 'add', 'remove', 'update', 'test']
    libname = __file__.split('/')[-1].split('.')[0]
    storage_path = os.path.expanduser('~/.'+libname)
    modules_path = os.path.expanduser(f'{storage_path}/modules')

    # In-memory storage for modules
    def __init__(self,password=None,**kwargs):
        self.password = password or self.get_password()
        self.user = self.get_user(self.password)
    
    def rm_module(self, module):
        return c.rm(self.get_path(module))
    
    def new_password(self):
        password = c.hash(c.time())
        return password

    def get_password(self):
        return c.get(f'{self.storage_path}/password', self.new_password())

    def get_path(self, module):
        return f"{self.modules_path}/{module}"
    
    def get_latest_path(self, module):
        return f"{self.get_path(module)}/latest"
    
    def get_info_path(self, module):
        return f"{self.get_latest_path(module)}/module.json"

    
    
    def check_module(self, data, max_staleness=10):
        assert isinstance(data, dict), "Data must be a dictionary"
        assert 'key' in data, "Key not found"
        assert 'name' in data, "Name not found"
        assert 'code' in data and isinstance(data['code'], dict), "Code not found"
        assert 'time' in data, "Time not found"
        staleness = c.time() - int(data['time'])
        assert staleness < max_staleness, "Data is too old {}".format(staleness)
        return True
    
    def exists(self, module):
        return os.path.exists(self.get_path(module))
    
    def get_user(self, password=None):
        password = password or self.password
        from .user import User
        return User(password)
    
    def remove(self, module, password=None):
        user = self.get_user(password)
        info = self.get_info(module)
        owner = info['owner']
        assert user.key.ss58_address in owner, "User not in owners {}".format(owner)
        return c.rm(self.get_path(module))

    def add_from_path(self, path='./',  password=None, key=None, app=None):
        path = c.resolve_path(path)
        code = c.file2text(path)
        name = path.split('/')[-1]
        user = self.get_user(password)
        data = {"code": code, 
                  "name": name, 
                  "app": app ,
                  "time": c.time(), 
                  "key": user.key.ss58_address}
        data =  user.sign(data)
        assert user.verify(data), "Data not verified"
        self.check_module(data['data'])
        data = data['data']
        path = self.get_path(data["name"])
        current_path = path + '/latest' 
        info_path = f"{current_path}/module.json"
        info = load_json(info_path, {})
        previous_hash = info.get('code_hash', 'NA')
        code_hash = c.hash(code)
        assert previous_hash != code_hash, "Code hashes match {} == {}".format(previous_hash, code_hash)
        last_path = path + '/' + previous_hash
        code = data['code']
        info = {
            'owner': user.key.ss58_address,
            'key': data['key'], 
            'name': data['name'], 
            'time': data['time'],
            'previous_hash': previous_hash,
            'code_hash': code_hash
        }
        if os.path.exists(info_path):
            c.mv(current_path, last_path)
        code_path = current_path + '/code'
        for p, t in code .items():
            c.put_text(code_path +p, t)
        save_json(info_path, info)
        return info

    def owners(self, module):
        return self.get_info(module)['owners']
    
    def pwd2key(self, password, crypto_type=1, **kwargs):
        return c.str2key(password, crypto_type=crypto_type, **kwargs)

    def get_info(self,  model):
        return load_json( self.get_info_path(model) )

    def get_modules(self):
        return self.modules()
    
    def infos(self):
        return {m: self.get_info(m) for m in self.modules()}

    def module2path(self):
        return {p.split('/')[-1]: p for p in ls(self.modules_path)}
    
    def modules(self):
        return list(self.module2path().keys())
    
    def get_code(self, module):
        return self.get_module(module)['code']
         
    def exists(self, module: str):
        return os.path.exists(self.get_info(module))

    def update(self, module_id: str, module: Dict):
        if not self.exists(module_id):
            raise HTTPException(status_code=404, detail="Module not found")
        module = self.get_module(module_id)
        self.save_module(module_id, module)

    def commits(self, module='app', commit_chain=None, features=['key',  'time', 'code_hash', 'previous_hash']):
        """
        The commits from a signel app
        """
        info =  self.get_info(module)
        commit_chain = commit_chain or []
        path = self.get_path(module)
        for p in ls(path):
            info_path = f"{p}/module.json"
            if os.path.exists(info_path):
                info = load_json(info_path)
                info = {k: info[k] for k in features}
                commit_chain.append(info)
        commit_chain = sorted(commit_chain, key=lambda x: x['time'])
        return commit_chain
