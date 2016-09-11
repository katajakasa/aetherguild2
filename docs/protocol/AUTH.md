# Auth module protocol docs

## 1. Login

Requests the server to authenticate the client with username and password. When correct user
credentials are supplied, returns session key & user data and sets the connection to authenticated state.

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

Response (server -> client):
```
{
    'route': 'auth.login',
    'receipt': <variable Receipt ID>, # Receipt ID, if one was supplied on request
    'error': false,
    'data': {
        'session_key': <str Session key>,
        'user': {
            'id': <int User ID>,
            'avatar': <str Avatar image url>,
            'username': <str Username>,
            'nickname': <str User nickname>,
            'level': <int User level>,
            'active': <bool Is user active>,
            'created_at': <str User creation timestamp>,
            'profile_data': <dict User profile data>,
            'last_contact': <str User last contact timestamp>
        }
    }
}
```

## 2. Authentication

Requests the server to authenticate the client with a session key. When a valid session key is  supplied,
returns session key & user data and sets the connection to authenticated state.

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

Response (server -> client):
```
{
    'route': 'auth.authenticate',
    'receipt': <variable Receipt ID>, // Receipt ID, if one was supplied on request
    'error': false,
    'data': {
        'session_key': '<str Session key>',
        'user': {
            'id': <int User ID>,
            'avatar': <str Avatar image url>,
            'username': <str Username>,
            'nickname': <str User nickname>,
            'level': <int User level>,
            'active': <bool Is user active>,
            'created_at': <str User creation timestamp>,
            'profile_data': <dict User profile data>,
            'last_contact': <str User last contact timestamp>
        }
    }
}
```

## 3. Logout

Requests the server to invalidate the current authenticated session.
All user privileges are dropped, all operations requiring authorization
will fail after this to error 403.

To run this command, user must have a valid session (be logged in).

Request (client -> server):
```
{
    'route': 'auth.logout',
    'receipt': <variable Receipt ID>,  # Optional
    'data': {}
}
```

Response (server -> client), success:
```
{
    'route': 'auth.logout',
    'receipt': <variable Receipt ID>, # Receipt ID, if one was supplied on request
    'error': false,
    'data': {}
}
```

## 4. Registration

Requests the server to register a new username/password combination.
If registration fails, a specific error is returned. Field requirements:
* Username must not be reserved, and must be 4-32 characters long.
* Nickname must not be reserved, and must be 2-32 characters long.
* Password must be 8 characters long. No upper limit.

Profile data field can be used to save a freeform JSON dict to the server.

Request (client -> server):
```
{
    'route': 'auth.register',
    'receipt': <variable Receipt ID>,  # Optional
    'data': {
        'username': <str Username>,
        'password': <str Password>,
        'nickname': <str Nickname>,
        'profile_data': <dict Freeform profile data>
    }
}
```

Response (server -> client), success:
```
{
    'route': 'auth.register',
    'receipt': <variable Receipt ID>, # Receipt ID, if one was supplied on request
    'error': false,
    'data': {}
}
```

## 5. Updating profile

Requests the server to update the currently logged in users profile.
If registration fails, a specific error is returned. Field requirements:
* Nickname must not be reserved, and must be 2-32 characters long.
* New password must be 8 characters long. No upper limit.
* Old password must match the users current password.

Profile data field can be used to save a freeform JSON dict to the server.

To run this command, user must have a valid session (be logged in).

Request (client -> server):
```
{
    'route': 'auth.update_profile',
    'receipt': <variable Receipt ID>,  # Optional
    'data': {
        'new_password': <str New password, Optional>,
        'old_password': <str Old, valid password. Mandatory if new_password is supplied>,
        'nickname': <str New nickname. Mandatory>,
        'profile_data': <dict User profile data, Mandatory>
    }
}
```

Response (server -> client), success:
```
{
    'route': 'auth.update_profile',
    'receipt': <variable Receipt ID>, # Receipt ID, if one was supplied on request
    'error': false,
    'data': {
        'user': {
            'id': <int User ID>,
            'avatar': <str Avatar image url>,
            'nickname': <str Nickname>,
            'level': <int User level>,
            'created_at': <iso8601 User creation date>,
            'profile_data': <dict User profile data>,
            'last_contact': <iso8601 Last contact with user>
        }
    }
}
```

## 6. Fetching profile

Requests the server to fetch the current user profile.

To run this command, user must have a valid session (be logged in).

Request (client -> server):
```
{
    'route': 'auth.get_profile',
    'receipt': <variable Receipt ID>,  # Optional
    'data': {}
}
```

Response (server -> client), success:
```
{
    'route': 'auth.get_profile',
    'receipt': <variable Receipt ID>, # Receipt ID, if one was supplied on request
    'error': false,
    'data': {
        'user': {
            'id': <int User ID>,
            'avatar': <str Avatar image url>,
            'nickname': <str Nickname>,
            'level': <int User level>,
            'created_at': <iso8601 User creation date>,
            'profile_data': <dict User profile data>,
            'last_contact': <iso8601 Last contact with user>
        }
    }
}
```

## 7. Setting avatar

Requests the server to download an avatar image from the internet and save
it to disk, then set it as the profile image for the user.

To run this command, user must have a valid session (be logged in).

Request (client -> server):
```
{
    'route': 'auth.update_avatar',
    'receipt': <variable Receipt ID>,  # Optional
    'data': {
        'url': <str Valid image url to fetch>
    }
}
```

Response (server -> client), success:
```
{
    'route': 'auth.update_avatar',
    'receipt': <variable Receipt ID>, # Receipt ID, if one was supplied on request
    'error': false,
    'data': {
        'user': {
            'id': <int User ID>,
            'avatar': <str Avatar image url>,
            'nickname': <str Nickname>,
            'level': <int User level>,
            'created_at': <iso8601 User creation date>,
            'profile_data': <dict User profile data>,
            'last_contact': <iso8601 Last contact with user>
        }
    }
}
```
