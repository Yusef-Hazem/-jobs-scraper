import scrapy
from scrapy.spiders import CrawlSpider ,Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.loader import ItemLoader
from ..items import Items
class WuzzafSpider(CrawlSpider):
    name = "wuzzuf"
    allowed_domains = ["wuzzuf.net"]
    numpages = 1
    '''
    start_urls = [f"https://wuzzuf.net/search/jobs/?a=navbg&q=data%20analysis&start=0"]
    rules = (
        Rule(LinkExtractor(allow=(r'https://wuzzuf.net/jobs/p/',)), process_request='process_request', callback='parse_job', follow=True),
    )
    
    def process_request(self, request , response):
        return SplashRequest(request.url, self.parse_job, args={'wait': 3})
    
    
    '''
    for i in range(numpages):
        start_urls = [f"https://wuzzuf.net/search/jobs/?a=navbg&q=data%20scientist&start={i}"]
        rules = (
            Rule(LinkExtractor(allow=(r'/jobs/p/',)), callback='parse_job', follow=True),
        )
        #process_request='use_playwright'
    #def use_playwright(self, request, response):
    #    """Inject Playwright meta into requests"""
    #    request.meta['playwright'] = True
    #    return request
    
    def parse_job(self, response):

        L = ItemLoader( item= Items() , response= response)
        L.add_css('job_title' , 'h1.css-f9uh36')
        #L.add_xpath('seniority_level' , '//div[span[text()="Career Level:"]]/span[@class="css-47jx3m"]/span[@class="css-4xky9y"]')
        #L.add_xpath('seniority_level' , '//div[span[text()="Career Level:"]]/span/span[@class="css-4xky9y"]')
        L.add_css('location' , 'strong.css-9geu3q::text')
        ##L.add_css('country' , 'span.topcard__flavor.topcard__flavor--bullet')
        L.add_css('employment_type' , 'a.css-g65o95::text')
        ###posted-time-ago__text topcard__flavor--metadata
        L.add_css('job_published_date_wuzzuf' , 'span.css-182mrdn')
        L.add_css('job_description' ,'div.css-s2o0yh *::text')
        ##L.add_css('job_desc' ,'div.show-more-less-html__markup.show-more-less-html__markup--clamp-after-5.relative.overflow-hidden')
        ##L.add_xpath('job_description' , '//div[contains(@class, "show-more-less-html__markup")]/br/following-sibling')
        return L.load_item()
        
         
        """
           job_title = response.css('h1.css-f9uh36::text').get()
           
           seniority_level = response.css('span.description__job-criteria-text.description__job-criteria-text--criteria::text').get()
           company_name = response.css('a.topcard__org-name-link.topcard__flavor--black-link::text').get()
           location = response.css('span.topcard__flavor.topcard__flavor--bullet::text').get()
           employment_type = response.css('span.description__job-criteria-text.description__job-criteria-text--criteria::text').get()
           
           first_statment =response.css('div.show-more-less-html__markup.show-more-less-html__markup--clamp-after-5.relative.overflow-hidden::text').get()
           br_texts =response.xpath('//div[contains(@class, "show-more-less-html__markup")]/br/following-sibling::text()').extract()
           filtered_br = [text.strip() for text in br_texts if text.strip()]
           complete_content = ' '.join(filtered_br)
           job_description = first_statment.strip()+' '+ complete_content 
           
           job_published_date = response.css('span.posted-time-ago__text.posted-time-ago__text--new.topcard__flavor--metadata::text').get()
           posted-time-ago__tex.topcard__flavor--metadata
        """