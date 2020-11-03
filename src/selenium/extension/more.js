/*
 * Copyright 2010-2020 Gildas Lormeau
 * contact : gildas.lormeau <at> gmail.com
 * 
 * This file is part of SingleFile.
 *
 *   The code in this file is free software: you can redistribute it and/or 
 *   modify it under the terms of the GNU Affero General Public License 
 *   (GNU AGPL) as published by the Free Software Foundation, either version 3
 *   of the License, or (at your option) any later version.
 * 
 *   The code in this file is distributed in the hope that it will be useful, 
 *   but WITHOUT ANY WARRANTY; without even the implied warranty of 
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero 
 *   General Public License for more details.
 *
 *   As additional permission under GNU AGPL version 3 section 7, you may 
 *   distribute UNMODIFIED VERSIONS OF THIS file without the copy of the GNU 
 *   AGPL normally required by section 4, provided you include this license 
 *   notice and a URL through which recipients can access the Corresponding 
 *   Source.
 */

/* global browser, singlefile, Blob, URL, document, GDrive, woleet */

// See https://github.com/mdn/webextensions-examples/issues/194
/*
#194 (comment) is correct,
however, now days, newer Firefox versions will always have both chrome and browser available. Older versions that supports web-extension (versions 42 to 53) won't, since the support was introduces gradually, for this case there is a small line to include on the top of the JS file(s) you're using:

"use strict";
var API = chrome || browser;
then use API instead of chrome or browser to play nice with both browsers,
or include Mozilla's https://github.com/mozilla/webextension-polyfill that will wrap everything nicely in a cross-browser compatible promise-structure.
*/

const partialContents = new Map();
const MIMETYPE_HTML = "text/html";
const STATE_DOWNLOAD_COMPLETE = "complete";
const STATE_DOWNLOAD_INTERRUPTED = "interrupted";
const STATE_ERROR_CANCELED_CHROMIUM = "USER_CANCELED";
const ERROR_DOWNLOAD_CANCELED_GECKO = "canceled";
const ERROR_CONFLICT_ACTION_GECKO = "conflictaction prompt not yet implemented";
const ERROR_INCOGNITO_GECKO = "'incognito'";
const ERROR_INCOGNITO_GECKO_ALT = "\"incognito\"";
const ERROR_INVALID_FILENAME_GECKO = "illegal characters";
const ERROR_INVALID_FILENAME_CHROMIUM = "invalid filename";
const CLIENT_ID = "207618107333-bktohpfmdfnv5hfavi1ll18h74gqi27v.apps.googleusercontent.com";
const SCOPES = ["https://www.googleapis.com/auth/drive.file"];
const CONFLICT_ACTION_SKIP = "skip";
const CONFLICT_ACTION_UNIQUIFY = "uniquify";
const REGEXP_ESCAPE = /([{}()^$&.*?/+|[\\\\]|\]|-)/g;

async function downloadBlob(blob, incognito, message) {
    try {
        message.url = URL.createObjectURL(blob);
        await downloadPage(message, {
            confirmFilename: message.confirmFilename,
            incognito,
            filenameConflictAction: message.filenameConflictAction,
            filenameReplacementCharacter: message.filenameReplacementCharacter,
            includeInfobar: message.includeInfobar
        });
    } catch (error) {
        if (!error.message || error.message != "upload_cancelled") {
            console.error(error); // eslint-disable-line no-console
        }
    } finally {
        if (message.url) {
            URL.revokeObjectURL(message.url);
        }
    }
}

function getRegExp(string) {
    return string.replace(REGEXP_ESCAPE, "\\$1");
}

async function downloadPage(pageData, options) {
    const filenameConflictAction = options.filenameConflictAction;
    let skipped;
    if (filenameConflictAction == CONFLICT_ACTION_SKIP) {
        const downloadItems = await API.downloads.search({
            filenameRegex: "(\\\\|/)" + getRegExp(pageData.filename) + "$",
            exists: true
        });
        if (downloadItems.length) {
            skipped = true;
        } else {
            options.filenameConflictAction = CONFLICT_ACTION_UNIQUIFY;
        }
    }
    if (!skipped) {
        const downloadInfo = {
            url: pageData.url,
            saveAs: options.confirmFilename,
            filename: pageData.filename,
            conflictAction: options.filenameConflictAction
        };
        if (options.incognito) {
            downloadInfo.incognito = true;
        }
        const downloadData = await download(downloadInfo, options.filenameReplacementCharacter);
    }
}

async function download(downloadInfo, replacementCharacter) {
    let downloadId;
    try {
        downloadId = await API.downloads.download(downloadInfo);
    } catch (error) {
        if (error.message) {
            const errorMessage = error.message.toLowerCase();
            const invalidFilename = errorMessage.includes(ERROR_INVALID_FILENAME_GECKO) || errorMessage.includes(ERROR_INVALID_FILENAME_CHROMIUM);
            if (invalidFilename && downloadInfo.filename.startsWith(".")) {
                downloadInfo.filename = replacementCharacter + downloadInfo.filename;
                return download(downloadInfo, replacementCharacter);
            } else if (invalidFilename && downloadInfo.filename.includes(",")) {
                downloadInfo.filename = downloadInfo.filename.replace(/,/g, replacementCharacter);
                return download(downloadInfo, replacementCharacter);
            } else if (invalidFilename && !downloadInfo.filename.match(/^[\x00-\x7F]+$/)) { // eslint-disable-line  no-control-regex
                downloadInfo.filename = downloadInfo.filename.replace(/[^\x00-\x7F]+/g, replacementCharacter); // eslint-disable-line  no-control-regex
                return download(downloadInfo, replacementCharacter);
            } else if ((errorMessage.includes(ERROR_INCOGNITO_GECKO) || errorMessage.includes(ERROR_INCOGNITO_GECKO_ALT)) && downloadInfo.incognito) {
                delete downloadInfo.incognito;
                return download(downloadInfo, replacementCharacter);
            } else if (errorMessage == ERROR_CONFLICT_ACTION_GECKO && downloadInfo.conflictAction) {
                delete downloadInfo.conflictAction;
                return download(downloadInfo, replacementCharacter);
            } else if (errorMessage.includes(ERROR_DOWNLOAD_CANCELED_GECKO)) {
                return {};
            } else {
                throw error;
            }
        } else {
            throw error;
        }
    }
    return new Promise((resolve, reject) => {
        API.downloads.onChanged.addListener(onChanged);

        function onChanged(event) {
            if (event.id == downloadId && event.state) {
                if (event.state.current == STATE_DOWNLOAD_COMPLETE) {
                    API.downloads.search({ id: downloadId })
                        .then(downloadItems => resolve({ filename: downloadItems[0] && downloadItems[0].filename }))
                        .catch(() => resolve({}));
                    API.downloads.onChanged.removeListener(onChanged);
                }
                if (event.state.current == STATE_DOWNLOAD_INTERRUPTED) {
                    if (event.error && event.error.current == STATE_ERROR_CANCELED_CHROMIUM) {
                        resolve({});
                    } else {
                        reject(new Error(event.state.current));
                    }
                    API.downloads.onChanged.removeListener(onChanged);
                }
            }
        }
    });
}

function saveToClipboard(pageData) {
    const command = "copy";
    document.addEventListener(command, listener);
    document.execCommand(command);
    document.removeEventListener(command, listener);

    function listener(event) {
        event.clipboardData.setData(MIMETYPE_HTML, pageData.content);
        event.clipboardData.setData("text/plain", pageData.content);
        event.preventDefault();
    }
}

var message = {}
message.filename = Date.now()

downloadBlob(new Blob([document.documentElement.innerHTML], { type: MIMETYPE_HTML }), false, message);
