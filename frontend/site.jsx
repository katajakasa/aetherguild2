'use strict';

import React from 'react';
import ReactDOM from 'react-dom';
import WSListener from './listener';
import CONFIG from './settings';

var q = new WSListener(CONFIG.WEBSOCK_ADDRESS);
q.add_listener('auth.login', function(route, message) {
    console.log("Broadcast for " + route + " w/ " + message);
});
q.add_listener('auth.login', function(route, message) {
    console.log("Broadcast for " + route + " w/ " + message);
});
q.connect().then(function(obj) {
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
        obj.listener.cancel_route_listeners('auth.login');
        obj.listener.cancel_route_listeners('auth.logout');

    }).catch(function(obj) {
        console.log("Error: " + obj.error_str);

    });
});
