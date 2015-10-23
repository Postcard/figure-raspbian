var page = require('webpage').create();
var system = require('system');
var args = system.args;
page.content = args[1]

var base64 = page.renderBase64('JPG');
console.log(base64);
phantom.exit();
