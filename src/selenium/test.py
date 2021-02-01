from urllib.parse import urlparse

def get_network(log_entries):
    """ Reads the performance log entries and computes a network traffic dictionary based on the actual requests. """

    network_traffic = {}
    for log_entry in log_entries:
        message = json.loads(log_entry["message"])
        method = message["message"]["method"]
        params = message["message"]["params"]
        if method not in ["Network.requestWillBeSent", "Network.responseReceived", "Network.loadingFinished"]:
            continue
        if method != "Network.loadingFinished":
            request_id = params["requestId"]
            loader_id = params["loaderId"]
            if loader_id not in network_traffic:
                network_traffic[loader_id] = {"requests": {}, "encoded_data_length": 0}
            if request_id == loader_id:
                if "redirectResponse" in params:
                    network_traffic[loader_id]["encoded_data_length"] += params["redirectResponse"]["encodedDataLength"]
                if method == "Network.responseReceived":
                    network_traffic[loader_id]["type"] = params["type"]
                    network_traffic[loader_id]["url"] = params["response"]["url"]
                    network_traffic[loader_id]["remote_IP_address"] = None
                    if "remoteIPAddress" in params["response"].keys():
                        network_traffic[loader_id]["remote_IP_address"] = params["response"]["remoteIPAddress"]
                    network_traffic[loader_id]["encoded_data_length"] += params["response"]["encodedDataLength"]
                    network_traffic[loader_id]["headers"] = params["response"]["headers"]
                    network_traffic[loader_id]["status"] = params["response"]["status"]
                    network_traffic[loader_id]["security_state"] = params["response"]["securityState"]
                    network_traffic[loader_id]["mime_type"] = params["response"]["mimeType"]
                    if "via" in params["response"]["headers"]:
                        network_traffic[loader_id]["cached"] = True
            else:
                if request_id not in network_traffic[loader_id]["requests"]:
                    network_traffic[loader_id]["requests"][request_id] = {"encoded_data_length": 0}
                if "redirectResponse" in params:
                    network_traffic[loader_id]["requests"][request_id]["encoded_data_length"] += params["redirectResponse"]["encodedDataLength"]
                if method == "Network.responseReceived":
                    network_traffic[loader_id]["requests"][request_id]["type"] = params["type"]
                    network_traffic[loader_id]["requests"][request_id]["url"] = params["response"]["url"]
                    network_traffic[loader_id]["requests"][request_id]["remote_IP_address"] = None
                    if "remoteIPAddress" in params["response"].keys():
                        network_traffic[loader_id]["requests"][request_id]["remote_IP_address"] = params["response"]["remoteIPAddress"]
                    network_traffic[loader_id]["requests"][request_id]["encoded_data_length"] += params["response"]["encodedDataLength"]
                    network_traffic[loader_id]["requests"][request_id]["headers"] = params["response"]["headers"]
                    network_traffic[loader_id]["requests"][request_id]["status"] = params["response"]["status"]
                    network_traffic[loader_id]["requests"][request_id]["security_state"] = params["response"]["securityState"]
                    network_traffic[loader_id]["requests"][request_id]["mime_type"] = params["response"]["mimeType"]
                    if "via" in params["response"]["headers"]:
                        network_traffic[loader_id]["requests"][request_id]["cached"] = 1
        else:
            request_id = params["requestId"]
            encoded_data_length = params["encodedDataLength"]
            for loader_id in network_traffic:
                if request_id == loader_id:
                    network_traffic[loader_id]["encoded_data_length"] += encoded_data_length
                elif request_id in network_traffic[loader_id]["requests"]:
                    network_traffic[loader_id]["requests"][request_id]["encoded_data_length"] += encoded_data_length
    return network_traffic

def extract_components(url):
    """ Returns a dict with the URL components. """

    parsed = urlparse(url)
    components = {'scheme': parsed.scheme, 'netloc': parsed.netloc, 'path': parsed.path, 'params': parsed.params,
                  'query': parsed.query, 'fragment': parsed.fragment, 'username': parsed.username,
                  'password': parsed.password, 'hostname': parsed.hostname, 'port': parsed.port}
    return components

def download_file(url, destination, headers=None, verify=True):
    """ Downloads a file. """

    h = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:45.0) Gecko/20100101 Firefox/45.0'}
    if headers is not None:
        h.update(headers)

    resp = requests.get(url, stream=True, headers=h, timeout=(6, 27), verify=verify)
    for chunk in resp.iter_content(chunk_size=4096):
        if chunk:
            destination.write(chunk)

    destination.seek(0)
    return destination, resp.headers

def download_url(process, url, filename):
    """ Downloads the given url into the given filename. """

    with open(filename, 'wb') as f:
        try:
            f, headers = download_file(url=url, destination=f)
        except requests.exceptions.SSLError:
            try:
                requests.packages.urllib3.disable_warnings()
                f, headers = download_file(url=url, destination=f, verify=False)
            except Exception as e:
                logger.error("(proc. %s) Error #1: %s" % (process, str(e)))
                return False
        except UnicodeError as e:
            logger.error("(proc. %s) Error #2: Couldn't download url %s with error %s" % (process, url, str(e)))
            return False
        except Exception as e:
            logger.error("(proc. %s) Error #3: %s" % (process, str(e)))
            return False
    logger.debug("(proc. %s) Found external resource %s" % (process, url))
    return True

def manage_request(db, process, domain, request, plugin, temp_folder):
    """ Inserts the URL data if non-existent and downloads/beautifies if needed """

    t = utc_now()
    # Insert new URL info
    url = insert_url(db, request, t, t)
    if not url:
        return

    # Creates the relation between domain <-> url <-> plugin
    components = extract_components(request["url"])
    root_url = components['netloc'] + components['path']
    url_type = Connector(db, "type")
    url_type.load(url.values["type"])

    resource_id = None

    # Download resource in temp file if needed
    if url_type.values["download"]:
        os.makedirs(os.path.join(os.path.abspath("."), temp_folder), exist_ok=True)
        filename = os.path.join(temp_folder, domain.values["name"] + '.tmp')
        if download_url(process, url.values["url"], filename):
            hash_code = hash_file(filename)
            size = os.stat(filename).st_size

            # Compress the code
            with open(filename, 'rb') as f:
                code = f.read()
            compressed_code = zlib.compress(code)

            # Insert resource
            resource = Connector(db, "resource")
            if not resource.load(hash_code):
                resource.values["file"] = compressed_code
                resource.values["size"] = size
                resource.values["fuzzy_hash"] = lsh_file(filename)
                resource.values["insert_date"] = t
                resource.values["update_timestamp"] = t
                if not resource.save():
                    max = 30
                    # Wait until the other thread saves the file inside the database (or 30s max)
                    while not resource.load(hash_code) and max > 0:
                        max -= 1
                        time.sleep(1)
            resource_id = resource.values["id"]
            db.call("ComputeResourceType", values=[resource_id])
            db.call("ComputeResourcePopularityLevel", values=[resource_id])

            # Remove temp file
            os.remove(filename)

        if not resource_id:
            logger.error("(proc. %s) Error #4: Resource not correctly saved" % process)


    # Compute the url length (without the domain and path)
    query_length = 0
    if url.values["params"] is not None:
        query_length += len(url.values["params"])
    if url.values["query"] is not None:
        query_length += len(url.values["query"])
    if url.values["fragment"] is not None:
        query_length += len(url.values["fragment"])
    if url.values["username"] is not None:
        query_length += len(url.values["username"])
    if url.values["password"] is not None:
        query_length += len(url.values["password"])

    domain.add_double(url, plugin, {"resource_id": resource_id, "query_length": query_length,
                                    "insert_date": t, "update_timestamp": t})

def visit_site(db, process, driver, domain, plugin, temp_folder, cache):
    """ Loads the website and extract its information. """

    # Load the website and wait some time inside it
    try:
        driver.get('http://' + domain.values["name"])
    except TimeoutException:
        logger.warning("Site %s timed out (proc. %d)" % (domain.values["name"], process))
        driver.close()
        driver = build_driver(plugin, cache, process)
        while not driver:
            driver = build_driver(plugin, cache, process)
        driver.set_page_load_timeout(30)
        return driver, True
    except WebDriverException as e:
        logger.warning("WebDriverException on site %s / Error: %s (proc. %d)" % (domain.values["name"], str(e),
                                                                                  process))
        driver = reset_browser(driver, process, plugin, cache)
        return driver, True
    except Exception as e:
        logger.error("%s (proc. %d)" % (str(e), process))
        driver = reset_browser(driver, process, plugin, cache)
        return driver, True
    time.sleep(10)

    # Get network traffic dictionary
    # logger.debug(driver.log_types)
    log_entries = driver.get_log('performance')
    # logger.debug("(proc. %d) Network data: %s" % (process, str(log_entries)))
    network_traffic = get_network(log_entries)
    # logger.debug("(proc. %d) Extracted data: %s" % (process, str(network_traffic)))

    # Process traffic dictionary
    for key in network_traffic.keys():
        manage_request(db, process, domain, network_traffic[key], plugin, temp_folder)
        for sub_key in network_traffic[key]["requests"].keys():
            manage_request(db, process, domain, network_traffic[key]["requests"][sub_key], plugin, temp_folder)

    driver = reset_browser(driver, process, plugin, cache)
    return driver, False

visit_site(a_site)