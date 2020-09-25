"""Pipelines the spiders use.

Following Scrapy's structure, pipelines are implemented in this file. I have implemented mainly two pipelines into our project: JsCrawlersPipeline, FileSaverPipeline.
"""
from itemadapter import ItemAdapter
import json
import os


class JsCrawlersPipeline:
    """Basic pipeline, return items after being processed. Useful for interaction with other scripts"""

    def process_item(self, item, spider):
        return item


class FileSaverPipeline(object):
    """This pipeline saves each page processed to a file in the out directory. Each file's name is it's url. The content of the file is the whole html and js the browser would render.
    """

    def open_spider(self, spider):
        if not os.path.exists("out/"):
            os.mkdir("out/")

    def process_item(self, item, spider):
        url = item["url"]
        page = item["page"]
        with open(
            "out/%s.html"
            % url.replace("https:", "").replace("/", "").replace(".", "-"),
            "w",
        ) as f:
            f.write(page)
        return item
