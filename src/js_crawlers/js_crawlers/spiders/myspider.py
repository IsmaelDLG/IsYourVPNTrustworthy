# -*- coding: utf-8 -*-
"""Crawler to download all the webpages from the top500 list.

In this module, all the list is crawled and dowloaded. This is run both in an 
environment with a VPN and in an environment without one. By downloading the pages, we 
want to find wether JS is being injected in them or not, and if the VPN is injecting 
it on us.
"""
import scrapy
from scrapy.crawler import CrawlerProcess
from pathlib import Path
import urllib
import requests


def get_website_list(filepath: str) -> list:
    """This method parses the document obtained from https://moz.com/top500 into a list 
    object that contains the urls. The .csv file must use the ',' character as 
    separator.

    :param filepath: Path to the .csv file that contains the list.

    :return: A list of URLs, as strings.
    """
    clean_list = []

    if Path(filepath).exists():
        with open(filepath, "r") as f:
            raw_list = f.readlines()

        raw_list.pop(0)
        for row in raw_list:
            field = row.split(",")[1].replace('"', "")

            if field.startswith("http"):
                clean_list.append(field)
            elif field.startswith("www"):
                clean_list.append("https://" + field)
            else:
                clean_list.append("https://www." + field)

    return clean_list


class Page(scrapy.Item):
    """Our own Item object.

    Scrapy can return Items from spiders. The item class has been adapted to our needs.
    """

    url = scrapy.Field()
    page = scrapy.Field()
    last_updated = scrapy.Field(serializer=str)


class MySpider(scrapy.Spider):
    """Crawler implementation.

    Each spider Scrapy launches executes, by default the method parse. This 
    implementation is very simple, once it gets the page, it returns it. The list of 
    webpages is obtained from the top500 from moz, mentioned above.
    """

    name = "myspider"
    start_urls = get_website_list(
        Path(__file__).parent.absolute().resolve() / Path("top500Domains.csv")
    )

    def parse(self, response):
        """Returns the url and the html of the page, encapsulated in a Page object."""
        return Page(url=response.url, page=response.text)


if __name__ == "__main__":
    process = CrawlerProcess(
        settings={
            "USER_AGENT": "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)",
        }
    )

    process.crawl(MySpider)
    process.start()  # the script will block here until the crawling is finished
