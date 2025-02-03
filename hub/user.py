

import commune as c
class User:
    
    storage_path = '~/.hub/users'

    def __init__(self, password='12345' , crypto_type=1, **data):
        self.set_key(password=password, crypto_type=crypto_type)
        self.data = data
    
    def circuit(self, password):
        """
        The circuit function is a circuit between the password and the key 
        [password] -> circuit(password) -> suri -> [key]
        """
        return c.hash(password)
    
    def get_key(self, password='12345', crypto_type=1):
        key = c.pwd2key(self.circuit(password), crypto_type=crypto_type)
        return key
    
    def set_key(self, password='12345', crypto_type=1):
        self.key = self.get_key(password, crypto_type=crypto_type)
        return self.key
    
    def resolve_key(self, key=None, password=None):
        if key is not None:
            return key
        if password is not None:
            return 
        return self.key
    def sign(self, data:dict, key=None, password=None, crypto_type=1):
        data = c.copy(data)
        return c.sign(data, key=key, crypto_type=crypto_type)
    
    def resolve_module_path(self, module):
        return c.abspath(f'~/.users/{self.key.ss58_address}/{module}.json')
    
    def get_module_name(self, path='./'):
        path = c.resolve_path(path)
        return path.split('/')[-1]

    @classmethod
    def verify(cls, data, max_staleness=10):
        data = c.copy(data)
        assert 'data' in data and 'signature' in data and 'address' in data, 'Data must have data and signature'    
        return c.verify(data)
    
    @classmethod
    def verify_threshold(self, data, addresses, n=1):     
        n_sig_addresses = len([address for address in addresses if address in data['signature']])
        if n_sig_addresses < n:
            return False
        return self.verify(data)

    def __repr__(self):
        return f'User(key={self.key.ss58_address} type={self.key.crypto_type})'
    
    def __str__(self):
        return self.__repr__()
