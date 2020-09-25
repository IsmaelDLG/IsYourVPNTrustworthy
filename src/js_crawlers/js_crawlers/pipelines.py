# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import json
import os

class JsCrawlersPipeline:
    def process_item(self, item, spider):
        return item

class FileSaverPipeline(object):
    def open_spider(self, spider):
        if not os.path.exists('out/'):
            os.mkdir('out/')

    def close_spider(self, spider):
        pass

    def process_item(self, item, spider):
        url = item['url']
        page = item['page']
        with open('out/%s.html' % url.replace('https:', '').replace('/','').replace('.', '-'), 'w') as f:
            f.write(page)
        return item