# Error handling

## Possible error codes

* 500: Server error. Server side bug.
* 400: Bad request. Your request was badly formed; client side bug.
* 401: Login failure; need to authenticate
* 403: Forbidden
* 450: Validation error. User supplied bad information in fields. User error.

## Error response format

Errors will always follow a certain format. Description below.

```
{
    "route": <str Route string>, # Route exists if one was supplied in the request
    "receipt": <variable Receipt ID>,  # Receipt field exists if one was supplied in the request
    "data": {
        "error_code": <int Error code, see above>,
        "error_messages": [
            {
                # Error messages with fields are tied to an inputted field
                "field": <str Field name>,
                "message": <str Error Message for field>
            },
            {
                # Error messages without field are generic errors
                "message": <str Generic error message>
            },
            ...
        ]
    },
    "error": true # Always exists and is true if error.
}
```
