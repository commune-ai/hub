

import commune as c

class User:
   
    def __init__(self, password='12345' , crypto_type=1, **data):
        self.set_key(password=password, crypto_type=crypto_type)
        self.data = data
    
    def child(self, password=None, crypto_type=None):
        crypto_type = crypto_type or self.key.crypto_type
        child_password = password + self.password if password else self.password
        return User(child_password , crypto_type=crypto_type)
    
    def circuit(self, password):
        return c.hash(password)
    
    def address(self):
        return self.key.ss58_address
    
    def crypto_type(self):
        return self.key.crypto_type

    def set_key(self, password='12345', crypto_type=1):
        """
        set the key with a passord
        """
        self.password = password
        self.key = c.pwd2key(self.circuit(password), crypto_type=crypto_type)
        return {"msg": "Key created", "address": self.key.ss58_address, "crypto_type": self.key.crypto_type}
    
    def sign(self, data:dict):
        """
        Input: any
        Output:
        dict(
            data -> {hash:hash(data) time:utc_timestamp}
            signatures -> {address: {signature: signature(data), time: utc_timestamp, crypto_type: crypto_type}}
        )
        """
        data = c.copy(data)
        if "signatures" not in data:
            data = {"data": data, "signatures": {}}
        sigdata = {"hash": c.hash(data["data"]), "time": c.time()}
        data['signatures'][self.key.ss58_address] ={'signature': self.key.sign(sigdata).hex(),'crypto_type': self.key.crypto_type,"time": sigdata["time"] }
        return data
    
    def resolve_module_path(self, module):
        return c.abspath(f'~/.users/{self.key.ss58_address}/{module}.json')
    
    def get_module_name(self, path='./'):
        path = c.resolve_path(path)
        return path.split('/')[-1]

    @classmethod
    def verify(cls, data, max_staleness=10):
        data = c.copy(data)
        assert 'data' in data and 'signatures' in data, 'Data must have data and signatures'    
        signatures = data['signatures']
        data_hash = c.hash(data["data"])
        results = []
        for sigaddress, sig in signatures.items():
            staleness = c.time() - sig['time']
            assert staleness < max_staleness, f'Staleness {staleness} > {max_staleness}'
            sigdata = {"hash": data_hash, "time": sig["time"]}
            result = c.verify(auth=sigdata, signature=sig['signature'],  address=sigaddress)
            results += [result]
        return all(results)
    
    @classmethod
    def verify_threshold(self, data, addresses, n=1):     
        n_sig_addresses = len([address for address in addresses if address in data['signatures']])
        if n_sig_addresses < n:
            return False
        return self.verify(data)

    def __repr__(self):
        return f'User(key={self.key.ss58_address} type={self.key.crypto_type})'
    
    def __str__(self):
        return self.__repr__()

    @classmethod
    def test_single(cls, n=10, ticket={'a': 1}):
        for i in range(n):
            self = cls(password="1234" + str(i))
            ticket = self.sign(ticket)
            assert cls.verify(ticket), 'Ticket verification failed'
        return {"msg": "All tests passed", "test": "test_single"}

    @classmethod
    def test_threshold(cls, n=10, ticket={'a': 1}):
        users = [User(password="1234" + str(i)) for i in range(n)]
        user_addresses = [user.key.ss58_address for user in users]
        self = cls(password="1234c")
        for i, user in enumerate(users):
            ticket = user.sign(ticket)
            assert self.verify_threshold(ticket, user_addresses, i+1), 'Ticket verification failed'
        return {"msg": "All tests passed", "test": "test_threshold"}
    
    @classmethod
    def test(self):
        return [self.test_single(), self.test_threshold()]