function IndexCtrl($scope, $http) {
    $scope.text = '';
    $scope.suggests = [];
    $scope.show_suggests = false;
    $scope.results_class = 'input-form';
    $scope.is_mouse = false;

    $scope.tryToShowSuggests = function() {
        if ($scope.suggests.length > 0) {
            showSuggests();
        }
    };

    function showSuggests() {
        $scope.show_suggests = true;
        $scope.results_class = 'input-form input-suggest';
    }

    $scope.hideSuggests = function() {
        // Нельзя прятать подсказки, если фокус на каком-то элементе
        // и сделан он был мышкой
        if ( $scope.is_mouse ) {
            for ( let i = 0; i < $scope.suggests.length; ++i ) {
                if ( $scope.suggests[i].selected ) {
                    return;
                }
            }
        }
        $scope.show_suggests = false;
        $scope.results_class = 'input-form';
    }

    $scope.toggleSuggests = function(where) {
        if ( where == 'enter' ) {
            if ( $scope.suggests.length === 1 ) {
                document.location = '/' + $scope.suggests[0].slug;
            } else {
                for ( let i = 0; i < $scope.suggests.length; ++i ) {
                    if ( $scope.suggests[i].selected ) {
                        document.location = '/' + $scope.suggests[i].slug;
                    }
                }
            }
            return;
        }

        let current = where === 'up' ? $scope.suggests.length : -1;

        for ( let i = 0; i < $scope.suggests.length; ++i ) {
            if ( $scope.suggests[i].selected ) {
                current = i;
            }
        }

        if ( where == 'down' ) {
            $scope.selectSuggest((current + 1) % $scope.suggests.length);
        } else {
            $scope.selectSuggest((current + $scope.suggests.length - 1) % $scope.suggests.length);
        }
    }

    $scope.selectSuggest = function(index, is_mouse) {
        $scope.is_mouse = is_mouse || false;

        for ( let i = 0; i < $scope.suggests.length; ++i ) {
            if ( i === index ) {
                $scope.suggests[i].selected = true;
            } else {
                $scope.suggests[i].selected = false;
            }
        }
    }

    $scope.unselectSuggests = function() {
        for ( let i = 0; i < $scope.suggests.length; ++i ) {
            $scope.suggests[i].selected = false;
        }
    }

    $scope.suggest = function() {
        switch (event.keyCode) {
            case 13: // enter
                $scope.toggleSuggests('enter');
                return;
            case 38:
                $scope.toggleSuggests('up');
                return;
            case 40:
                $scope.toggleSuggests('down');
                return;
            default: break;
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

                showSuggests();
            } else {
                $scope.hideSuggests();
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
