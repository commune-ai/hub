from fastapi import FastAPI, HTTPException
import uvicorn
import os
import json
from pydantic import BaseModel
from typing import Dict, Optional
import commune as c 
# Pydantic model for module dat
import requests

from .utils import load_json, save_json, logs, ls

class Hub:

    avoid_terms = ['__pycache__', '.ipynb_checkpoints', "node_modules", ".git", ".lock", "public", "json"]
    server_port = 8000
    app_port = 3000
    app_name =  __file__.split('/')[-3] + '_app' 
    model='anthropic/claude-3.5-sonnet'
    free = True
    endpoints = ["get_modules", 'modules', 'add_module', 'remove', 'update', 'test']
    modules_path = os.path.expanduser('~/.hub/modules')

    # In-memory storage for modules
    def __init__(self,password='12345',**kwargs):
        self.password = password
    
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
    
    def module_exists(self, module):
        return os.path.exists(self.module_path(module))
    

    def get_module_history_path(self, module):
        return f"{self.modules_path}/{module}/history"
    

    def get_user(self, key):
        from .user import User
        return User(key)



    def add(self, path='./', description=None, update=True, password=None):

        """
        key: str
        name: str
        code: dict

        address: str
        """
        password = password or self.password
        path = c.resolve_path(path)
        code = c.file2text(path)
        name = path.split('/')[-1]
        params = {"code": code, "name": name, 
                  "time": c.time(), 
                  "key": self.key.ss58_address,
                  'crypto_type': self.key.crypto_type,
                  "update": update}
        data =  self.get_user(password).sign(params)
        
        self.check_module(data['data'])
        data = data['data']
        module_path = self.module_path(data["name"])
        code_hash = c.hash(code)
        current_module_path = module_path + '/current' 
        module_info_path = f"{current_module_path}/module.json"
        module_exists = os.path.exists(module_info_path)
        module_info = load_json(module_info_path, {})
        last_hash = module_info.get('code_hash', 'NA')
        assert last_hash != code_hash, "Code hashes match {} == {}".format(last_hash, code_hash)
        last_module_path = module_path + '/' + last_hash
        update = data.pop("update", False)
        # famfff
        if module_exists: 
            if not update:
                raise Exception("Module already exists")
        code = data['code']
        module_info['key'] = data['key']
        module_info['name'] = data['name']
        module_info['time'] = data['time']
        module_info['crypto_type'] = data["crypto_type"]
        module_info['path'] = module_path.replace(os.path.expanduser('~'), '~')
        module_info['last_hash'] = last_hash
        module_info['code_hash'] = code_hash

        if module_exists:
            c.mv(current_module_path, last_module_path)
    
        for p, t in code .items():
            c.put_text(current_module_path + '/' +p, t)
        save_json(module_info_path, module_info)
        return module_info

    def module_info(self,  model):
        return load_json( self.module_info_path(model) )

    def get_modules(self):
        return self.modules()
    
    def module_infos(self):
        return {m: self.module_info(m) for m in self.modules()}

    def module2path(self):
        return {p.split('/')[-1]: p for p in ls(self.modules_path)}
    
    def modules(self):
        return list(self.module2path().keys())
    
    def get_code(self, module):
        return self.get_module(module)['code']
         
    def module_exists(self, module: str):
        return os.path.exists(self.module_info(module))
    
    def refresh_modules(self):
        for module in self.modules():
            self.get_module(module)

    def update(self, module_id: str, module: Dict):
        if not self.module_exists(module_id):
            raise HTTPException(status_code=404, detail="Module not found")
        module = self.get_module(module_id)
        self.save_module(module_id, module)


    def serve(self, port=server_port):
        return c.serve(self.module_name(), port=port)
    
    def kill_app(self, name=app_name, port=app_port):
        while c.port_used(port):
            c.kill_port(port)
        return c.kill(name)

    def app(self, name=app_name, port=app_port, remote=0):
        self.kill_app(name, port)
        c.cmd(f"pm2 start yarn --name {name} -- dev --port {port}")
        return c.logs(name, mode='local' if remote else 'cmd')

    def get_key(self, password, **kwargs):
        return c.str2key(password, **kwargs)
    
    def chain(self, module='app', commit_chain=None, features=['key',  'time', 'code_hash', 'last_hash']):
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

        