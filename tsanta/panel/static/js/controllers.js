function BaseCtrl($scope, $timeout, $http, $location) {

    $scope.app_version = tsanta.version;
    $scope.pagename = '';

    $scope.status_message = '';
    $scope.solved_statuses = {
        '-1': 'hide',
        '0': 'glyphicon glyphicon-remove red',
        '1': 'glyphicon glyphicon-ok green',
    };

    $scope.set_pagename = function(name) {
        $scope.pagename = name;
    };

    $scope.say = function(text) {

        $scope.status_message = text;

        $timeout(function() {
            $scope.status_message = '';
        }, 5 * 1000);
    };

    $scope.say_error = function(text) {

        text = text || 'Произошла ошибка';

        $scope.status_message = text;

        $timeout(function() {
            $scope.status_message = '';
        }, 10 * 1000);
    };

    $scope.errorHandler = function(response) {

        switch ( response.status ) {
            case 404:
                $scope.say_error('Ресурс не найден');
                break;
            case 403:
                $scope.say_error('У вас нет доступа к запрашиваемому ресурсу');
                break;
            default:
                $scope.say_error();
                break;
        }
    };

    $scope.go = function(path) {
        $location.path(path);
    };

    $scope.load_group_list = function(prefix, callback) {
        prefix = prefix || '';

        $http.get(tsanta.api + '/groups?q=' + prefix)
        .then(function(response) {
            if ( response.status === 200 ) {
                if ( callback !== undefined ) {
                    callback(response.data);
                }
            }
        }, $scope.errorHandler);
    }
}


function GroupsCtrl($scope, $http) {

    $scope.set_pagename('Группы');

    $scope.groups = {
        items: [],
        filter_text: '',
        filter: function() {
            $scope.load_group_list(this.filter_text, function(response) {

                $scope.groups.items = response;

                if ( $scope.groups.filter_text ) {
                    var regexp = new RegExp('^' + $scope.groups.filter_text, 'i');

                    for ( var i = 0; i < response.length; ++i ) {
                        var match = response[i].short_name.match(regexp);

                        $scope.groups.items[i].short_name = response[i].short_name.replace(
                            match[0], '<mark>' + match[0] + '</mark>');
                    }
                }
            });
        }
    };

    $scope.load_group_list('', function(response) {
        $scope.groups.items = response;
    });
}


function GroupFormCtrl($scope, $http, $routeParams) {

    $scope.group_id = $routeParams.groupId;

    if ( $scope.group_id !== undefined ) {
        load_group($scope.group_id, function() {
            $scope.set_pagename($scope.name);
            $scope.current_slug = $scope.slug.text;
            $scope.slug.check();
        });
    } else {
        $scope.set_pagename('Новая группа');
    }

    $scope.name = '';
    $scope.alt_names = '';
    $scope.current_slug = undefined;
    $scope.event_lock = undefined;

    $scope.cities = {
        items: [],
        selected: undefined
    }

    $scope.slug = {
        text: '',
        is_ok: undefined,
        msg: undefined,
        check: function() {
            if ( this.text && this.text !== $scope.current_slug ) {
                $http.get(tsanta.api + '/groups/check_slug?q=' + this.text)
                .then(function(response) {
                    if ( response.status === 200 ) {
                        $scope.slug.is_ok = response.data.is_ok;

                        if ( !response.data.is_ok ) {
                            if ( response.data.is_exists ) {
                                $scope.slug.msg = 'Занят';
                            } else {
                                $scope.slug.msg = 'Некорректный';
                            }
                        } else {
                            $scope.slug.msg = 'OK';
                        }
                    }
                }, $scope.errorHandler);
            } else if ( $scope.current_slug !== undefined ) {
                this.msg = 'OK';
                this.is_ok = true;
            } else {
                this.msg = undefined;
            }
        }
    };

    $scope.submit_group = function() {
        var obj = {
            short_name: $scope.name,
            alt_names: $scope.alt_names,
            city: $scope.cities.selected,
            slug: $scope.slug.text
        }

        if ( $scope.group_id === undefined ) {
            $http.post(tsanta.api + '/groups', obj)
            .then(function(response) {
                if ( response.status === 200 ) {
                    $scope.say('Новая группа создана');
                    $scope.go('/groups');
                }
            }, $scope.errorHandler);
        } else {
            $http.put(tsanta.api + '/groups/' + $scope.group_id, obj)
            .then(function(response) {
                if ( response.status === 200 ) {
                    $scope.say('Данные группы обновлены');
                    $scope.go('/groups');
                }
            }, $scope.errorHandler);
        }
    };

    $scope.delete_group = function() {

        if (!confirm('Уверены, что хотите удалить группу?')) {
            return;
        }

        $http.delete(tsanta.api + '/groups/' + $scope.group_id)
        .then(function(response) {
            if ( response.status === 200 ) {
                $scope.say('Группы удалена');
                $scope.go('/groups');
            }
        }, $scope.errorHandler);
    };

    function load_group(group_id, callback) {
        $http.get(tsanta.api + '/groups/' + group_id)
        .then(function(response) {
            if ( response.status === 200 ) {
                $scope.name = response.data.short_name;
                $scope.alt_names = response.data.alt_names;
                $scope.slug.text = response.data.slug;
                $scope.cities.selected = response.data.city;
                $scope.event_lock = response.data.event_lock;
            }

            callback();
        }, $scope.errorHandler);
    }

    function load_cities(prefix) {
        prefix = prefix || '';

        $http.get(tsanta.api + '/cities?q=' + prefix)
        .then(function(response) {
            if ( response.status === 200 ) {
                $scope.cities.items = response.data;
            }
        }, $scope.errorHandler);
    };

    load_cities();
}


function EventsCtrl($scope, $http) {

    $scope.set_pagename('События');

    $scope.events = {
        items: []
    };
}

function EventsFormCtrl($scope, $http, $routeParams) {

    $scope.set_pagename('Новое событие');

    $scope.event_id = $routeParams.eventId;

    $scope.name;
    $scope.date_start;
    $scope.date_end;
    $scope.rules;
    $scope.process;

    $scope.groups = {
        items: []
    };

    $scope.free_questions = [];

    $scope.add_question = function() {
        $scope.free_questions.push({'text': ''});
    };

    $scope.delete_question = function(index) {
        var len = $scope.free_questions.length;

        for ( var i = index; i < len; ++i ) {
            $scope.free_questions[i] = $scope.free_questions[i + 1];
        }

        $scope.free_questions.splice(len - 1, 1);
    };

    $scope.load_group_list('', function(response) {
        var j = 0;
        for ( var i = 0; i < response.length; ++i ) {
            if ( response[i].event_lock === false ) {
                $scope.groups.items[j] = response[i];
                $scope.groups.items[j].checked = false;

                j++;
            }
        }
    });

    $scope.submit_event = function() {

    };
}


function ParticipantsCtrl($scope, $http) {
    $scope.set_pagename('Участники');
}

function NotificationsCtrl($scope, $http) {
    $scope.set_pagename('Рассылки');
}
