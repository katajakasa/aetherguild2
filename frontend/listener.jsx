
class Listener {
    constructor(address) {
        this.address = address
        this.waiting = {};
        this.sock = null;
        this.should_close = false;
        this.reconnect_wait = 5000;
        this.receipt_wait = 15000;
        this.id = 1;
    }

    generate_id() {
        /**
         * Generates an unique ID for the session
         * @return {number} Unique ID
         */
        return this.id++;
    }

    connect() {
        /**
         * Connects to the websocket server.
         * @returns {Promise} Response
         */
        this.should_close = false;
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

    add_waiting_promise(receipt, resolve, reject, timeout) {
        /**
         * Adds a promise to the list of pending requests
         * @param {any} receipt - Receipt ID to wait for
         * @param {function} resolve - Resolve function for the Promise
         * @param {function} reject - Reject function for the Promise
         * @param {object} timeout - Timeout reference
         */
        this.waiting[receipt] = {
            'resolve': resolve,
            'reject': reject,
            'timeout': timeout
        };
    }

    reject_waiting_promise(receipt, error_msg, error_code) {
        /**
         * Rejects a waiting promise with a receipt ID
         * @param {any} receipt - Receipt ID to reject
         * @param {string} error_msg - Error message
         * @param {number} error_code - Error code
         */
        var cbs = this.waiting[receipt];
        delete this.waiting[receipt];
        window.clearTimeout(cbs.timeout);
        cbs.reject({
            'listener': this,
            'error_str': error_msg,
            'error_code': error_code
        });
    }

    resolve_waiting_promise(receipt, data) {
        /**
         * Resolves a waiting promise with a receipt ID
         * @param {any} receipt - Receipt ID to resolve
         * @param {dictionary} data - Response data
         */
        var cbs = this.waiting[receipt];
        delete this.waiting[receipt];
        window.clearTimeout(cbs.timeout);
        cbs.resolve({
            'listener': this,
            'data': data
        });
    }

    on_message(event) {
        var msg = JSON.parse(event.data);
        if('receipt' in msg) {
            if(msg.receipt in this.waiting) {
                if(msg.error) {
                    this.reject_waiting_promise(msg.receipt, msg.data.error_message, msg.data.error_code);
                } else {
                    this.resolve_waiting_promise(msg.receipt, msg.data);
                }
            } else {
                console.error('Couldn\'t resolve receipt ' + msg.receipt);
            }
        } else {
            // This is a broadcast message
            console.log('Caught broadcast: ' + event.data);
        }
    }

    request(route, data) {
        /**
         * Make an asynchronous request to the server
         * @param {string} route - Message routing string (effectively packet type)
         * @param {any} data - Data to send to the server
         * @return {Promise} - Response
         */
        var receipt = this.generate_id();
        var listener = this;
        return new Promise(function(resolve, reject) {
            if(listener.should_close === true) {
                reject({
                    'listener': listener,
                    'error_str': 'Listener is closed',
                    'error_code': -3
                });
            } else {
                var timeout = window.setTimeout(function() {
                    listener.reject_waiting_promise(receipt, 'Response timeout', -1);
                }, listener.receipt_wait);
                listener.add_waiting_promise(receipt, resolve, reject, timeout);
                listener.send(route, receipt, data);
            }
        });
    }

    send(route, receipt, data) {
        /**
         * Send a message through websocket to the server
         * @param {string} route - Message routing string (effectively packet type)
         * @param {any} receipt - Receipt ID for the message
         * @param {dictionary} data - Data to send to the server
         */
        this.sock.send(JSON.stringify({
            'route': route,
            'receipt': receipt,
            'data': data
        }));
    }

    close() {
        /**
         * Close the connection to server and reject any pending promises
         */
        this.should_close = true;
        for(const key in Object.keys(this.waiting)) {
            this.reject_waiting_promise(key, 'Listener closing', -2);
        }
        if(this.sock !== null) {
            this.sock.close();
            this.sock = null;
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
