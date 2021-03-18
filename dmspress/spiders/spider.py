import re
import scrapy
from scrapy.loader import ItemLoader
from ..items import DmspressItem
from itemloaders.processors import TakeFirst
import requests
import json
from scrapy import Selector
pattern = r'(\xa0)?'

url = "https://dmsgovernance.com/wp-admin/admin-ajax.php"

payload="action=get_more_posts&offset={}&category_id=25"
headers = {
  'authority': 'dmsgovernance.com',
  'pragma': 'no-cache',
  'cache-control': 'no-cache',
  'sec-ch-ua': '"Google Chrome";v="89", "Chromium";v="89", ";Not A Brand";v="99"',
  'accept': '*/*',
  'x-requested-with': 'XMLHttpRequest',
  'sec-ch-ua-mobile': '?0',
  'user-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36',
  'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
  'origin': 'https://dmsgovernance.com',
  'sec-fetch-site': 'same-origin',
  'sec-fetch-mode': 'cors',
  'sec-fetch-dest': 'empty',
  'referer': 'https://dmsgovernance.com/category/press_releases/',
  'accept-language': 'en-US,en;q=0.9',
  'cookie': '__cfduid=d315d609b866d886291046f9e74d1daf41614339769; _gcl_au=1.1.705995563.1614339772; _ga=GA1.2.1716179102.1614339772; hblid=9XWQD4eVljaY9H013n1Jp0NIB2oJ5z2O; olfsk=olfsk7336411166270291; cookie_notice_accepted=true; _gid=GA1.2.1056509146.1616058563; wcsid=q77uzvtT7suVE0de3n1Jp0N66BrKrzBR; _okdetect=%7B%22token%22%3A%2216160585646240%22%2C%22proto%22%3A%22https%3A%22%2C%22host%22%3A%22dmsgovernance.com%22%7D; _okbk=cd4%3Dtrue%2Cvi5%3D0%2Cvi4%3D1616058564943%2Cvi3%3Dactive%2Cvi2%3Dfalse%2Cvi1%3Dfalse%2Ccd8%3Dchat%2Ccd6%3D0%2Ccd5%3Daway%2Ccd3%3Dfalse%2Ccd2%3D0%2Ccd1%3D0%2C; _ok=2958-518-10-1493; _oklv=1616058781067%2Cq77uzvtT7suVE0de3n1Jp0N66BrKrzBR'
}

class DmspressSpider(scrapy.Spider):
	name = 'dmspress'
	start_urls = ['https://dmsgovernance.com/category/press_releases/']

	offset = 0

	def parse(self, response):
		data = requests.request("POST", url, headers=headers, data=payload.format(self.offset))
		data = json.loads(data.text)
		container = data['content']
		links = Selector(text=container).xpath('//h3/a/@href').getall()
		yield from response.follow_all(links, self.parse_post)

		if not data["is_last"]:
			self.offset += 12
			yield response.follow(response.url, self.parse, dont_filter=True)

	def parse_post(self, response):
		date = response.xpath('//div[@class="post_date"]/text()').get()
		title = response.xpath('//h1/text()').get()
		content = response.xpath('//div[@class="post_content"]//text()').getall()
		content = [p.strip() for p in content if p.strip()]
		content = re.sub(pattern, "", ' '.join(content))

		item = ItemLoader(item=DmspressItem(), response=response)
		item.default_output_processor = TakeFirst()

		item.add_value('title', title)
		item.add_value('link', response.url)
		item.add_value('content', content)
		item.add_value('date', date)

		yield item.load_item()
