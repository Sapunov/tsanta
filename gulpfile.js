var gulp = require('gulp');

var less = require('gulp-less');
var concat = require('gulp-concat');
var minify = require('gulp-minify');
var rename = require('gulp-rename');
var cleancss = require('gulp-clean-css');

// front
var front_base = 'tsanta/front/static/';
var front_less_directory = front_base + 'styles/less/';
var front_js_directory = front_base + 'js/';

// panel
var panel_base = 'tsanta/panel/static/';
var panel_js_directory = panel_base + 'js/';
var panel_less_directory = panel_base + 'less/';

// Tasks
gulp.task('front-less-standalone', function() {
	return gulp.src(front_less_directory + 'scaffolding.less')
		.pipe(less())
		.pipe(rename('styles.min.css'))
		.pipe(cleancss())
		.pipe(gulp.dest('tsanta/front/static/styles'));
});

gulp.task('front-less-mobile', function () {
	return gulp.src(front_less_directory + 'scaffolding.mobile.less')
		.pipe(less())
		.pipe(rename('styles.mobile.min.css'))
		.pipe(cleancss())
		.pipe(gulp.dest('tsanta/front/static/styles'));
});

gulp.task('front-js-minify', function() {
	return gulp.src(front_js_directory + '*.js')
		.pipe(minify({
			ext: {
				min: '.min.js'
			}
		}))
		.pipe(gulp.dest(front_js_directory));
});

gulp.task('front-less', ['front-less-standalone', 'front-less-mobile']);

gulp.task('front-less-watch', ['front-less'], function() {
	gulp.watch(front_less_directory + '**/*.less', ['front-less']);
});

gulp.task('panel-js-concat', function() {
	return gulp.src([
			panel_js_directory + 'common.js',
			panel_js_directory + 'controllers.js',
			panel_js_directory + 'app.js',
			panel_js_directory + 'directives.js'
		])
		.pipe(concat('app.js'))
		.pipe(gulp.dest(panel_base));
});

gulp.task('panel-less', function() {
	return gulp.src(panel_less_directory + 'scaffolding.less')
		.pipe(less())
		.pipe(rename('styles.min.css'))
		.pipe(cleancss())
		.pipe(gulp.dest(panel_base));
});


gulp.task('panel-watch', ['panel-js-concat', 'panel-less'], function() {
	gulp.watch(panel_js_directory + '*.js', ['panel-js-concat']);
	gulp.watch(panel_less_directory + '**/*.less', ['panel-less']);
});
