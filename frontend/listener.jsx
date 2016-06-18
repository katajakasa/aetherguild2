
class Listener {
    constructor(address) {
        this.address = address
        this.waiting = {};
        this.should_close = false;
        this.reconnect_wait = 5000;
        this.receipt_wait = 15000;
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
                console.log("Connected to " + listener.address);
                resolve({listener: listener});
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
            window.setTimeout(this.connect, this.reconnect_wait);
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
                delete this.waiting[receipt];
                window.clearTimeout(cbs['timeout']);
                cbs['resolve']({
                    listener: this,
                    data: msg
                });
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
            var timeout = window.setTimeout(function() {
                var cbs = listener.waiting[receipt];
                delete listener.waiting[receipt];
                cbs['reject']({
                    listener: listener,
                    error_str: "Timeout",
                    error_code: -1
                });
            }, listener.receipt_wait);
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
        for(const key in Object.keys(this.waiting)) {
            var cbs = this.waiting[key];
            delete this.waiting[key];
            window.clearTimeout(cbs['timeout']);
            cbs['reject']({
                listener: this,
                error_str: "Listener closing",
                error_code: -2
            });
        }
    }

}


new Listener("ws://localhost:8000/ws").connect().then(function(obj) {
    obj.listener.request(
        "auth.login", {"username": "tuomas", "password": "test1234"}
    ).then(function(obj) {
        console.log(obj.data);
        return obj.listener.request("forum.get_combined_boards", {});
    }).then(function(obj) {
        console.log(obj.data);
        return obj.listener.request("auth.logout", {});
    }).then(function(obj) {
        console.log(obj.data);
        obj.listener.close();
    }).catch(function(obj) {
        console.log("Error: " + obj.error_str);
        obj.listener.close();
    });
});
