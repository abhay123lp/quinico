/*

Copyright 2013 - Tom Alessi

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

*/

// Update a select field with a new list.
// Don't encode the resultant items
function updateDropdown(selectedOption,formName,selectName,input_array) {

   var option = document.getElementById(selectedOption).value;

   // The select menu to modify, and its parent form, to modify
   var select_menu = document.forms[formName].elements[selectName];

   // Remove all existing options from the select menu
   select_menu.options.length = 0;

   var data = window[input_array];

   for (i=0; i<data[option].length; i++) {

      // Setup the dropdown
      select_menu.options[select_menu.options.length] = new Option(data[option][i],data[option][i]);
   }
}


// Update a select field with a new list.
// Encode the resultant items
function updateDropdownEncode(selectedOption,formName,selectName,input_array) {

   var option = document.getElementById(selectedOption).value;

   // The select menu to modify, and its parent form, to modify
   var select_menu = document.forms[formName].elements[selectName];

   // Remove all existing options from the select menu
   select_menu.options.length = 0;

   var data = window[input_array];

   for (i=0; i<data[option].length; i++) {

      // Encode item
      var encoded_item = encodeURIComponent(data[option][i])

      // Setup the dropdown
      select_menu.options[select_menu.options.length] = new Option(data[option][i],encoded_item);
   }
}


// URL encode a select value after a form submit
function encodeValues(formName,selectName) {

   element = document.getElementById(selectName).options[document.getElementById(selectName).selectedIndex].value
   alert(element);
   var encodedElement = encodeURIComponent(element);
   alert(encodedElement);
   document.getElementById(selectName).options[document.getElementById(selectName).selectedIndex].value = encodedElement;
   }


function getJSONData(u) {

   var request = $.ajax({
       type: "GET",
       url: u,
       dataType: 'json',
       async: false
   }).responseText;

   return request;
}


function getHTMLData(u) {

   var request = $.ajax({
       type: "GET",
       url: u,
       dataType: 'html',
       async: false
   }).responseText;

   return request;
}


function switchGraph(u,slot) {

   var request = getJSONData(u);

   // Create our data table out of JSON data loaded from the server.
   // We need to create a JSON object first and then obtain the data portion
   var data = new google.visualization.DataTable($.parseJSON(request)['data']);

   var chart = new google.visualization.LineChart(document.getElementById(slot));
   chart.draw(data,$.parseJSON(request)['options']);

}


function switchPie(u,slot) {

   var request = getJSONData(u);

   // Create our data table out of JSON data loaded from the server.
   // We need to create a JSON object first and then obtain the data portion
   var data = new google.visualization.DataTable($.parseJSON(request)['data']);

   var chart = new google.visualization.PieChart(document.getElementById(slot));
   chart.draw(data,$.parseJSON(request)['options']);

}


function switchHTML(u,slot) {

   // Grab the HTML data
   var request = getHTMLData(u);

   // Set the DIV contents
   document.getElementById(slot).innerHTML = request;
}


function switchImage(u,slot,w,h) {

   // Set the DIV contents
   img = '<img src=\"' + u + '\" width=\"' + w + '\" height=\"' + h + '\">'
   document.getElementById(slot).innerHTML = img
}


// Change an image from Quinico
function switchQImage(img_url,frame_id) {
   document.getElementById(frame_id).src = img_url;
}


function changeElement(action,divName,fieldName,size) {

   var div = document.getElementById(divName);

   // Obtain all of the input fields in the div
   var inputs = div.getElementsByTagName("input");
   var last_item = inputs.length - 1;
   var last = inputs[last_item].id;

   if (action == 'add') {
      var count = Number(last.split("_")[1]) + 1;
      var input = document.createElement('input');
      var br = document.createElement('br');

      input.id = fieldName + "_" + count;
      br.id = fieldName + "_" + 'br_' + count;

      input.name = fieldName;
      br.name = fieldName + 'br_';

      input.type = "text";
      input.className = "dash_url";
      input.size = size;
      div.appendChild(input);
      div.appendChild(br);
   } else {
      var count = Number(last.split("_")[1]);

      // If there is only one textfield, quit
      if (count == 1) {return;}
    
      // Remove the field
      var field_name = fieldName + "_" + count;
      var input = document.getElementById(field_name);
      div.removeChild(input);

      // Remove the break
      var br_name = fieldName + "_" + 'br_' + count;
      var br = document.getElementById(br_name);
      div.removeChild(br);

   }
}


// Hide/Show an element
function hide_show(element) {

   if (document.getElementById(element).style.display == 'none') {
      document.getElementById(element).style.display = '';
   } else {
      document.getElementById(element).style.display = 'none';
   }
}

// Hide/Show an element using an image plus/minus
function hide_show_img(div,img) {
   if (document.getElementById(div).style.display == 'none') {
      document.getElementById(div).style.display = '';
      document.getElementById(img).src = '/html/images/minus.gif';
   } else {
      document.getElementById(div).style.display = 'none';
      document.getElementById(img).src = '/html/images/plus.gif';
   }
}


