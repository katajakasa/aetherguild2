
class Listener {
    constructor(address) {
        this.address = address
        this.waiting = {};
        this.should_close = false;
        this.reconnect_wait = 5000;
        this.id = 1;
    }

    generate_id() {
        return this.id++;
    }

    connect() {
        var listener = this;
        return new Promise(function(resolve, reject) {
            listener.sock = new WebSocket(listener.address);
            listener.sock.onopen = function() {
                resolve();
            };
            listener.sock.onclose = function(event) {
                listener.on_close(event);
            };
            listener.sock.onmessage = function(event) {
                listener.on_message(event);
            };
            listener.sock.onerror = function(event) {
                listener.on_error(event);
            };
        });
    }

    on_close(event) {
        console.log("Socket closed.");
        if(this.should_close === false) {
            console.log("Attempting to reconnect in " + this.reconnect_wait + " milliseconds.");
            setTimeout(this.connect, this.reconnect_wait);
        }
    }

    on_error(error) {
        console.error('Error: ' + error);
    }

    on_message(event) {
        var msg = JSON.parse(event.data);
        if("receipt" in msg) {
            var receipt = msg['receipt'];
            if(receipt in this.waiting) {
                var cbs = this.waiting[receipt];
                console.log("Resolved " + receipt);
                clearTimeout(cbs['timeout']);
                cbs['resolve'](msg);
            } else {
                console.error("Couldnt't resolve receipt " + receipt);
            }
        } else {
            // This is a broadcast message
            console.log("Caught broadcast: " + event.data);
        }
    }

    request(route, data) {
        var receipt = this.generate_id();
        var listener = this;
        var p = new Promise(function(resolve, reject) {
            var timeout = setTimeout(function() {
                var cbs = listener.waiting[receipt];
                cbs['reject']("Timeout");
                delete listener.waiting[receipt];
            }, 15000);
            listener.waiting[receipt] = {
                'resolve': resolve,
                'reject': reject,
                'timeout': timeout
            };
        });
        this.send(route, receipt, data);
        return p;
    }

    send(route, receipt, data) {
        this.sock.send(JSON.stringify({
            'route': route,
            'receipt': receipt,
            'data': data
        }));
    }

    close() {
        this.should_close = true;
        this.sock.close();
        for(var key in this.waiting) {
            if(this.waiting.hasOwnProperty(key)) {
                var cbs = this.waiting[key];
                clearTimeout(cbs['timeout']);
                cbs['reject']("Listener closing");
                delete this.waiting[key];
            }
        }
    }

}

var listener = new Listener("ws://localhost:8000/ws");
listener.connect().then(function() {
    console.log("Connected!");
    listener.request(
        "auth.login", {"username": "tuomas", "password": "test1234"}
    ).then(function(data) {
        console.log(data);
        listener.request(
            "auth.logout", {}
        ).then(function(data) {
            console.log(data);
            listener.close();
        }).catch(function(error) {
            console.error("Error: " + error);
            listener.close();
        });
    }).catch(function(error) {
        console.error("Error: " + error);
        listener.close();
    });
});
