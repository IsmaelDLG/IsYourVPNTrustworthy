if (window == top) {
 window.addEventListener('load', sendHTML, false); 
}

function sendHTML() {
    scripts = document.getElementsByTagName("script");
    iframes = document.getElementsByTagName("iframe");

    // html = document.documentElement.cloneNode(true).innerHTML.toString();
    chrome.extension.sendRequest({type: "downloadPage", value: { text: html, name: document.title.replace(/ /g, "_").substr(0,10) + ".html"}});
}

chrome.runtime.onMessage.addListener(
 function(request, sender) {
  console.log("content_script <<< " + request.value + "");
  });