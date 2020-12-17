if (window == top) {
 window.addEventListener('load', sendHTML, false); 
}

function sendHTML() {
    result = new Array()

    scripts = document.getElementsByTagName("script");

    Array.from(scripts).forEach((el, index) => {
        result.push(el.outerHTML);
    });

    iframes = document.getElementsByTagName("iframe");
    Array.from(iframes).forEach((el, index) => {
        result.push(el.outerHTML);
    });


    // html = document.documentElement.cloneNode(true).innerHTML.toString();
    chrome.extension.sendRequest({type: "downloadPage", value: { text: result, name: document.title.replace(/ /g, "_").substr(0,10) + ".html"}});
}

chrome.runtime.onMessage.addListener(
 function(request, sender) {
  console.log("content_script <<< " + request.value + "");
  });