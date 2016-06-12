var gulp = require('gulp'),
    spawn = require('child_process').spawn,
    babel = require('gulp-babel'),
    sourcemaps = require('gulp-sourcemaps'),
    concat = require('gulp-concat'),
    uglify = require('gulp-uglify'),
    sass = require('gulp-sass'),
    server;

INCLUDE_JS = [
    'bower_components/react/react.js',
    'bower_components/react/react-dom.js',
    'bower_components/jquery/dist/jquery.min.js',
    'bower_components/babel/browser.min.js',
    'bower_components/socket.io-client/socket.io.js',
    'bower_components/bootstrap/dist/js/bootstrap.min.js',
];

INCLUDE_CSS = [
    // Library CSS goes here.
    // Bootstrap is included in the site theme as SCSS.
];

INCLUDE_FONTS = [
    'bower_components/bootstrap-sass/assets/fonts/**/*',
];

SOURCES = 'frontend/';
TARGET = 'target/';

gulp.task('libs/js', function () {
    var handler = function (err) {
        console.error('Error in library JS', err.toString());
    };
    return gulp.src(INCLUDE_JS)
        .pipe(sourcemaps.init())
        .pipe(concat('libs.js'))
        //.pipe(uglify())//.on('error', handler)
        .pipe(sourcemaps.write('.'))
        .pipe(gulp.dest(TARGET + 'js/'));
});
gulp.task('libs/css', function () {
    return gulp.src(INCLUDE_CSS)
        .pipe(concat('libs.css'))
        .pipe(gulp.dest(TARGET + 'css/'));
});
gulp.task('libs/fonts', function () {
    return gulp.src(INCLUDE_FONTS)
        .pipe(gulp.dest(TARGET + 'fonts/'));
});
gulp.task('site/js', function () {
    var handler = function (err) {
        console.error('Error in site JS', err.toString());
    };
    return gulp.src('frontend/**/*.jsx')
        .pipe(sourcemaps.init())
        .pipe(babel())//.on('error', handler)
        .pipe(concat('app.js'))
        .pipe(uglify())//.on('error', handler)
        .pipe(sourcemaps.write('.'))
        .pipe(gulp.dest(TARGET + 'js/'));
});
gulp.task('site/css', function () {
    return gulp.src('frontend/site.scss')
        .pipe(sass({
            includePaths: ['bower_components/bootstrap-sass/assets/stylesheets']
        }).on('error', sass.logError))
        .pipe(concat('app.css'))
        .pipe(gulp.dest(TARGET + 'css/'));
});
gulp.task('site/html', function () {
    return gulp.src('frontend/**/*.html')
        .pipe(gulp.dest(TARGET));
});

gulp.task('client', ['libs/js', 'libs/css', 'libs/fonts', 'site/js', 'site/css', 'site/html']);

// build client and server, watch sources, automatically restart server
gulp.task('watch', ['client'], function () {
    gulp.watch(['frontend/**/*.html'], ['site/html']);
    gulp.watch(['frontend/**/*.jsx'], ['site/js']);
    gulp.watch(['frontend/**/*.scss'], ['site/css']);
});

