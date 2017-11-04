
function BaseCtrl($scope, $timeout, $http, $interval) {

        $scope.app_version = tsanta.version;

        $scope.status_message = '';
        $scope.solved_statuses = {
            '-1': 'hide',
            '0': 'glyphicon glyphicon-remove red',
            '1': 'glyphicon glyphicon-ok green',
        }

        $scope.say = function(text) {

            $scope.status_message = text;

            $timeout(function() {
                $scope.status_message = '';
            }, 5 * 1000);
        }

        $scope.say_error = function(text) {

            text = text || 'Произошла ошибка';

            $scope.status_message = text;

            $timeout(function() {
                $scope.status_message = '';
            }, 10 * 1000);
        }

        $scope.errorHandler = function(response) {}
}


function HeaderCtrl($scope, $timeout) {}


function IndexCtrl($scope, $http) {}


function EventsCtrl($scope, $http) {

}

(function() {
    angular.module('tsanta', ['ngRoute'])

    .controller('baseCtrl', BaseCtrl)
    .controller('headerCtrl', HeaderCtrl)
    .controller('indexCtrl', IndexCtrl)
    .controller('eventsCtrl', EventsCtrl)

    // Configuring routes
    .config(['$locationProvider', '$routeProvider', '$httpProvider',
        function config($locationProvider, $routeProvider, $httpProvider) {
            $locationProvider.html5Mode(true);

            $httpProvider.defaults.xsrfCookieName = 'csrftoken';
            $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';

            $routeProvider

            .when('/', {
                templateUrl: '/static/partials/index.html?v=' + tsanta.version,
                controller: 'indexCtrl'
            })

            .when('/events', {
                templateUrl: '/static/partials/events.html?v=' + tsanta.version,
                controller: 'eventsCtrl'
            })
        }
    ]);
})();

angular.module('tsanta')

.directive('ngAutofocus', function($timeout) {
    return {
        link: function (scope, element, attrs) {
            scope.$watch(attrs.ngAutofocus, function(val) {
                if (angular.isDefined(val) && val) {
                    $timeout(function() { element[0].focus(); });
                }
            }, true);
        }
    };
});
