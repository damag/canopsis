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

 require.config({
    paths: {
        'components/component-rrule': 'canopsis/canopsis-ui/src/components/rrule/template',
        'components/component-rruleeditor': 'canopsis/canopsis-ui/src/components/rruleeditor/template',
        'editor-rrule': 'canopsis/canopsis-ui/src/editors/editor-rrule',
        'editor-rruleeditor': 'canopsis/canopsis-ui/src/editors/editor-rruleeditor',
        'jobform': 'canopsis/canopsis-ui/src/forms/jobform/jobform',
        'renderer-rrule': 'canopsis/canopsis-ui/src/renderers/renderer-rrule',
        'application': 'canopsis/canopsis-ui/src/templates/application',

    }
});

 define([
    'canopsis/canopsis-ui/src/components/rrule/component',
    'ehbs!components/component-rrule',
    'canopsis/canopsis-ui/src/components/rruleeditor/component',
    'ehbs!components/component-rruleeditor',
    'ehbs!editor-rrule',
    'ehbs!editor-rruleeditor',
    'canopsis/canopsis-ui/src/forms/jobform/controller',
    'ehbs!jobform',
    'canopsis/canopsis-ui/src/forms/scheduleform/controller',
    'canopsis/canopsis-ui/src/forms/taskform/controller',
    'ehbs!renderer-rrule',
    'canopsis/canopsis-ui/src/reopens/routes/application',
    'canopsis/canopsis-ui/src/reopens/views/application',
    'link!canopsis/canopsis-ui/src/style.css',
    'ehbs!application',
    'canopsis/canopsis-ui/requirejs-modules/externals.conf',
    'canopsis/canopsis-ui/requirejs-modules/i18n'
], function (templates) {
    templates = $(templates).filter('script');
for (var i = 0, l = templates.length; i < l; i++) {
var tpl = $(templates[i]);
Ember.TEMPLATES[tpl.attr('data-template-name')] = Ember.Handlebars.compile(tpl.text());
};
});

