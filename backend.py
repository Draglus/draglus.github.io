from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from urllib.request import urlopen, Request
import urllib
import matplotlib.pyplot as plt
import time
import requests
import random
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from bs4 import BeautifulSoup
import pandas as pd

app = Flask(__name__)
CORS(app)

# Define global variables
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "utf-8",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0"
}

# Define functions for web scraping and text analysis
def search_function(Søgeord, lokation):
    ArbejdsTitel = []
    Beskrivelse = []
    LinkBeskrivelse = []
    Links = []

    df = {'ArbejdsTitel': [], 'Beskrivelse': []}
    Søgeord = Søgeord.replace(" ", "+")
    Søgeord = Søgeord.replace("ø", "oe")
    Søgeord = Søgeord.replace("æ", "ae")
    Søgeord = Søgeord.replace("å", "aa")
    link = [num for num in range(1, 2)] 
    for i in link:
        url = 'https://www.jobindex.dk/jobsoegning/' + lokation+'?page='+str(i) + '&q=%27'+Søgeord+'%27'#Bevæger sig igennem hjemmesiden, en side af gangen.
        try: 
            request = Request(url, headers=headers) #Bruger headers, for at sørge for, at jeg kan lave request fra hjemmesiden
            response = urlopen(request)
            html = response.read()
            response.close()
            soup = BeautifulSoup(html, 'html.parser')
            Smaa_beskrivelser = soup.find_all('div',class_='jix_robotjob-inner')
            h4_elements = soup.find_all('h4') #Finder titlerne på jobbet
            Beskrivelse_div = soup.find_all('div',class_='PaidJob-inner') # Finder beskrivelsen af jobbet
    
            for b2 in Beskrivelse_div:
                beskrivelse_elements = b2.find_all('p')
                if beskrivelse_elements:
                    Beskrivelse_text = " ".join([p.text.strip() for p in beskrivelse_elements])
                    Beskrivelse.append(str(Beskrivelse_text))
            for h4 in Beskrivelse_div:
                link_elements = h4.find('h4')
                for link_element in link_elements:
                    href_value = link_element.get('href') 
                    if link_element:
                        url_new = str(href_value)
                        Links.append(url_new)
                        response = requests.get(url_new)
                        if response.status_code == 200:
                            # Parse the HTML content
                            soup = BeautifulSoup(response.content, "html.parser")

                            # Find all text within the webpage
                            all_text = soup.get_text()
                            concatenated_text = ''.join(all_text.splitlines())
                            LinkBeskrivelse.append(str(concatenated_text))
                        
                        else:
                            LinkBeskrivelse.append("No link")
                           
            for b2 in Smaa_beskrivelser:
                beskrivelse_elements = b2.find_all('p')
                if beskrivelse_elements:
                    Beskrivelse_text = " ".join([p.text.strip() for p in beskrivelse_elements])
                    Beskrivelse.append(str(Beskrivelse_text))
                else:
                    Beskrivelse.append("_")
            for h4 in Smaa_beskrivelser:
                link_elements = h4.find('h4')
                for link_element in link_elements:
                    href_value = link_element.get('href') 
                    print(href_value)
                    if link_element:
                        url_new = str(href_value)
                        Links.append(url_new)
                        response = requests.get(url_new)
                        if response.status_code == 200:
                            # Parse the HTML content
                            soup = BeautifulSoup(response.content, "html.parser")
                            
                            # Find all text within the webpage
                            all_text = soup.get_text()
                            concatenated_text = ''.join(all_text.splitlines())
                            LinkBeskrivelse.append(str(concatenated_text))
                        
                        else:
                            LinkBeskrivelse.append("No link")
                            
                    
            for h4 in h4_elements:
                time.sleep(random.random()*0.05)
                titlen_element = h4.find('a') #Denne del finder specifikt titlen
                if titlen_element:
                    print(titlen_element.text)
                    ArbejdsTitel.append(str(titlen_element.text))
    
    
    
        except urllib.error.HTTPError:
            print("Pages not found")
    df['ArbejdsTitel'] = ArbejdsTitel
    df['Beskrivelse'] = Beskrivelse
    df['Links'] = Links
    df["Stor_Beskrivelse"] = LinkBeskrivelse
    df = pd.DataFrame(df)
    return df

def similarity(keyword, DescribeYourSelf, lokation):
    df = search_function(keyword,lokation)
    all_texts = df['Stor_Beskrivelse'].tolist() + [DescribeYourSelf]
    tfidf_vectorizer = TfidfVectorizer()
    tfidf_matrix = tfidf_vectorizer.fit_transform(all_texts)
    Self_Description_tfidf = tfidf_matrix[-1]  # Last vector is SelfDescription
    Beskrivelse_tfidf = tfidf_matrix[:-1]  # All vectors except the last one
    cosine_similarities = cosine_similarity(Self_Description_tfidf, Beskrivelse_tfidf)
    df['CosineSimilarity'] = cosine_similarities.tolist()[0]  # Convert to list and extract values
    df_sorted = df.sort_values(by='CosineSimilarity', ascending=False)
    return df_sorted
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    search_word = request.form.get('search_word', '')
    description = request.form.get('Description_Sentence', '')
    location = request.form.get('region-dropdown', '')

    result_df = similarity(search_word, description, location)

    # Convert DataFrame to JSON
    result_json = result_df.to_json(orient='records')

    return jsonify(result=result_json)

if __name__ == '__main__':
    app.run(debug=True, port=8080)
