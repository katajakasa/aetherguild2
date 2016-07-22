'use strict';

import React from 'react';
import ReactDOM from 'react-dom';
import { Link, Route, Router, RouteHandler, withRouter, hashHistory } from 'react-router';
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

var NoMatch = React.createClass({
    render: function () {
        return (<div>404</div>);
    }
});


var App = withRouter(React.createClass({
    render: function () {
        var state = this.state;
        return (
            <div id="wrapper" class="container-fluid">
                <div id="top-row" class="row">
                    <div id="header">
                        <h1 id="header_text">Æther</h1>
                        <h2 id="header_desc">Gaming since 2009</h2>
                    </div>
                </div>
                <div id="nav-row" class="row">
                    <ul id="nav">
                        <li>Frontpage</li>
                        <li>Forum</li>
                    </ul>
                </div>
                <div id="content-row" class="row">
                    <div id="left" class="col-lg-2 col-md-1">
                    </div>
                    <div id="content" class="col-lg-8 col-md-10">

                    {this.props.children}

                    </div>
                    <div id="right" class="col-lg-2 col-md-1">
                    </div>
                </div>
            </div>
        );
    }
}));

var routes = (
    <Router history={hashHistory}>
        <Route path="/" component={App}>
            <Route path="*" component={NoMatch}/>
        </Route>
    </Router>
);

ReactDOM.render(routes, document.getElementById('app'));
