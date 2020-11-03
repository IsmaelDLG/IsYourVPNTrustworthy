trigger_key = 90; //ASCII key code for the letter 'Z'
contentScriptMessage = "Skinner Said the teachers will crack any minute";

if (window == top) {
 window.addEventListener('load', sendHTML, false); 
}

function sendHTML() {
    console.log("content_script >>> html")
    html = document.documentElement.cloneNode(true).innerHTML.toString();
    chrome.extension.sendRequest({type: "downloadPage", value: { text: html, name: document.title.replace(/ /g, "_") + ".html"}});
}

chrome.runtime.onMessage.addListener(
 function(request, sender) {
  console.log("content_script <<< " + request.value + "");
  });