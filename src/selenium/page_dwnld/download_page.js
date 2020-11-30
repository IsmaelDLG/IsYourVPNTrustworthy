const MIMETYPE_HTML = "text/html";

chrome.extension.onRequest.addListener(function(request, sender) 
{
    console.log("background <<< " + request.type);
    
    customDownload(request.value);
    returnMessage("ok");
});

function returnMessage(messageToReturn)
{
  chrome.tabs.getSelected(null, function(tab) {
  chrome.tabs.sendMessage(tab.id, {value: messageToReturn});
 });
}

function customDownload(message) {
    var blob = new Blob([message.text], {type: MIMETYPE_HTML});
    var url = URL.createObjectURL(blob);
    chrome.downloads.download({
    url: url, // The object URL can be used as download URL
    filename: message.name //not too long, pls
    //...
    });
}