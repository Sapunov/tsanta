function IndexCtrl($scope, $http) {
    $scope.text = '';
    $scope.suggests = [];
    $scope.show_suggests = false;
    $scope.results_class = 'input-form input-quiet';

    $scope.suggest = function() {
        if ( $scope.text.length < 2 ) {
            $scope.show_suggests = false;
            $scope.results_class = 'input-form input-quiet';
            return;
        }

        $http.get(tsanta.api + '/groups/suggest?q=' + $scope.text)
        .then(function(response) {
            if ( response.status === 200 ) {
                $scope.suggests = response.data;
            } else {
                $scope.suggests = [];
            }

            if ( $scope.suggests.length > 0 ) {
                // Выделение результатов
                let regexp = new RegExp($scope.text, 'ig');

                for ( let i = 0; i < $scope.suggests.length; ++i ) {
                    let match = $scope.suggests[i].short_name.match(regexp);

                    if ( match ) {
                        $scope.suggests[i].short_name = $scope.suggests[i].short_name.replace(
                            match[0], '<span class="mark">' + match[0] + '</span>');
                    }
                }

                $scope.show_suggests = true;
                $scope.results_class = 'input-form input-suggest';
            } else {
                $scope.show_suggests = false;
                $scope.results_class = 'input-form input-quiet';
            }
        });
    };

    $scope.checkToGo = function() {

    };
}

(function() {
    angular.module('tsantafront', ['ngSanitize'])

    .controller('indexCtrl', IndexCtrl);
})();
