var page = require('webpage').create();
var system = require('system');
var fileName = system.args[1];
console.log(fileName)
page.open('http://localhost:8080/resources/ticket.html', function() {
  page.render(fileName);
  phantom.exit();
});