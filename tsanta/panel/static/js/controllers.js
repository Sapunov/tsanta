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
