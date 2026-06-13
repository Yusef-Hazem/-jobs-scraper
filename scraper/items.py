import scrapy
from itemloaders.processors import  MapCompose , TakeFirst ,Compose
from w3lib.html import remove_tags
# Load the model and tokenizer for extract entities 
from transformers import AutoModelForTokenClassification, AutoTokenizer
from transformers import pipeline

#load embedding and job normalization requirements
from sentence_transformers import SentenceTransformer
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

#dealing with dates 
from datetime import datetime
from dateutil.relativedelta import relativedelta
#for country allocation
from geopy.geocoders import Nominatim
#extract entities model
model_identifier = "GalalEwida/LLM-BERT-Model-Based-Skills-Extraction-from-jobdescription"
tokenclassification = AutoModelForTokenClassification.from_pretrained(model_identifier)
tokenizer = AutoTokenizer.from_pretrained(model_identifier)
nlp = pipeline("ner", model=tokenclassification, tokenizer=tokenizer)


#embedding model
emedding  = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
tech_df = pd.read_csv(r"~/Jobs_scraper/linkedin/techh1.csv")
job_titles = tech_df["job titles"]
job_title_embeddings = emedding.encode(job_titles)

def job_normalization(value):
    target_term = str(value)
    target_embedding = emedding.encode([target_term])
    similarities = cosine_similarity(target_embedding, job_title_embeddings)[0]
    max_index = similarities.argmax()
    most_similar = job_titles[max_index]
    job_title_words = set(value.lower().split())
    most_similar_words = set(most_similar.lower().split())
    common_words = job_title_words.intersection(most_similar_words)
    if len(common_words) >=2 :
        return most_similar
    else : 
        raise scrapy.exceptions.DropItem("Item deleted job")

def extract_entities(job_description):
    skills = 'TECHNOLOGY'
    bio_result = nlp(job_description)
    entity = ''
    entities = set()  
    flag = 0
    for i in bio_result:
        if i['entity'] == f'I-{skills}' and flag == 1:
            entity += i['word'].replace(" ##", "").replace("##", "")
        elif i["entity"] == f'B-{skills}':
            if entity:
                entities.add(entity.strip())  
            entity = ''
            flag = 1
            entity = i['word'].replace(" ##", "").replace("##", "")
        else:
            flag = 0
            if entity:
                entities.add(entity.strip())  
            entity = ''

    if entity:
        entities.add(entity.strip())  

    return list(entities)  

def deal_wih_date(date_scraped):
    today = datetime.now()

    if 'day' in date_scraped:
        days = int(date_scraped.split()[0])
        return (today - relativedelta(days=days)).strftime('%Y-%m-%d')
    elif 'week' in date_scraped:
        weeks = int(date_scraped.split()[0])
        return (today - relativedelta(weeks=weeks)).strftime('%Y-%m-%d')
    elif 'month' in date_scraped:
        months = int(date_scraped.split()[0])
        return (today - relativedelta(months=months)).strftime('%Y-%m-%d')
    else:
        raise scrapy.exceptions.DropItem("Item deleted date")  
'''
def deal_wih_date_wuzzuf(date_scraped):
    today = datetime.now()

    if 'days' in date_scraped:
        days = int(date_scraped.split()[1])
        return (today - relativedelta(days=days)).strftime('%Y-%m-%d')
    elif 'weeks' in date_scraped:
        weeks = int(date_scraped.split()[1])
        return (today - relativedelta(weeks=weeks)).strftime('%Y-%m-%d')
    elif 'months' in date_scraped:
        months = int(date_scraped.split()[1])
        return (today - relativedelta(months=months)).strftime('%Y-%m-%d')
    else:
        raise scrapy.exceptions.DropItem("Item deleted date")  
'''

def get_country(location):
    geolocator = Nominatim(user_agent = "GetLoc")

    location = geolocator.geocode(location)
    print(location)
    if location:
        return location.address.split(',')[-1].strip()
    else:
        return None

def Extract_location(location): 
    return location.split(",")[0]

def cleanup (value) : 
    return value.strip()


class Items(scrapy.Item):
    job_title = scrapy.Field(
        input_processor =MapCompose(remove_tags , cleanup ,job_normalization ) , 
        output_processor = TakeFirst())
    
    seniority_level = scrapy.Field(
        input_processor =MapCompose(remove_tags ,cleanup) , 
        output_processor = TakeFirst())
    
    employment_type = scrapy.Field(
        input_processor =MapCompose(remove_tags,cleanup) , 
        output_processor = TakeFirst())
        
    company_name = scrapy.Field(
        input_processor =MapCompose(remove_tags ,cleanup) , 
        output_processor = TakeFirst())
    
    city_name = scrapy.Field(
        input_processor =MapCompose(remove_tags ,cleanup , Extract_location) , 
        output_processor = TakeFirst())
    
    country_name =scrapy.Field(
        input_processor =MapCompose(remove_tags ,cleanup , get_country) , 
        output_processor = TakeFirst())
    
    posted_date = scrapy.Field(
        input_processor =MapCompose(remove_tags ,cleanup ,deal_wih_date) , 
        output_processor = TakeFirst())
    skills = scrapy.Field(
        input_processor =MapCompose(remove_tags ,extract_entities) , 
        output_processor= Compose())
    
'''    
    job_published_date_wuzzuf = scrapy.Field(
        input_processor =MapCompose(remove_tags ,cleanup ,deal_wih_date_wuzzuf) , 
        output_processor = TakeFirst())
'''    
