var page = require('webpage').create();
var system = require('system');

page.open('http://localhost:8080/resources/ticket.html', function() {
  var base64 = page.renderBase64('JPG');
  console.log(base64);
  phantom.exit();
});