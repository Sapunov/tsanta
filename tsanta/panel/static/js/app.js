(function() {
    angular.module('tsanta', ['ngRoute', 'ui.bootstrap', 'ngSanitize'])

    .controller('baseCtrl', BaseCtrl)
    .controller('groupsCtrl', GroupsCtrl)
    .controller('eventsCtrl', EventsCtrl)
    .controller('participantsCtrl', ParticipantsCtrl)
    .controller('notificationsCtrl', NotificationsCtrl)
    .controller('groupFormCtrl', GroupFormCtrl)
    .controller('eventsFormCtrl', EventsFormCtrl)
    .controller('eventsFlyCtrl', EventsFlyCtrl)

    // Configuring routes
    .config(['$locationProvider', '$routeProvider', '$httpProvider',
        function config($locationProvider, $routeProvider, $httpProvider) {
            $locationProvider.html5Mode(true);

            $httpProvider.defaults.xsrfCookieName = 'csrftoken';
            $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';

            $routeProvider

            .when('/', {
                redirectTo: '/groups'
            })

            .when('/groups', {
                templateUrl: '/static/partials/groups.html?v=' + tsanta.version,
                controller: 'groupsCtrl'
            })

            .when('/groups/new', {
                templateUrl: '/static/partials/groups_form.html?v=' + tsanta.version,
                controller: 'groupFormCtrl'
            })

            .when('/groups/:groupId/edit', {
                templateUrl: '/static/partials/groups_form.html?v=' + tsanta.version,
                controller: 'groupFormCtrl'
            })

            .when('/events', {
                templateUrl: '/static/partials/events.html?v=' + tsanta.version,
                controller: 'eventsCtrl'
            })

            .when('/events/new', {
                templateUrl: '/static/partials/events_form.html?v=' + tsanta.version,
                controller: 'eventsFormCtrl'
            })

            .when('/events/:eventId', {
                templateUrl: '/static/partials/events_fly.html?v=' + tsanta.version,
                controller: 'eventsFlyCtrl'
            })

            .when('/events/:eventId/edit', {
                templateUrl: '/static/partials/events_form.html?v=' + tsanta.version,
                controller: 'eventsFormCtrl'
            })

            .when('/participants', {
                templateUrl: '/static/partials/participants.html?v=' + tsanta.version,
                controller: 'participantsCtrl'
            })

            .when('/notifications', {
                templateUrl: '/static/partials/notifications.html?v=' + tsanta.version,
                controller: 'notificationsCtrl'
            })

            .when('/logout', {
                redirectTo: function() {
                    window.location = '/panel/logout';
                }
            })
        }
    ]);
})();
