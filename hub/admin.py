import commune as c
class Admin:
    def admins(self):
        return c.get(f'{self.storage_path}/admin', [])
    
    def is_admin(self, address):
        return address in self.admins()
    
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