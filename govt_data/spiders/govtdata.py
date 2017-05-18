# -*- coding: utf-8 -*-
import scrapy

class GovtdataSpider(scrapy.Spider):
	'''This spider extracts a dictionary of the available data 
	   on data.govt.nz'''

	name = "govtdata"
	#allowed_domains = [".*govt.nz.*"]
	allowed_domains = ["data.govt.nz"]
	start_urls = ['https://data.govt.nz/search?q=']

	def parse(self, response):
		# get info cards
		info_cards = response.xpath('//*[@id="main-content"]/div[2]/div/div[@class="collatedInfo cf"]')

		for card in info_cards:
			# Get the details for each government database
			yield {
			'title' : card.xpath('div[1]/h5/a/strong').re("<strong>\s*(.+?)\s*</strong>")[0],
			'link' : response.urljoin(card.xpath('div[1]/h5/a/@href').extract_first()),
			'description' : card.xpath('div[1]/p/text()').extract_first(),
			'agency' : card.xpath('div[1]/div[1]/text()').re("\s*(.+)\s*")[-1],
			'type' : card.xpath('div[1]/div[2]/text()').re("\s*(.+)\s+")[-1],
			'formats' : sorted(card.xpath('div[2]/ul/li/label/text()').extract()),
			}

		page_links =  response.xpath('//*[@id="main"]/div[3]/div[2]/a[@class="next_page"]/@href').extract()[-1]
		next_page = page_links[-1]
		if page_links is not None:
			next_page = response.urljoin(next_page)
			yield scrapy.Request(next_page, callback=self.parse)
		