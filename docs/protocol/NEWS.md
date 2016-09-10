# News module protocol docs

## 1. Get all news items

Requests the server to send all news posts.

Request (client -> server):
```
{
    'route': 'news.get_news_posts',
    'receipt': <variable Receipt ID>,  # Optional
    'data': {
        'start': <int Start index, for paging, optional>,
        'count': <int Number of entries, for paging, optional>
    }
}
```

Response (server -> client), success:
```
{
    'route': 'news.get_news_posts',
    'receipt': <variable Receipt ID>, # Receipt ID, if one was supplied on request
    'error': false,
    'data': {
        'posts': [
        {
            'id': <int Post ID>,
            'nickname': <str Poster nickname>,
            'message': <int News item message content>,
            'created_at': <iso8601 User creation date>,
        },
        {
            <...>
        }],
    },
}
```

## 2. Get one news item

This command requires admin level privileges!

Requests the server to send one news item (identified by id).

Request (client -> server):
```
{
    'route': 'news.get_news_post',
    'receipt': <variable Receipt ID>,  # Optional
    'data': {
        'post': <bool News item ID>,
    }
}
```

Response (server -> client), success:
```
{
    'route': 'news.get_news_post',
    'receipt': <variable Receipt ID>, # Receipt ID, if one was supplied on request
    'error': false,
    'data': {
        'post': {
            'id': <int Post ID>,
            'nickname': <str Poster nickname>,
            'message': <int News item message content>,
            'created_at': <iso8601 User creation date>,
        }
    },
}
```

## 3. Add a new news post

This command requires admin level privileges!

Requests the server to create a new news post. Returns the newly created
news post object.

Request (client -> server):
```
{
    'route': 'news.insert_news_post',
    'receipt': <variable Receipt ID>,  # Optional
    'data': {
        'message': <bool News item message text>,
    }
}
```

Response (server -> client), success:
```
{
    'route': 'news.insert_news_post',
    'receipt': <variable Receipt ID>, # Receipt ID, if one was supplied on request
    'error': false,
    'data': {
        'post': {
            'id': <int Post ID>,
            'nickname': <str Poster nickname>,
            'message': <int News item message content>,
            'created_at': <iso8601 User creation date>,
        }
    },
}
```

## 4. Edit a new news post

This command requires admin level privileges!

Requests the server to edit an existing news post. Returns the edited news post object.

Request (client -> server):
```
{
    'route': 'news.update_news_post',
    'receipt': <variable Receipt ID>,  # Optional
    'data': {
        'post': <int Post ID>,
        'message': <bool News item message text>,
    }
}
```

Response (server -> client), success:
```
{
    'route': 'news.update_news_post',
    'receipt': <variable Receipt ID>, # Receipt ID, if one was supplied on request
    'error': false,
    'data': {
        'post': {
            'id': <int Post ID>,
            'nickname': <str Poster nickname>,
            'message': <int News item message content>,
            'created_at': <iso8601 User creation date>,
        }
    },
}
```

## 5. Delete a new news post

This command requires admin level privileges!

Requests the server to delete an existing news post. Returns the edited news post object.

Request (client -> server):
```
{
    'route': 'news.delete_news_post',
    'receipt': <variable Receipt ID>,  # Optional
    'data': {
        'post': <int Post ID>,
    }
}
```

Response (server -> client), success:
```
{
    'route': 'news.delete_news_post',
    'receipt': <variable Receipt ID>, # Receipt ID, if one was supplied on request
    'error': false,
    'data': {},
}
```
