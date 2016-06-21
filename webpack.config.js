var path = require('path'),
    webpack = require('webpack');

var config = {
    //watch: true,
    entry: path.resolve(__dirname, 'frontend/site.jsx'),
    output: {
        path: path.resolve(__dirname, 'target'),
        filename: 'app.js',
        sourceMapFilename: 'app.js.map',
    },
    module: {
        loaders: [{
            test: /\.jsx?$/,
            exclude: /node_modules/,
            loader: 'babel-loader',
            query:
            {
                presets: ['es2015', 'react']
            }
        }]
    },
    resolve: {
        extensions: ['', '.js', '.jsx']
    },
    devtool: 'source-map',
};

module.exports = config;