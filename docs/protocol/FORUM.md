# Forum module protocol docs

## 1. Get forum sections

Requests the server to send forum sections that are available for the current user.

Request (client -> server):
```
{
    'route': 'forum.get_sections',
    'receipt': <variable Receipt ID>,  # Optional
}
```

Response (server -> client), success:
```
{
    'route': 'forum.get_sections',
    'receipt': <variable Receipt ID>, # Receipt ID, if one was supplied on request
    'error': false,
    'data': {
        'sections': [
        {
            'id': <int Section ID>,
            'sort_index': <int Sort index>,
            'title': <str Section title>,
        },
        {
            <...>
        }],
    },
}
```


## 2. Get forum boards

Requests the server to send forum boards that are available for the current user. If 'section' is added to the query,
only boards belonging to that section are returned.

Request (client -> server):
```
{
    'route': 'forum.get_boards',
    'receipt': <variable Receipt ID>,  # Optional
    'data': { # Optional
        'section': <int Section ID> # Optionsl
    }
}
```

Response (server -> client), success:
```
{
    'route': 'forum.get_boards',
    'receipt': <variable Receipt ID>, # Receipt ID, if one was supplied on request
    'error': false,
    'data': {
        'boards': [
        {
            'description': <str Board description>,
            'title': <std Board title>,
            'section': <int Section ID>,
            'sort_index': <int Sort index>,
            'req_level': <int Required user level>,
            'id': <int Board ID>
        },
        {
            <...>
        }],
    },
}
```

## 3. Get forum sections and boards as a tree

Requests the server to send forum sections and boards as an easily iterable tree structure. Only sections that have
viewable boards are listed, and only boards that the user has rights to are shown.

Request (client -> server):
```
{
    'route': 'forum.get_combined_boards',
    'receipt': <variable Receipt ID>,  # Optional
}
```

Response (server -> client), success:
```
{
    'route': 'forum.get_combined_boards',
    'receipt': <variable Receipt ID>, # Receipt ID, if one was supplied on request
    'error': false,
    'data': {
        'sections': [
        {
            'id': <int Section ID>,
            'sort_index': <int Sort index>,
            'title': <str Section title>,
            'boards': [
            {  
                'description': <str Board description>,
                'title': <std Board title>,
                'section': <int Section ID>,
                'sort_index': <int Sort index>,
                'req_level': <int Required user level>,
                'id': <int Board ID>
            },
            {
                <...>
            }],
        },
        { 
            <...>
        }],
    },
}
```

## 4. Get forum threads for board

Requests the server to send forum threads for a board.

Request (client -> server):
```
{
    'route': 'forum.get_threads',
    'receipt': <variable Receipt ID>,  # Optional
    'data': {
        'board': <int Board ID>,
        'start': <int Index of first result entry>,  # Optional
        'count': <int Number of result entries>  # Optional
    }
}
```

Response (server -> client), success:
```
{
    'route': 'forum.get_threads',
    'receipt': <variable Receipt ID>, # Receipt ID, if one was supplied on request
    'error': false,
    'data': {
        'users': [ # Contains all users shown in the threads
            <int User ID>: {
                'id': <int User ID>,
                'nickname': <str Nickname>,
                'level': <int User level>,
                'created_at': <iso8601 User creation date>,
                'last_contact': <iso8601 Last contact with user>
            }, 
            <int User ID>: {
                <...>
            }
        ],
        'threads': [
        {
            'id': <int Thread ID>,
            'board': <int Board ID>,
            'user': <int User ID for the owner (creator) of the thread>,
            'title': <str Section title>,
            'created_at': <iso8601 Creation date>,
            'views': <int Number of views>,
            'sticky': <bool Is thread sticky>,
            'closed': <bool Is thread closed>,
            'last_read': <iso8601 Last read by the user>,
        },
        {
            <...>
        }],
    },
}
```


## 5. Get forum posts for thread

Requests the server to send forum posts for a thread.

Request (client -> server):
```
{
    'route': 'forum.get_posts',
    'receipt': <variable Receipt ID>,  # Optional
    'data': {
        'board': <int Thread ID>,
        'start': <int Index of first result entry>,  # Optional
        'count': <int Number of result entries>  # Optional
    }
}
```

Response (server -> client), success:
```
{
    'route': 'forum.get_posts',
    'receipt': <variable Receipt ID>, # Receipt ID, if one was supplied on request
    'error': false,
    'data': {
        'users': [ # Contains all users shown in the posts
            <int User ID>: {
                'id': <int User ID>,
                'nickname': <str Nickname>,
                'level': <int User level>,
                'created_at': <iso8601 User creation date>,
                'last_contact': <iso8601 Last contact with user>
            }, 
            <int User ID>: {
                <...>
            }
        ],
        'posts': [
        {
            'id': <int Post ID>,
            'thread': <int Thread ID>,
            'user': <int User ID for the owner/creator of the post>,
            'message': <str Message>,
            'created_at': <iso8601 Creation date>,
            'edits': [
            {
                'id': <int Edit ID>,
                'post': <int Post ID>,
                'user': <int User ID>,
                'message': <str Edit message>,
                'created_at': <iso8601 Edit creation date>
            }, {
                <...>
            }]
        },
        {
            <...>
        }],
    },
}
```

## 6. Get forum post

Requests the server to send a single forum post

Request (client -> server):
```
{
    'route': 'forum.get_post',
    'receipt': <variable Receipt ID>,  # Optional
    'data': {
        'post': <int Post ID>,
    }
}
```

Response (server -> client), success:
```
{
    'route': 'forum.get_post',
    'receipt': <variable Receipt ID>, # Receipt ID, if one was supplied on request
    'error': false,
    'data': {
        'users': [ # Contains all users shown in the posts
            <int User ID>: {
                'id': <int User ID>,
                'nickname': <str Nickname>,
                'level': <int User level>,
                'created_at': <iso8601 User creation date>,
                'last_contact': <iso8601 Last contact with user>
            }, 
            <int User ID>: {
                <...>
            }
        ],
        'post': {
            'id': <int Post ID>,
            'thread': <int Thread ID>,
            'user': <int User ID for the owner/creator of the post>,
            'message': <str Message>,
            'created_at': <iso8601 Creation date>,
            'edits': [
                {
                    'id': <int Edit ID>,
                    'post': <int Post ID>,
                    'user': <int User ID for the owner/creator of the edit>,
                    'message': <str Edit message>,
                    'created_at': <iso8601 Edit creation date>
                },
                {
                    <...>
                }
            ] # /edits
        } # /post
    },
}
```

## 7. Upsert forum post

Inserts or updates a forum post. Insert if no ID is supplied, update if id is supplied and user owns the post.

## 8. Upsert forum thread

Inserts or updates a forum thread. Insert if no ID is supplied, update if id is supplied and user owns the thread.
