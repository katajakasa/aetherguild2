# aetherguild2

Website project for https://aetherguild.net

## 1. Installation

1. Copy aetherguild/config.py-dist to aetherguild/config.py
2. Edit the newly created aetherguild/config.py. Make sure you have AMQP vhost & mysql database set up.
3. pip install --upgrade -r requirements.txt
4. alembic upgrade head
5. Start by running `python -m aetherguild.listener_service.main` and `python -m aetherguild.socket_service.main`.

## 2. Packet formats

### 2.1. Authentication

Requests the server to authenticate the client with username and password. When correct user
credentials are supplied, returns session key and sets the connection to authenticated state.

On failure, a standard error packet is returned.

Request (client -> server):
```
{
    'type': 'login',
    'payload': {
        'username': '<username>',
        'password': '<password>'
    }
}
```

Response (server -> client), success:
```
{
    'type': 'login',
    'error': false,
    'payload': {
        'session_key': '<session_key>',
    }
}
```

Response (server -> client), failure:
```
{
    'type': 'login',
    'error': true,
    'payload': {
        'error_code': <error code>,
        'error_message': '<error message>',
    }
}
```