!function(){Ember.JSONEditor=Ember.Namespace.create(),Ember.JSONEditor.VERSION="0.1.0",Ember.libraries.register("ember-jsoneditor",Ember.JSONEditor.VERSION)}(),function(){"use strict";Ember.JSONEditor.EditorComponent=Ember.Component.extend({tagName:"div",classNames:["jsoneditor-component"],_editor:void 0,editor:function(){var a=this;if(console.log("editor"),Ember.isEqual(a.get("_editor"),void 0)){var b=a.get("element");if(Ember.isEqual(b,void 0))return void 0;var c=a.get("options"),d=a.get("json"),e=new jsoneditor.JSONEditor(b,c,d);return a.set("_editor",e),e}return a.get("_editor")}.property("element","options","json"),json:{},options:function(){var a=this.getProperties(["mode","modes","_change","search","history","name","indentation","error"]);return a.change=a._change,delete a._change,a.component=this,a}.property("mode","modes","_change","search","history","name","indentation","error"),mode:"tree",modes:["tree","view","form","text","code"],change:function(){console.log("JSON Editor changed!")},error:function(a){console.error("An error occured: ",a)},_updating:!1,_change:function(){var a=this.component,b=a.get("editor"),c=b.get();a.set("_updating",!0),a.set("json",c),a.set("_updating",!1),a.change&&a.change()},search:!0,history:!0,name:"JSONEditor",indentation:4,editorDidChange:function(){var a=this;a.get("editor")}.observes("editor").on("didInsertElement"),jsonDidChange:function(){var a=this;if(Ember.isEqual(a.get("_updating"),!1)){var b=a.get("editor"),c=a.get("json");b.set(c)}}.observes("json"),modeDidChange:function(){var a=this,b=a.get("editor"),c=a.get("mode");b.setMode(c)}.observes("mode"),nameDidChange:function(){var a=this,b=a.get("editor"),c=a.get("name");b.setName(c)}.observes("name")}),Ember.Handlebars.helper("json-editor",Ember.JSONEditor.EditorComponent)}();