Jobs = open('/home/yosse/Jobs_scraper/linkedin/spiders/Jobs.txt', 'r')
#"https://www.linkedin.com/jobs/search?
# keywords={Job}%27&location={Loc}&start=0"
def URL(link):
    start_urls =[]
    
    for job  in Jobs:
        for i in range(0,100,25):
            url = link+f'keywords={job}'+f"&location=Egypt"+f"&start={i}"
            start_urls.append(url)
    
    return start_urls