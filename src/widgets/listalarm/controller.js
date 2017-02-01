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
    name: 'ListAlarmWidget',
    after: ['TimeWindowUtils', 'DataUtils', 'WidgetFactory', 'UserconfigurationMixin', 'RinfopopMixin', 'SchemasLoader'],
    initialize: function(container, application) {
		    var timeWindowUtils = container.lookupFactory('utility:timewindow'),
            dataUtils = container.lookupFactory('utility:data'),
			      WidgetFactory = container.lookupFactory('factory:widget'),
			      UserConfigurationMixin = container.lookupFactory('mixin:userconfiguration');
				  // RinfopopMixin = container.lookupFactory('mixin:rinfopop');

        var get = Ember.get,
            set = Ember.set,
            isNone = Ember.isNone;

        // load the viewMixin
        var listOptions = {
            mixins: [
                UserConfigurationMixin,
				// RinfopopMixin
            ]
        };

        /**
         * This widget allows to display alarms, with action possible on them.
         *
         * @memberOf canopsis.frontend.brick-listalarm
         * @mixes UserConfigurationMixin
         * @class WidgetListAlarm
         * @widget listalarm
         */
        var widget = WidgetFactory('listalarm',{

            viewMixins: [
                ],

            searchText: '',
            isValidSearchText: true,
            

            /**
             * Create the widget and set widget params into Ember vars
             * @method init
             */
            init: function() {
                this._super.apply(this, arguments);
				        this.fetchAlarms();
                // this.valideExpression();

				        set(this, 'store', DS.Store.extend({
                    container: get(this, 'container')
                }));
                this.showParams();
                this.setFields();
                this.loadRadioButtonView();                
                this.loadTemplates(this.get('model.popup'));
            },

            loadRadioButtonView: function () {
                view = Ember.View.extend({
                    tagName : "input",
                    type : "radio",
                    attributeBindings : [ "name", "type", "value", "checked:checked:" ],
                    click : function() {
                        console.error(this);
                        this.set("selection", this.$().val())
                    },
                    checked : function() {
                        return this.get("value") == this.get("selection");   
                    }.property()
                });
                try {
                  if (!Ember.RadioButton) {
                    Ember.RadioButton = view;
                  }
                } catch (err) {

                }
            },

            loadTemplates: function (templates) {
                Ember.columnTemplates = templates.map(function (obj) {
                  return {
                    columnName: obj.column,
                    columnTemplate: Ember.View.extend({
                      template: Ember.HTMLBars.compile(obj.template)
                    })                    
                  }
                })
            },

            showParams: function () {
                var controller = this;
                var params = ["popup", "title"];
                console.error("brick's parameters");
                params.forEach(function(param) {
                    console.error(param + ': ' + controller.get('model.' + param));
                });
                console.error("default_sort_column: " + controller.get('model.default_sort_column.property') + "-" + controller.get('model.default_sort_column.direction'));
                console.error("columnts: " + controller.get('model.columns').join(' ')),
                console.error("alarms_state_filter: " + controller.get('model.alarms_state_filter.state'))
                
            },

            /**
             * Set the reload to true in order to redraw events
             * extend the native refreshContent method
             * @method refreshContent
             */
            refreshContent: function () {
				          // Not implemented because backend too long, feature not useful for this widget
            },

            /**
             * Get the Alarms from the backend using the adapter
             * @method fetchAlarms
             */
            fetchAlarms: function(params) {
              var controller = this;
              var iParams = params || {};
              var filterState = this.get('model.alarms_state_filter.state') || 'opened';

              var query = {
                tstart: iParams['tstart'] || 0,
								tstop: iParams['tstop'] || 0,
								sort_key: iParams['sort_key'] || this.get('model.default_sort_column.property'),
           			sort_dir: iParams['sort_dir'] || this.get('model.default_sort_column.direction'),
                search: iParams['search'] || '',
                opened: filterState == 'opened',
                resolved: filterState == 'resolved'
							};

              var adapter = dataUtils.getEmberApplicationSingleton().__container__.lookup('adapter:alerts');
            	adapter.findQuery('alerts', query).then(function (result) {
                    // onfullfillment
					          var alerts = get(result, 'data');
                    controller.setAlarmsForShow(alerts[0]['alarms']);

                    console.error('alerts::', alerts);
              }, function (reason) {
                    // onrejection
                    // console.error('ERROR in the adapter: ', reason);
              });
            },

            /**
             * Get the Alarms from the backend using the adapter
             * @method valideExpression
             */
            isValidExpression: function (expression) {
              var controller = this;

              var query = {
                expression: expression
              };

              var rs = false;

              var adapter = dataUtils.getEmberApplicationSingleton().__container__.lookup('adapter:alertexpression');
            	adapter.findQuery('alertexpression', query).then(function (result) {
                    // onfullfillment
					          var result = get(result, 'data');
                    console.error('alertexpression result', result);
                    controller.set('isValidSearchText', result[0]);
                    if (result[0]) {
                      var params = {};

                      params['search'] = expression;                      
                      
                      controller.fetchAlarms(params);
                    }
                    
                    // rs = result[0];
              }, function (reason) {
                    // onrejection
                    // rs = false;
                    console.error('ERROR in the adapter: ', reason);
              });
              // return rs;              
            },

            setFields: function () {
              this.set('fields', this.parseFields(get(this, 'model.columns')));              
            },

            setAlarmsForShow: function (alarms) {
              var fields = get(this, 'fields');
              var controller = this;
              var alarmsArr = alarms.map(function(alarm) {
                var newAlarm = {};
                fields.forEach(function(field) {
                  newAlarm[field.name] = get(Ember.Object.create(alarm), 'v.' + field.getValue)
                })
                return newAlarm;
              });

              this.set('alarms', alarmsArr);
            },

						parseFields: function (columns) {
							var nestedObjects = ['state', 'status'];
							var fields = [];
							var sortColumn = this.get('model.default_sort_column.property');
							var order = this.get('model.default_sort_column.direction');
							

							fields = columns.map(function(column) {
								var obj = {};

								obj['name'] = column;

								obj['isSortable'] = column == sortColumn;
								obj['isASC'] = order == 'ASC';

								if (nestedObjects.includes(column)) {
									obj['getValue'] = column + '.val';
								} else {
									obj['getValue'] = column;
								}
								return obj;
							});

							return fields;
						},

            sortColumn: function() {
              var column = get(this, 'fields').findBy('name', get(this, 'controller.default_sort_column.property'));
              if (!column) {
                column = get(this, 'fields.firstObject');
                column['isSortable'] = true;
                column['isASC'] = get(this, 'controller.default_sort_column.property');
                console.error('the column "' + get(this, 'controller.default_sort_column.property') + '" was not found.');
                return column;
              }
              return column;
            }.property('controller.default_sort_column.property', 'fields.[]'),



            actions: {
              updateSortField: function (field) {
                var params = {};

                params['sort_key'] = field.name;
                params['sort_dir'] = field.isASC ? 'ASC' : 'DESC';
                
                this.fetchAlarms(params);
              },
              
              search: function (text) {
                console.error('search', text);
                // console.error(this.isValidExpression(text));
                this.isValidExpression(text);
                  // console.error('request for search')
                // } else {
                  // this.set('isValidSearchText', false)
                // }
              }
            }

        }, listOptions);

        application.register('widget:listalarm', widget);
    }
});
