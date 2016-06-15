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
            "id": <int Section ID>,
            "sort_index": <int Sort index>,
            "title": <str Section title>,
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
        "boards": [
        {
            "description": <str Board description>,
            "title": <std Board title>,
            "section": <int Section ID>,
            "sort_index": <int Sort index>,
            "req_level": <int Required user level>,
            "id": <int Board ID>
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
            "id": <int Section ID>,
            "sort_index": <int Sort index>,
            "title": <str Section title>,
            "boards": [
            {  
                "description": <str Board description>,
                "title": <std Board title>,
                "section": <int Section ID>,
                "sort_index": <int Sort index>,
                "req_level": <int Required user level>,
                "id": <int Board ID>
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

## 5. Get forum posts for thread

## 6. Get forum post

## 7. Upsert forum post

## 8. Get forum thread

## 9. Upsert forum thread

