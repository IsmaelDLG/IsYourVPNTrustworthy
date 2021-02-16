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

    name_array = document.URL.split(".");
    result.forEach((el, index) => {
        chrome.extension.sendRequest({type: "downloadPage", value: { text: el, name: md5(el)}});
    });
}

chrome.runtime.onMessage.addListener(
 function(request, sender) {
  console.log("content_script <<< " + request.value + "");
  });