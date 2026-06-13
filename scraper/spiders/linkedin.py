import scrapy
from scrapy.spiders import CrawlSpider ,Rule
from scrapy.linkextractors import LinkExtractor
from ..items import Items
from scrapy.loader import ItemLoader
from .URLs import URL
class linkedinSpider(CrawlSpider):
    name = "linkedin"
    numpages =1
    allowed_domains = ["linkedin.com"]
    start_urls = URL('https://www.linkedin.com/jobs/search?')
    rules  = (
    #Rule(LinkExtractor (allow=(r'start=',))),
    Rule(LinkExtractor (allow=(r'/jobs/view/',)) ,callback = 'parse_job' ) , 
    )

    def parse_job(self, response):

        L = ItemLoader( item= Items() , response= response)
        L.add_css('job_title' , 'h1.top-card-layout__title')
        #L.add_css('seniority_level' , 'li.description__job-criteria-item:nth-child(1) span.description__job-criteria-text--criteria')
        #L.add_css('employment_type' , 'li.description__job-criteria-item:nth-child(2) span.description__job-criteria-text--criteria')
        L.add_xpath('seniority_level', '//li[contains(@class, "description__job-criteria-item")][.//h3[contains(text(), "Seniority level")]]//span[contains(@class, "description__job-criteria-text--criteria")]/text()')
        L.add_xpath('employment_type', '//li[contains(@class, "description__job-criteria-item")][.//h3[contains(text(), "Employment type")]]//span[contains(@class, "description__job-criteria-text--criteria")]/text()')
        #L.add_css('seniority_level', 'li.description__job-criteria-item:has(h3:contains("Seniority level")) span.description__job-criteria-text--criteria::text')
        #L.add_css('employment_type', 'li.description__job-criteria-item:has(h3:contains("Employment type")) span.description__job-criteria-text--criteria::text')
        L.add_css('company_name' , 'a.topcard__org-name-link.topcard__flavor--black-link')
        L.add_css('city_name' , 'span.topcard__flavor.topcard__flavor--bullet')
        L.add_css('country_name' , 'span.topcard__flavor.topcard__flavor--bullet')
        
        #posted-time-ago__text topcard__flavor--metadata
        L.add_css('posted_date' , 'span.posted-time-ago__text.topcard__flavor--metadata')
        L.add_css('skills' ,'div.show-more-less-html__markup.show-more-less-html__markup--clamp-after-5.relative.overflow-hidden')
        #L.add_css('job_desc' ,'div.show-more-less-html__markup.show-more-less-html__markup--clamp-after-5.relative.overflow-hidden')
        #L.add_xpath('job_description' , '//div[contains(@class, "show-more-less-html__markup")]/br/following-sibling')
        return L.load_item()
        
         
        """
           job_title = response.css('h1.top-card-layout__title::text').get()
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