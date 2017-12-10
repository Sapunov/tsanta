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

    $scope.suggest = function(event) {
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

        if ( $scope.text === "" ) {
            $scope.suggests = [];
            $scope.hideSuggests();
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

                showSuggests();
            } else {
                $scope.hideSuggests();
            }
        });
    };
}

function ApplicationCtrl($scope, $http) {

    $scope.questions = {};

    let errors = {
        'validation': 'Заполните, пожалуйста, все поля.<br>Не забудьте, что email должен быть правильной формы, а номер телефона должен иметь минимум 10 цифр.',
        'submit': 'Произошла неизвестная ошибка. Пожалуйста, напишите об этом в <a href="https://vk.com/t_santa" target="blank">группе Тайного Санты</a>',
        'already_sent': 'Данные уже были отправлены. Если у вас есть подозрение, что они не дошли до Санты, напишите в группу <a href="https://vk.com/t_santa" target="blank">Тайного Санты</a>, разберемся.',
        'already_signed': 'Вы уже зарегистрированы на данное событие в этой группе. Если вы еще не регистрировались, напишите в группу <a href="https://vk.com/t_santa" target="blank">Тайного Санты</a>, разберемся.'
    };

    $scope.errorMsg = errors.validation;
    $scope.lock = false;

    $scope.data = {
        name: undefined,
        surname: undefined,
        sex: 'female',
        email: undefined,
        phone: undefined,
        social_network_link: undefined,
        questions: {},
        event: undefined,
        group: undefined
    };

    $scope.formError = false;

    $scope.suggest = function(element) {
        $scope.formError = false;
    }

    $scope.saveApplication = function(isInvalid, eventId, groupId) {
        if ( isInvalid ) {
            $scope.formError = true;
            return;
        }

        $scope.data.event = parseInt(eventId);
        $scope.data.group = parseInt(groupId);
        $scope.data.questions = prepareQuestions($scope.questions);

        if ( !$scope.lock ) {
            $scope.lock = true;

            $http.post(tsanta.api + '/events/submit', $scope.data)
            .then(function (response) {
                if ( response.status == 201 ) { // HTTP_201_CREATED
                    document.location = '/thanks';
                } else {
                    $scope.errorMsg = errors.submit;
                    $scope.formError = true;
                }
            // Обработка ошибок
            }, function(response) {
                switch (response.status) {
                    case 409:
                        $scope.errorMsg = errors.already_signed;
                        $scope.formError = true;
                        break;
                    default:
                        $scope.errorMsg = errors.submit;
                        $scope.formError = true;
                }
            });
        } else {
            $scope.errorMsg = errors.already_sent;
            $scope.formError = true;
        }
    }

    function prepareQuestions(questions) {
        let tmp = [];

        for (var key in questions) {
            if (questions.hasOwnProperty(key)) {
                // type == 0 - text
                // Пока так
                tmp.push({id: parseInt(key), typed_content: questions[key], type: 0});
            }
        }

        return tmp;
    }
}

function SliderCtrl($scope, $http) {
    $scope.images = [1, 2, 3, 4 , 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15];
}

// Angular application
(function() {
    angular.module('tsantafront', ['ngSanitize', 'ngRoute'])

    .controller('indexCtrl', IndexCtrl)
    .controller('applicationCtrl', ApplicationCtrl)
    .controller('sliderCtrl', SliderCtrl)

    .config(['$locationProvider', '$routeProvider', '$httpProvider',
        function config($locationProvider, $routeProvider, $httpProvider) {
            $httpProvider.defaults.xsrfCookieName = 'csrftoken';
            $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
        }
    ]);
})();
