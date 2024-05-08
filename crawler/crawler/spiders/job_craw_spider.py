import scrapy
import requests
import json
import chompjs
from scrapy_splash import SplashRequest
from scrapy import signals
from scrapy.signalmanager import dispatcher
# from crawler.items import JobItem


def handle_spider_closed(spider):
    final_results = spider.crawler.stats.get_value('final_results')
    print(final_results)  # You can process the data as needed here
    print(len(final_results))

class JobSpider(scrapy.Spider):
    name = 'job_spider'
    allowed_domains = ['jobs.workable.com']
    start_urls = ['https://jobs.workable.com/search?location=uk&query=full+stack']

    custom_settings = {
        'HTTP_PROXY': 'http://150.107.136.110:8082',
        'HTTPS_PROXY': 'https://150.107.136.110:8082'
    }

    def __init__(self, *args, **kwargs):
        super(JobSpider, self).__init__(*args, **kwargs)
        dispatcher.connect(handle_spider_closed, signal=signals.spider_closed)

    def parse(self, response):
        javascript = response.css("script::text").get()
        data = chompjs.parse_js_object(javascript)

        job_return_list = []
        next_page_token = data['initialState']['api/v1/jobs']['data']['nextPageToken']
        job_data = data['initialState']['api/v1/jobs']['data']['jobs']
        job_return_list+=self.get_job_data(job_data)
        while next_page_token:
            response = requests.get(f'https://jobs.workable.com/api/v1/jobs?query=full+stack&location=uk&pageToken={next_page_token}', timeout=1000)
            response_data = response.json()
            job_data = response_data['jobs']
            job_return_list+=self.get_job_data(job_data)
            next_page_token = response_data.get('nextPageToken', None)

        self.crawler.stats.set_value('final_results', job_return_list)
        # print(job_return_list)

    def get_job_data(self, job_list):
        job_return_list = []
        for job in job_list:
            job_data = {}
            job_data['title'] = job['title']
            job_data['location'] = job['location']['countryName']
            job_data['url'] = job['url']
            job_return_list.append(job_data)

        return job_return_list
