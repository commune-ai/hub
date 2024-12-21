

import commune as c
from hub.user import User
from hub.hub import Hub

def test_single(n=10, ticket={'a': 1}):
    for i in range(n):
        self = User(password="1234" + str(i))
        ticket = self.sign(ticket)
        assert User.verify(ticket), 'Ticket verification failed'
    return {"msg": "All tests passed", "test": "test_single"}

def test_threshold( n=10, ticket={'a': 1}):
    users = [User(password="1234" + str(i)) for i in range(n)]
    user_addresses = [user.key.ss58_address for user in users]
    for i, user in enumerate(users):
        ticket = user.sign(ticket)
        assert User.verify_threshold(ticket, user_addresses, i+1), 'Ticket verification failed'
    return {"msg": "All tests passed", "test": "test_threshold"}


# def test_add_module():
#     hub = Hub()
#     module = {
#         "data": {
#             "key": "key",
#             "name": "name",
#             "code": {
#                 "a": "1",
#                 "b": "2"
#             },
#             "address": "address",
#             "time": c.time(),
#             "crypto_type": "crypto_type"
#         }
#     }
#     return hub.add_module(module)

