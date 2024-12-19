from fastapi import FastAPI, HTTPException
import uvicorn
import os
import json
from pydantic import BaseModel
from typing import Dict, Optional
import hub as c 
# Pydantic model for module dat
import requests

from .utils import load_json, save_json, logs, ls

class Hub:

    server_port = 8000
    app_port = 3000
    app_name =  __file__.split('/')[-3] + '_app' 
    model='anthropic/claude-3.5-sonnet'
    free = True
    endpoints = ["get_modules", 'modules', 'add_module', 'remove', 'update', 'test']
    modules_path = os.path.expanduser('~/.hub/modules')

    def __init__(self, network='local'):
        self.network_module = c.module(network)()
    
    # In-memory storage for modules
    
    def module_path(self, module):
        return f"{self.modules_path}/{module}"
    
    def module_info_path(self, module):
        return f"{self.module_path(module)}/module.json"
    
    def module_history_path(self, module):
        return f"{self.module_path(module)}/history"
    
    def check_module(self, data, staleness=10):
        assert isinstance(data, dict), "Data must be a dictionary"
        assert 'key' in data, "Key not found"
        assert 'name' in data, "Name not found"
        assert 'code' in data and isinstance(data['code'], dict), "Code not found"
        assert 'time' in data, "Time not found"
        staleness = c.time() - int(data['time'])
        assert staleness < staleness, "Data is too old {}".format(staleness)
        return True
    
    def module_exists(self, module):
        return os.path.exists(self.module_path(module))

    def add_module(self, module: dict):
        """
        key: str
        name: str
        code: dict
        address: str
        """
        data = module["data"]
        update = data.pop("update", False)
        module_path = self.module_path(data["name"])
        module_info_path = f"{module_path}/module.json"
        module_info = load_json(module_info_path, {})
        module_exists = os.path.exists(module_path)
        if module_exists: 
            if not update:
                raise Exception("Module already exists")
        self.check_module(data)
        code = data.pop('code', None)
        module_info['last_hash'] = c.copy(module_info.get('code_hash', None))
        module_info['code_hash'] = c.hash(code)
        module_info['key'] = data['key']
        module_info['name'] = data['name']
        module_info['time'] = c.time()
        module_info['crypto_type'] = data.get('crypto_type', 1)
        module_info['path'] = module_path.replace(os.path.expanduser('~'), '~')
        path2text = {f"{module_path}/{p}": t for p, t in code.items()}

        if os.path.exists(module_path) and update:
            c.rm(module_path)
        for p, t in path2text.items():
            c.put_text(p, t)
        save_json(module_info_path, module_info)
        return module_info
    
    def test(self):
        from .user import User
        user = User()
        return user

    def module_info(self, model):
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
         
    def module_exists(self, module_id: str):
        return os.path.exists(self.module_info_path(module_id))
    
    def refresh_modules(self):
        for module in self.modules():
            self.get_module(module)

    def update(self, module_id: str, module: Dict):
        if not self.module_exists(module_id):
            raise HTTPException(status_code=404, detail="Module not found")
        module = self.get_module(module_id)
        
        self.save_module(module_id, module)

    avoid_terms = ['__pycache__', '.ipynb_checkpoints', "node_modules", ".git", ".lock", "public", "json"]

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

    networks = ['ethereum',
                 'bitcoin', 
                 'solana', 
                 'bittensor', 
                 'hub']
    def is_valid_network(self, network):
        return network in self.networks
    
    def get_key(self, password, **kwargs):
        return c.str2key(password, **kwargs)
    
