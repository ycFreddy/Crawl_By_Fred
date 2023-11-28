import os
import re
import requests
import urllib.request
from bs4 import BeautifulSoup
from collections import deque
from html.parser import HTMLParser
from urllib.parse import urlparse
import csv

HTTP_URL_PATTERN = r'^http[s]{0,1}://.+$'
site_url = "https://openai.com"
local_domain = "openai.com"

class PageInfos:
  def __init__(self, url):
    super().__init__()
    self.url = url
    self.reponse = requests.get(self.url)
    self.status = self.reponse.status_code        
    if self.status == 200:
        self.page = BeautifulSoup(self.reponse.text, "html.parser")
        self.titre = self.page.find("title").text
        self.meta_description = self.page.find("meta", attrs={"name":"description"})
        self.h1 = self.page.find("h1")
        self.liens = [a['href'] for a in self.page.find_all('a', href=True)]           
        self.liens_clean = clean_liens(self.liens)
        #print("ici:", self.liens_clean)

def clean_liens(liens):
    clean_links = deque([])
    for lien in liens:
        clean_link = None
        if re.search(HTTP_URL_PATTERN, lien):
            url_obj = urlparse(lien)
            if url_obj.netloc == local_domain:
                clean_link = lien
        else:
            if lien.startswith("/"):
                lien = lien[1:]
            elif (lien.startswith("#") or lien.startswith("mailto:") or lien.startswith("tel:")):
                continue
            if  lien.endswith(".xml") or lien.endswith(".pdf"):
                continue
            if re.findall(r"facebook\b", str(lien)) or re.findall(r"twitter\b", str(lien)) or re.findall(r"instagram\b", str(lien)) or re.findall(r"pinterest\b", str(lien)):
                continue            
            clean_link = "https://" + local_domain + "/" + lien

        if clean_link is not None:
            if clean_link.endswith("/"):
                clean_link = clean_link[:-1]
            clean_links.append(clean_link)            
    return list(set(clean_links))

def remplirCSV (nomfichier, ligne):
    titre = ""
    meta_description = ""
    h1 = ""
    fieldnames = ["Status code", "Url", "Titre", "Meta Description", "H1"]
    if not os.path.exists(nomfichier):
        with open(nomfichier, 'w', encoding="UTF-8", newline='') as csvfile:            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
    
    with open(nomfichier, 'a', encoding="UTF-8", newline='') as csvfile:            
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)        
        if ligne.status == 200:    
            if ligne.titre is not None: titre = ligne.titre
            if ligne.meta_description is not None: meta_description = ligne.meta_description["content"]
            if ligne.h1 is not None: h1 = str(ligne.h1.text)
        writer.writerow({"Status code":ligne.status, "Url":ligne.url, "Titre":titre, "Meta Description":meta_description, "H1":h1})

def crawl (url, nomfichier):
    lienvu = set([url])
    infos = PageInfos(url)
    queue = infos.liens_clean
    while queue:
        #traiter le lien        
        lien = queue.pop()         
        if lien not in lienvu:
            lienInfos = PageInfos(lien)
            print("Status:", lienInfos.status, "Url:", lien)
            remplirCSV (nomfichier, lienInfos)
            if lienInfos.status == 200:
                queue.extend(lienInfos.liens_clean)
            lienvu.add(lien)
        queue = list(set(queue))
        
crawl(site_url,"export_crawl.csv")