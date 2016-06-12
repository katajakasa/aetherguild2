# Protocol documentation

## 1. Login

Requests the server to authenticate the client with username and password. When correct user
credentials are supplied, returns session key & user data and sets the connection to authenticated state.

On failure, a standard error packet is returned.

Request (client -> server):
```
{
    'route': 'auth.login',
    'receipt': <variable Receipt ID>,  # Optional
    'data': {
        'username': <str Username>,
        'password': <str Password>
    }
}
```

Response (server -> client), success:
```
{
    'route': 'auth.login',
    'receipt': <variable Receipt ID>, # Receipt ID, if one was supplied on request
    'data': {
        'session_key': <str Session key>,
    }
}
```

Response (server -> client), failure:
```
{
    'route': 'auth.login',
    'receipt': <variable Receipt ID>, # Receipt ID, if one was supplied on request
    'error': true,
    'data': {
        'error_code': <int Error code>,
        'error_message': <str Error message>,
    }
}
```

Possible response error codes:
* 500: Server error
* 401: Login failure; need to authenticate

## 2. Authentication

Requests the server to authenticate the client with a session key. When a valid session key is  supplied,
returns session key & user data and sets the connection to authenticated state.

On failure, a standard error packet is returned.

Request (client -> server):
```
{
    'route': 'auth.authenticate',
    'receipt': <variable Receipt ID>,  // Optional
    'data': {
        'session_key': <str Session key>
    }
}
```

Response (server -> client), success:
```
{
    'route': 'auth.authenticate',
    'receipt': <variable Receipt ID>, // Receipt ID, if one was supplied on request
    'data': {
        'session_key': '<str Session key>',
        'user': {
            'id': <int User ID>,
            'username': <str Username>,
            'nickname': <str User nickname>,
            'level': <int User level>,
            'active': <bool Is user active>,
            'created_at': <str User creation timestamp>,
            'last_contact': <str User last contact timestamp>
        }
    }
}
```

Response (server -> client), failure:
```
{
    'route': 'auth.authenticate',
    'receipt': <variable Receipt ID>, // Receipt ID, if one was supplied on request
    'error': true,
    'data': {
        'error_code': <int Error code>,
        'error_message': <str Error message>,
    }
}
```

Possible response error codes:
* 500: Server error
* 401: Login failure; need to authenticate

