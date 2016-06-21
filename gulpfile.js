var gulp = require('gulp'),
    spawn = require('child_process').spawn,
    babel = require('gulp-babel'),
    sourcemaps = require('gulp-sourcemaps'),
    concat = require('gulp-concat'),
    uglify = require('gulp-uglify'),
    sass = require('gulp-sass'),
    webpack = require('webpack-stream'),
    server;

var env = 'development';
var webpackConfig = require('./webpack.config.js');

INCLUDE_CSS = [
    // Library CSS goes here.
    // Bootstrap is included in the site theme as SCSS.
];

INCLUDE_FONTS = [
    'node_modules/bootstrap-sass/assets/fonts/**/*',
];

SOURCES = 'frontend/';
TARGET = 'target/';

// library static CSS
gulp.task('libs/css', function () {
    return gulp.src(INCLUDE_CSS)
        .pipe(concat('libs.css'))
        .pipe(gulp.dest(TARGET + 'css/'));
});
// library fonts
gulp.task('libs/fonts', function () {
    return gulp.src(INCLUDE_FONTS)
        .pipe(gulp.dest(TARGET + 'fonts/'));
});
// site JS/JSX
gulp.task('site/js', function () {
    var handler = function (err) {
        console.error('Error in site JS:', err.toString());
    };
    return gulp.src(SOURCES + 'site.jsx')
        .pipe(webpack(webpackConfig))
        .pipe(gulp.dest(TARGET + 'js/'));
});
// site SCSS (includes bootstrap)
gulp.task('site/css', function () {
    return gulp.src(SOURCES + 'site.scss')
        .pipe(sass({
            includePaths: ['node_modules/bootstrap-sass/assets/stylesheets']
        }).on('error', sass.logError))
        .pipe(concat('app.css'))
        .pipe(gulp.dest(TARGET + 'css/'));
});
// site HTML
gulp.task('site/html', function () {
    return gulp.src(SOURCES + '**/*.html')
        .pipe(gulp.dest(TARGET));
});

gulp.task('client', ['libs/css', 'libs/fonts', 'site/js', 'site/css', 'site/html']);

// build client, watch sources
gulp.task('watch', ['client'], function () {
    gulp.watch([SOURCES + '**/*.html'], ['site/html']);
    gulp.watch([SOURCES + '**/*.jsx'], ['site/js']);
    gulp.watch([SOURCES + '**/*.scss'], ['site/css']);
});
