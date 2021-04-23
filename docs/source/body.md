
# Progress

## 01/10/2020

First thing I will do Is download different VPN services, install them and download the pages I get to look for JS Injection.

Used VPNs:
- Full VPNS:
    - ProtonVPN
    - Windscribe
- Browser VPN:
    - Browsec WPN
    - Hola Free VPN
    - Hotspot Shield Free
    - Hoxx VPN
    - SetupVPN
    - Surshark VPN
    - Touch VPN
    - uVPN
    - VPN
    - VPN Free
    - VPN Master
    - ZenMate Free

## 15/10/2020

Built a crawler (js_crawlers) that are able to download all the wepages they go through. They crawl the top 500 webpages. This works with the full-vpn setup (windscribe, protonvpn), but not with the in-browser vpn...

I need to crawl webpages usinng the browser itself.

## 01/11/2020

Built a crawler usinng selenium that, along with a chrome-addon, can crawl every webpage it goes through and download it. Then, a postscript reads the webpage and looks for iframes and scripts that may be used to track users.

Still strungling with vpn-addons, for I can't find a way to download them.

## 16/11/2020

Found a way to download the addons! If you go to a certain addon, and right-click the button "add to firefox" and select "Save Link As..." it will download the .xpi file with the addon.

Now I have to add this addon to my selenium crawler and activate it's services.