# Admin module protocol docs

## 1. Get all users

This command requires admin level privileges!

Requests the server to send all existing users in the database.

Request (client -> server):
```
{
    'route': 'admin.get_users',
    'receipt': <variable Receipt ID>,  # Optional
    'data': {
        'include_deleted': <bool Include also deleted users in the result set>,
        'start': <int Start index, for paging, optional>,
        'count': <int Number of entries, for paging, optional>
    }
}
```

Response (server -> client), success:
```
{
    'route': 'admin.get_users',
    'receipt': <variable Receipt ID>, # Receipt ID, if one was supplied on request
    'error': false,
    'data': {
        'users': [
        {
            'id': <int User ID>,
            'avatar': <str Avatar image url>,
            'nickname': <str Nickname>,
            'level': <int User level>,
            'created_at': <iso8601 User creation date>,
            'last_contact': <iso8601 Last contact with user>,
            'username': <str Username>,
            'deleted'; <bool Is user deleted. If include_deleted is False, this is always False>
        },
        {
            <...>
        }],
    },
}
```

## 1. Delete user

This command requires admin level privileges!

Requests the server to remove a user by ID and immediately invalidate all
sessions belonging to that user. User cannot login after this.

Request (client -> server):
```
{
    'route': 'admin.delete_user',
    'receipt': <variable Receipt ID>,  # Optional
    'data': {
        'user': <int User ID>,
    }
}
```

Response (server -> client), success:
```
{
    'route': 'admin.delete_user',
    'receipt': <variable Receipt ID>, # Receipt ID, if one was supplied on request
    'error': false,
    'data': {},
}
```
