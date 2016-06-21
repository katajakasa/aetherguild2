
'use strict';

export default class WSListener {
    constructor(address) {
        this.address = address
        this.waiting = {};
        this.listening = {};
        this.sock = null;
        this.should_close = true;
        this.reconnect_wait = 5000;
        this.receipt_wait = 15000;
        this.connect_timeout = null;
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
        var listener = this;
        return new Promise(function(resolve, reject) {
            listener.sock = new WebSocket(listener.address);
            listener.sock.onopen = function() {
                console.log("Connected to " + listener.address);
                listener.should_close = false;
                listener.sock.onclose = function(event) { listener.on_close(event); };
                listener.sock.onmessage = function(event) { listener.on_message(event); };
                resolve({'listener': listener});
            };
            listener.sock.onclose = function(event) {
                listener.reconnect(resolve);
            };
        });
    }

    reconnect(resolve) {
        var listener = this;
        if(listener.connect_timeout !== null) {
            return;
        }
        listener.connect_timeout = window.setTimeout(function() {
            listener.connect_timeout = null;
            listener.sock = new WebSocket(listener.address);
            listener.sock.onopen = function() {
                console.log("Connected to " + listener.address);
                listener.should_close = false;
                listener.sock.onclose = function(event) { listener.on_close(event); };
                listener.sock.onmessage = function(event) { listener.on_message(event); };
                if(resolve !== null) {
                    resolve({'listener': listener});
                }
            };
            listener.sock.onclose = function(event) {
                listener.reconnect(resolve);
            };
        }, listener.reconnect_wait);
    }

    on_close(listener, event) {
        console.log("Socket closed.");
        if(this.should_close === false) {
            console.log("Attempting to reconnect.");
            this.reconnect(null);
        }
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
            // Message has a receipt, try to resolve a Promise
            if(msg.receipt in this.waiting) {
                if(msg.error) {
                    this.reject_waiting_promise(msg.receipt, msg.data.error_message, msg.data.error_code);
                } else {
                    this.resolve_waiting_promise(msg.receipt, msg.data);
                }
            } else {
                console.error('Unexpected receipt ' + msg.receipt);
            }
        } else {
            // No receipt, this is a broadcast message
            if(msg.route in this.listening) {
                var callbacks = this.listening[msg.route];
                for(var i = 0; i < callbacks.length; i++) {
                    callbacks[i](msg.route, msg.data);
                }
            }
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
            if(listener.sock === null) {
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

    add_listener(route, callback) {
        /**
         * Adds a listener function for broadcast messages identified by route
         * @param {string} route - Routing tag to listen for
         * @param {function} callback - Callback function
         */
        if(!(route in this.listening)) {
            this.listening[route] = [];
        }
        this.listening[route].push(callback);
    }

    cancel_listener(route, callback) {
        /**
         * Cancel a broadcast message listener
         * @param {string} route - Routing tag
         * @param {function} callback - Callback function
         * @param {boolean} Was the listener removed succesfully
         */
        for(var i = 0; i < this.listening[route].length; i++) {
            if(this.listening[route][i] === callback) {
                this.listening[route].splice(i, 1);
                return true;
            }
        }
        return false;
    }

    cancel_route_listeners(route) {
        /**
         * Cancels all listeners for a route
         * @param {string} route - Routing tag
         */
        delete this.listening[route];
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
        this.listening = {};
        this.waiting = {};
    }

}
