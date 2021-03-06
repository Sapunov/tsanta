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

    $scope.load_event_list = function(prefix, callback) {
        prefix = prefix || '';

        $http.get(tsanta.api + '/events?q=' + prefix)
        .then(function(response) {
            if ( response.status === 200 ) {
                if ( callback !== undefined ) {
                    callback(response.data);
                }
            }
        }, $scope.errorHandler);
    }

    $scope.load_event = function (event_id, callback) {
        $http.get(tsanta.api + '/events/' + event_id)
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
                if (response.q === $scope.groups.filter_text) {
                    $scope.groups.items = response.groups;

                    if ( $scope.groups.filter_text ) {
                        var regexp = new RegExp('^' + $scope.groups.filter_text, 'i');

                        for ( var i = 0; i < response.groups.length; ++i ) {
                            var match = response.groups[i].short_name.match(regexp);

                            if ( match ) {
                                $scope.groups.items[i].short_name = response.groups[i].short_name.replace(
                                    match[0], '<span class="mark">' + match[0] + '</span>');
                            }
                        }
                    }
                }
            });
        }
    };

    $scope.load_group_list('', function(response) {
        $scope.groups.items = response.groups;
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
    $scope.current_event = undefined;

    $scope.repr_name = {
        name: '',
        example: '',
        excuse: 'В',
        error_len: false,
        get: function() {
            return this.excuse.toLowerCase() + ' ' + (this.name || '');
        },
        set: function(value) {
            let parts = value.split(' ');

            if ( parts.length > 1 ) {
                switch (parts[0].toLowerCase()) {
                    case 'в':
                        this.excuse = 'В';
                        break;
                    case 'на':
                        this.excuse = 'На';
                        break;
                    default:
                        this.excuse = 'В'
                        break;
                }

                parts.splice(0, 1);
                this.name = parts.join(' ');
            } else {
                this.excuse = 'В';
                this.name = value;
            }

            this.make_example();
        },
        make_example: function() {
            this.example = this.name ? this.get() : '';
            if ( this.example.length > 13 ) {
                $scope.repr_name.error_len = true;
            } else {
                $scope.repr_name.error_len = false;
            }
        }
    };

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
            repr_name: $scope.repr_name.get(),
            city: $scope.cities.selected,
            slug: $scope.slug.text
        }

        if ( $scope.group_id === undefined ) {
            $http.post(tsanta.api + '/groups', obj)
            .then(function(response) {
                if ( response.status === 200 ) {
                    $scope.say('Группа ' + $scope.name + ' создана!');
                    $scope.go('/groups');
                }
            }, $scope.errorHandler);
        } else {
            $http.put(tsanta.api + '/groups/' + $scope.group_id, obj)
            .then(function(response) {
                if ( response.status === 200 ) {
                    $scope.say('Группа ' + $scope.name + '  обновлена');
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
                $scope.say('Группа ' + $scope.name + ' удалена');
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
                $scope.repr_name.set(response.data.repr_name);
                $scope.slug.text = response.data.slug;
                $scope.cities.selected = response.data.city;
                $scope.event_lock = response.data.event_lock;
                $scope.current_event = response.data.current_event;
            }

            callback();
        }, $scope.errorHandler);
    }

    function load_cities(prefix) {
        prefix = prefix || '';

        $http.get(tsanta.api + '/cities?limit=-1&q=' + prefix)
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

    $scope.load_event_list('', function(response) {
        $scope.events.items = response;
    });
}

function EventsFormCtrl($scope, $http, $routeParams) {

    $scope.event_id = $routeParams.eventId;

    $scope.data = {
        name: "",
        date_start: "",
        date_end: "",
        rules: "",
        process: "",
        groups: [],
        questions: []
    };

    $scope.groups = {
        items: [],
        item_ids: []
    };

    if ( $scope.event_id !== undefined ) {
        $scope.load_event($scope.event_id, function(response) {
            $scope.set_pagename(response.name);
            $scope.data.name = response.name;
            $scope.data.date_start = new Date(response.date_start);
            $scope.data.date_end = new Date(response.date_end);
            $scope.data.rules = response.rules;
            $scope.data.process = response.process;
            $scope.data.questions = response.questions;
            $scope.groups.item_ids = response.groups.map( function( item ) {return item.id;} );
        });
    } else {
        $scope.set_pagename('Новое событие');
    }

    $scope.load_group_list('', function(response) {
        var j = 0;
        for ( var i = 0; i < response.groups.length; ++i ) {

            if ( $scope.event_id !== undefined && $scope.groups.item_ids.indexOf(response.groups[i].id) != -1) {
                $scope.groups.items[j] = response.groups[i];
                $scope.groups.items[j].checked = true;

                j++;
            }
            else if ( response[i].event_lock === false ) {
                $scope.groups.items[j] = response.groups[i];
                $scope.groups.items[j].checked = false;

                j++;
            }
        }

        // Проверка на доступность групп
        if ( $scope.event_id === undefined && $scope.groups.items.length == 0 ) {
            $scope.say_error('Нет групп для создания события!\nСначала добавьте новую группу.');
            $scope.go('/groups');
        }
    });

    $scope.add_question = function() {
        // В данный момент api поддерживает только один тип вопросов - текст
        // type == 0 - текст
        $scope.data.questions.push({typed_content: '', type: 0});
    };

    $scope.delete_question = function(index) {
        var len = $scope.data.questions.length;

        for ( var i = index; i < len; ++i ) {
            $scope.data.questions[i] = $scope.data.questions[i + 1];
        }

        $scope.data.questions.splice(len - 1, 1);
    };

    $scope.no_checked_groups = function() {
        return extract_group_ids($scope.groups.items).length === 0;
    };

    $scope.submit_event = function() {
        $scope.data.groups = extract_group_ids($scope.groups.items);
        $scope.data.questions = extract_not_null_questions($scope.data.questions);

        // Создание нового события
        if ( $scope.event_id === undefined ) {
            $http.post(tsanta.api + '/events', $scope.data)
            .then(function(response) {
                if ( response.status === 200 ) {
                    $scope.say('Событие ' + $scope.data.name + ' создано!');
                    $scope.go('/events');
                }
            }, $scope.errorHandler);
        // Обновление события
        } else {
            $http.put(tsanta.api + '/events/' + $scope.event_id, $scope.data)
            .then(function(response) {
                if ( response.status === 200 ) {
                    $scope.say('Событие ' + $scope.data.name + ' изменено');
                    $scope.go('/events');
                }
            }, $scope.errorHandler);
        }
    };

    function extract_group_ids(group_items) {
        let ids = [];

        for ( let i = 0; i < group_items.length; ++i ) {
            if ( group_items[i].checked ) {
                ids.push({id: group_items[i].id});
            }
        }

        return ids;
    }

    function extract_not_null_questions(input_questions) {
        let questions = [];

        for ( let i = 0; i < input_questions.length; ++i ) {
            if ( input_questions[i].typed_content !== '') {
                questions.push(input_questions[i]);
            }
        }

        return questions;
    }
}

function EventsStatCtrl($scope, $http, $routeParams) {

    $scope.event_id = $routeParams.eventId;
    $scope.event = {};
    $scope.event_stat = {};

    $scope.load_event_stat = function() {
        $http.get(tsanta.api + '/events/' + $scope.event_id + '/stat?state=4')
        .then(function(response) {
            if ( response.status === 200 ) {
                $scope.event_stat = response.data;
            }
        }, $scope.errorHandler);
    }

    $scope.load_event_stat();

    $scope.load_event($scope.event_id, function(response) {
        $scope.event = response;
        $scope.set_pagename($scope.event.name);
    });
}

function EventsParticipantsCtrl($scope, $http, $routeParams) {

    $scope.event_id = $routeParams.eventId;
    $scope.event = {};
    $scope.participants = [];
    $scope.counters = [];
    $scope.filter_state = -1;

    let states = [
        'Зарегистрирован',
        'Подтверждение email отправлено',
        'Email подтвержден',
        'Подтверждение участия отправлено',
        'Участие подтверждено',
        'Назначен подопечный',
        'Подопечный отправлен'
    ];

    $scope.search = {
        text: '',
        search: function () {
            $scope.load_participants($scope.filter_state, this.text);
        }
    };

    $scope.load_participants = function (state, query) {
        if (state !== undefined) {
            state = state;
        } else {
            state = -1;
        }
        query = query || '';

        $http.get(tsanta.api + '/events/' + $scope.event_id + '/participants?q=' + query + '&state=' + state)
        .then(function(response) {
            if ( response.status === 200 ) {
                if (response.data.q === $scope.search.text) {
                    // Заменить коды статусов на названия
                    for (let i = 0; i < response.data.questionnaires.length; ++i) {
                        response.data.questionnaires[i].state_code = response.data.questionnaires[i].state;
                        response.data.questionnaires[i].state = states[response.data.questionnaires[i].state];
                    }
                    $scope.participants = response.data.questionnaires;

                    for (let i = 0; i < response.data.state_counters.length; ++i) {
                        response.data.state_counters[i].state_code = response.data.state_counters[i].state;
                        response.data.state_counters[i].state = states[response.data.state_counters[i].state];
                    }
                    $scope.counters = response.data.state_counters;
                }
            }
        }, $scope.errorHandler);
    };

    $scope.load_participants($scope.filter_state);

    $scope.filter_participants = function (state) {
        $scope.filter_state = state;
        $scope.load_participants($scope.filter_state, $scope.search.text);
    }

    $scope.update = function() {
        $scope.load_participants($scope.filter_state, $scope.search.text);
    };

    $scope.load_event($scope.event_id, function(response) {
        $scope.event = response;
        $scope.set_pagename($scope.event.name);
    });
}


function EventManageCtrl($scope, $http) {

    let assign_types = {
        'all': 'по всем анкетам',
        'city': 'в рамках городов',
        'group': 'в рамках групп'
    };

    function errorHandler(response) {
        if (response.status === 400) {
            $scope.say_error(response.data[0]);
        } else {
            $scope.errorHandler(response);
        }
    };

    $scope.assign_wards = function(assign_type) {
        $http.post(tsanta.api + '/events/' + $scope.event_id + '/assign?type=' + assign_type)
        .then(function(response) {
            if ( response.status === 200 ) {
                $scope.say('Подопечные распределены ' + assign_types[assign_type]);

                $scope.search.text = '';
                $scope.filter_state = -1;
                $scope.load_participants($scope.filter_state);
            }
        }, errorHandler);
    }

    $scope.send_confirms = function() {
        $http.post(tsanta.api + '/events/' + $scope.event_id + '/send_confirms')
        .then(function(response) {
            if ( response.status === 200 ) {
                $scope.say('Подтверждения об участии будут отправлены');

                $scope.search.text = '';
                $scope.filter_state = -1;
                $scope.load_participants($scope.filter_state);
            }
        }, $scope.errorHandler);
    }

    $scope.send_wards = function() {
        $http.post(tsanta.api + '/events/' + $scope.event_id + '/send_wards')
        .then(function(response) {
            if ( response.status === 200 ) {
                $scope.say('Подопечные будут отправлены');

                $scope.search.text = '';
                $scope.filter_state = -1;
                $scope.load_participants($scope.filter_state);
            }
        }, $scope.errorHandler);
    }
}
