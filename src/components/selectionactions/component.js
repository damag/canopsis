Ember.Application.initializer({
    name: 'component-selectionactions',
    initialize: function(container, application) {
        var get = Ember.get,
            set = Ember.set,
            isNone = Ember.isNone;

        /**
         * This is the selectionactions component for the widget listalarm
         *
         * @class selectionactions component
         */
        var component = Ember.Component.extend({
            tagName: 'td',
            classNames: ['action-cell'],

            /**
             * @property actionsMap
             */
            actionsMap: Ember.A([
                {
                    class: '',
                    mixin_name: 'bulk_pbehavior',
                    caption: 'Apply PBehavior',
					rightName: "listalarm_pbehavior"
                },
                {
                    class: 'glyphicon glyphicon-ok',
                    mixin_name: 'fastack',
                    caption: 'Fast Ack',
					rightName: "listalarm_fastAck"
                },
                {
                    class: 'glyphicon glyphicon-saved',
                    mixin_name: 'ack',
                    caption: 'Ack',
					rightName: "listalarm_ack"
                },
                {
                    class: 'glyphicon glyphicon-ban-circle',
                    mixin_name: 'ackremove',
                    caption: 'Cancel ack',
					rightName: "listalarm_cancelAck"
                },
                {
                    class: 'glyphicon glyphicon-share-alt',
                    mixin_name: 'recovery',
                    caption: 'Restore alarm',
					rightName: 'listalarm_restoreAlarm',
                }
            ]),

			availableAction: [],

			canAction: function(rights, actionName){
				console.error("Rights", rights)
				console.error("ActionName", actionName)
				if (rights.hasOwnProperty(actionName)) {
					if (rights.get(actionName).checksum) {
						return true
					}
				}
				return false
			},


			genAvailableAction: function(rights) {
				var actions = new Array()
				for(i = 0; i < this.get("actionsMap").length; i++) {
					if (this.get("canAction")(rights, this.actionsMap[i]["rightName"])) {
						actions.push(this.actionsMap[i])
					}
				}
				this.set("availableAction", actions)
			},

            /**
             * @method init
             */
            init: function() {
                this._super();
				this.set("rights", this.get("_parentView._controller.login.rights"))
				console.error("Rights ", this.get("rights"))
				var func = this.get("genAvailableAction")
				console.error("genAvailable ", func)
				func(this.get("rights"))
            },

            actions: {
                /**
                 * @property sendAction
                 */
                sendAction: function (action) {
                    this.sendAction('action', action);
                }
            }

        });

        application.register('component:component-selectionactions', component);
    }
});
