/*
 * Copyright (c) 2015 "Capensis" [http://www.capensis.com]
 *
 * This file is part of Canopsis.
 *
 * Canopsis is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * Canopsis is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with Canopsis. If not, see <http://www.gnu.org/licenses/>.
 */

Ember.Application.initializer({
    name: 'WeatherWidget',
    after: 'WidgetFactory',
    initialize: function(container, application) {
        var WidgetFactory = container.lookupFactory('factory:widget');

        var get = Ember.get,
            set = Ember.set,
            isNone = Ember.isNone,
            Handlebars = window.Handlebars;

        /**
         * @widget weather
         */
        var widget = WidgetFactory('weather', {
            needs: ['application'],

            /**
             * @method init
             */
            init: function() {
                this._super();
                set(this, 'worst_state', undefined);
                set(this, 'sub_weather', []);
                /*this.fetchStates();*/
                console.log('Setting up weather widget : ' + get(this, 'config.title'));
            },

            actions: {
                goToInfo: function(element) {
                    console.log('goToInfo', element);
                    var transition = this.transitionToRoute('/userview/' + get(this, 'config.destination_view'));

                    var filter_pattern = get(this, 'model.filter_pattern');

                    // var weatherController = this;
                    // set(weatherController, 'controllers.application.isLoading', get(weatherController, 'controllers.application.isLoading') + 1);

                    transition.promise.then(function(routeInfos){
                        console.log('transition done', routeInfos);
                        var list = get(routeInfos, 'controller.content.containerwidget');
                        list = get(list, '_data.items')[0];
                        list = get(list, 'widget');
                        console.log(list);

                        console.log('filter_pattern', filter_pattern);

                        var template = filter_pattern;
                        var context = element;
                        var compiledFilterPattern = Handlebars.compile(template)(context);

                        console.log('compiledFilterPattern', compiledFilterPattern);

                        if(compiledFilterPattern !== '') {
                            if(!get(list, 'volatile')) {
                                set(list, 'volatile', {});
                            }

                            set(list, 'volatile.forced_filter', compiledFilterPattern);
                            set(list, 'rollbackable', true);
                            set(list, 'title', 'Info on events :', element.title);
                            set(list, 'dirtyMessage', element.title);
                        }
                    });
                }
            },

            /**
             * @property title
             * @description generate and refresh the title
             */
            title: function () {
                return get(this, 'config.title');
            }.property('config.title'),

            /**
             * @property icon
             */
            icon: function () {
                return this.class_icon(get(this, 'worst_state'));
            }.property('worst_state'),

            /**
             * @property class_icon
             * @description generate weather class depending on status
             */
            class_icon: function (status) {
                return [
                    'ion-ios7-sunny-outline',
                    'ion-ios7-cloudy-outline',
                    'ion-ios7-rainy-outline',
                    'ion-ios7-thunderstorm-outline',
                    'ion-checkmark-round'][status];
            } ,

            /**
             * @property background
             * @description generate and refresh background property for widget weather display
             */
            background: function () {
                return this.class_background(get(this, 'worst_state'));
            }.property('worst_state'),

            /**
             * @method class_background
             * @argument status
             * @description generate weather class depending on status
             * @return {string} the class to be applied to the div HTML element
             */
            class_background: function (status) {
                return [
                    'eventLikeGreen',
                    'eventLikeYellow',
                    'eventLikeOrange',
                    'eventLikeRed',
                    'eventLikePurple'][status];
            },

            /**
             * @method fetchStates
             */
            fetchStates: function () {
                var weatherWidget = this;
                var eventMetas = get(weatherWidget, 'config.event_selection'),
                    rks = [];

                console.log('rk information for weather', rks);


                if (!eventMetas || !eventMetas.length) {
                    console.warn('Widget weather ' + get(this, 'title') + ' No rk found, the widget may not be configured properly');
                    return;
                } else {
                    var rksLength = eventMetas.length,
                        rksLabels = {};
                    for (var i=0; i<rksLength; i++) {
                        var meta = eventMetas[i];
                        rksLabels[meta.rk] = meta.label;
                        rks.push(meta.rk);
                    }
                    set(weatherWidget,'rksLabels', rksLabels);
                }


                //TODO avoid using 0 as limit. A better practivce should be used, like limiting to 1000 and display a warning if payload.length > 1000
                var params = {
                    limit: 0,
                    ids: JSON.stringify(rks)
                };

                $.ajax({
                    url: '/rest/events',
                    data: params,
                    success: function(data) {
                        if (data.success) {
                            weatherWidget.computeWeather(data.data);
                        } else {
                            console.error('Unable to load event information for weather widget from API');
                        }
                        weatherWidget.trigger('refresh');
                        console.log(' + Weather content', get(weatherWidget, 'config.event_selection'));
                    }
                });
            },

            /**
             * @method computeWeather
             * @argument data
             */
            computeWeather: function (data) {
                console.group('computing weathers');
                var worst_state = 0,
                    sub_weathers = [],
                    ack_count = 0,
                    computedState = 0,
                    rksLabels = get(this, 'rksLabels');

                for (var i = 0, l = data.length; i < l; i++) {

                    var currentData = data[i];

                    console.log('subweather event', currentData);
                    var isAck = get(currentData, 'ack.isAck'),
                        ack = get(currentData, 'ack'),
                        resource = get(currentData, 'resource') || '',
                        event_type = get(currentData, 'event_type'),
                        component = get(currentData, 'component') || '',
                        rk = get(currentData, 'id');


                    //compute wether or not each event were acknowleged for this weather
                    if (isAck) {
                        console.log('one more ack count');
                        ack_count++;
                        computedState = 4;
                    } else {
                        console.log('normal ack count');
                        computedState = currentData.state;
                    }

                    //computing worst state for general weather display depending on ack state
                    if (currentData.state > worst_state) {
                        if(!ack || (ack && !isAck)) {
                            worst_state = currentData.state;
                        }
                    }


                    console.log('computedState', computedState);

                    //special selector event case
                    var component_label = component;
                    if (component_label === 'selector') {
                        component_label = '';
                    }

                    var label = component_label + ' ' + resource;
                    //define a label when option checked
                    if (get(this, 'use_labels')) {
                        //label is title by default is not set
                        label = rksLabels[rk] || label;
                    }

                    //building the data structure for sub parts of the weather
                    var subweatherDict = {
                        rk: rk,
                        event_type : event_type,
                        isSelector : event_type === 'selector',
                        component: component,
                        resource: resource,
                        title: label,
                        custom_class: this.class_background(computedState),
                        timestamp: get(currentData, 'timestamp'),
                        previous_state_change_ts: get(currentData, 'previous_state_change_ts')
                    };

                    if(event_type === 'selector') {
                        this.generateSelectorFilter(currentData, subweatherDict);
                    }

                    sub_weathers.pushObject(subweatherDict);

                }

                //when we got only one event, let display it s output separately
                console.log('The data lenght => ', data.length);
                if(data.length === 1) {
                    set(this, 'singleEvent', true);

                    var output = get(data[0], 'output');
                    if (!isNone(output) && output.length > 150) {
                        output = output.substr(0,150) + ' ...';
                    }
                    set(this, 'singleEventOutput', output);
                } else {
                    set(this, 'singleEvent', false);
                }

                if (ack_count === data.length) {
                    worst_state = 4;
                }

                console.log('worst_state', worst_state);

                console.log('weather content', {sub_weathers: sub_weathers, worst_state: worst_state});
                set(this, 'sub_weather', sub_weathers);
                set(this, 'worst_state', worst_state);

                console.groupEnd();

                this.trigger('refresh');
            },

            /**
             * @method generateSelectorFilter
             * @argument event
             * @argument subweatherDict
             */
            generateSelectorFilter: function (event, subweatherDict) {
                console.log('generateSelectorFilter', arguments);

                var params = {
                    limit: 1,
                    ids: JSON.stringify(get(event, 'selector_id'))
                };

                $.ajax({
                    url: '/rest/object',
                    data: params,
                    success: function(payload) {
                        if(payload.data.length >= 1) {
                            var filter = {'$or' : []};

                            var selectorObject = payload.data[0];
                            var include_ids = get(selectorObject, 'include_ids');
                            var exclude_ids = get(selectorObject, 'exclude_ids');
                            var mfilter = get(selectorObject, 'mfilter');

                            if(include_ids && include_ids.length) {
                                filter.$or.pushObject({ _id : { $in: include_ids}});
                            }

                            if(exclude_ids && exclude_ids.length) {
                                filter.$or.pushObject({ _id : { $nin: exclude_ids}});
                            }

                            if(mfilter) {
                                filter.$or.pushObject(JSON.parse(mfilter));
                            }

                            set(subweatherDict, 'selector_filter', JSON.stringify(filter));
                            console.log('selector filter', filter);
                        }
                    }
                });
            },

            /**
             * @method refreshContent
             */
            refreshContent: function () {
                this.fetchStates();
                this._super();
            }
        });

        application.register('widget:weather', widget);
    }
});
