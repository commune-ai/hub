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
    app_name =  __file__.split('/')[-3] + '_app' 
    model='anthropic/claude-3.5-sonnet'
    free = True
    endpoints = ["get_modules", 'modules', 'add', 'remove', 'update', 'test']
    libname = __file__.split('/')[-1].split('.')[0]
    storage_path = os.path.expanduser('~/.'+libname)
    modules_path = os.path.expanduser(f'{storage_path}/modules')

    # In-memory storage for modules
    def __init__(self,password=None,**kwargs):
        self.password = password or self.get_password()
        self.user = self.get_user(self.password)
    
    def rm_module(self, module):
        return c.rm(self.module_path(module))
    
    def set_password(self, password):
        c.put(f'{self.storage_path}/password', password)
    
    def get_password(self):
        return c.get(f'{self.storage_path}/password', '12345')
    
    def module_path(self, module):
        return f"{self.modules_path}/{module}"
    
    def module_code_path(self, module):
        return f"{self.module_path(module)}/current"
    
    def module_info_path(self, module):
        return f"{self.module_code_path(module)}/module.json"
    
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
        return os.path.exists(self.module_path(module))
    
    def get_user(self, password=None):
        password = password or self.password
        from .user import User
        return User(password)

    def fork(self, module, new_module=None, password=None):
        user = self.get_user(password)
        module_info = self.module_info(module)
        code = module_info['code']
        name = module_info['name']
        key = module_info['key']
        data = {"code": code, "name": name, "key": key, "time": c.time()}
        return user.sign(data)
    
    def remove(self, module, password=None):
        user = self.get_user(password)
        module_info = self.module_info(module)
        owner = module_info['owner']
        assert user.key.ss58_address in owner, "User not in owners {}".format(owner)
        return c.rm(self.module_path(module))

    def add(self, path='./',  password=None):

        """
        key: str
        name: str
        code: dict
        address: str
        """
        path = c.resolve_path(path)
        code = c.file2text(path)
        name = path.split('/')[-1]
        user = self.get_user(password)

        params = {"code": code, 
                  "name": name, 
                  "time": c.time(), 
                  "key": user.key.ss58_address}
        data =  user.sign(params)

        assert user.verify(data), "Data not verified"
        self.check_module(data['data'])
        data = data['data']
        module_path = self.module_path(data["name"])
        current_module_path = module_path + '/current' 
        module_info_path = f"{current_module_path}/module.json"
        exists = os.path.exists(module_info_path)
        module_info = load_json(module_info_path, {})
        last_hash = module_info.get('code_hash', 'NA')
        code_hash = c.hash(code)
        assert last_hash != code_hash, "Code hashes match {} == {}".format(last_hash, code_hash)
        last_module_path = module_path + '/' + last_hash
        code = data['code']
        module_info['owner'] = user.key.ss58_address
        module_info['key'] = data['key']
        module_info['name'] = data['name']
        module_info['time'] = data['time']
        module_info['path'] = module_path
        module_info['last_hash'] = last_hash
        module_info['code_hash'] = code_hash
        if exists:
            c.mv(current_module_path, last_module_path)
        code_path = current_module_path + '/code'
        for p, t in code .items():
            c.put_text(code_path +p, t)
        save_json(module_info_path, module_info)
        return module_info

    def owners(self, module):
        return self.module_info(module)['owners']
    
    def pwd2key(self, password, crypto_type=1, **kwargs):
        return c.str2key(password, crypto_type=crypto_type, **kwargs)
    
    def is_owner(self, module, password=None):
        user = self.get_user(password).key.ss58_address
        module_info = self.module_info(module)
        return user.address in module_info['owners']

    def module_info(self,  model):
        return load_json( self.module_info_path(model) )

    def get_modules(self):
        return self.modules()
    
    def infos(self):
        return {m: self.module_info(m) for m in self.modules()}

    def module2path(self):
        return {p.split('/')[-1]: p for p in ls(self.modules_path)}
    
    def modules(self):
        return list(self.module2path().keys())
    
    def get_code(self, module):
        return self.get_module(module)['code']
         
    def exists(self, module: str):
        return os.path.exists(self.module_info(module))

    def update(self, module_id: str, module: Dict):
        if not self.exists(module_id):
            raise HTTPException(status_code=404, detail="Module not found")
        module = self.get_module(module_id)
        self.save_module(module_id, module)

    def kill_app(self, name=app_name, port=app_port):
        while c.port_used(port):
            c.kill_port(port)
        return c.kill(name)

    def get_key(self, password, **kwargs):
        return c.str2key(password, **kwargs)
    
    def commits(self, module='app', commit_chain=None, features=['key',  'time', 'code_hash', 'last_hash']):
        """
        The commits from a signel app
        """
        
        module_info =  self.module_info(module)
        commit_chain = commit_chain or []
        module_path = self.module_path(module)
        for p in ls(module_path):
            module_info_path = f"{p}/module.json"
            if os.path.exists(module_info_path):
                module_info = load_json(module_info_path)
                module_info = {k: module_info[k] for k in features}
                commit_chain.append(module_info)
        commit_chain = sorted(commit_chain, key=lambda x: x['time'])
        return commit_chain

    def admins(self):
        return c.get(f'{self.storage_path}/admin', [])
    
    def is_admin(self, key_address):
        return key_address in self.admins()
    
    def add_admin(self, key_address):
        admins = c.get(f'{self.storage_path}/admin', [])
        if key_address not in admins:
            admins.append(key_address)
            c.put(f'{self.storage_path}/admin', admins)
        return {key_address: 'added', 'admins': admins}
    
    def remove_admin(self, key_address):
        admins = c.get(f'{self.storage_path}/admin', [])
        if key_address in admins:
            admins.remove(key_address)
            c.put(f'{self.storage_path}/admin', admins)
        return {key_address: 'removed', 'admins': admins}
    