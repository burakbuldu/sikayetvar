#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import codecs
import csv

import sys
if sys.version_info[0] >= 3:
    unicode = str
    
from htmlmin.minify import html_minify
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup

#proxies = {'http': 'http://89.105.202.101:3128/'}

def simple_get(url):
    """
    GET isteği yaparak url almaya çalışır.
    Yanıt HTML veya XML ise, içeriğini döndürür.
    Aksi halde None döner.
    """
    try:
        #with closing(requests.get(url, stream=True, proxies=proxies)) as resp:
        with closing(requests.get(url, stream=True)) as resp:
            if is_good_response(resp):
                return resp.content
            else:
                return None

    except RequestException as e:
        log_error('{0} için yapılan istekte hata döndü: {1}'.format(url, str(e)))
        return None

def is_good_response(resp):

    #Yanıt HTML ise True, aksi takdirde False döndürür.

    content_type = resp.headers['Content-Type'].lower()
    return (resp.status_code == 200
            and content_type is not None
            and content_type.find('html') > -1)


def log_error(e):

    #Hataları kaydeder.

    print(e)

domain = 'https://www.sikayetvar.com'
brand_names = ['marka1','marka-2'] #Markalar ['marka1','marka2',...] urlde nasıl geçiyorsa o şekilde yazılır

scraped_data = []

for brand in brand_names:
    brand_url = domain + '/' + brand

    brand_source = simple_get(brand_url)
    brand_soup = BeautifulSoup(html_minify(brand_source), 'html.parser')

    pagination = brand_soup.find('section',{'class':'pagination row'})

    sikayet_no =0

    """
    Markaya ait sayfa sayısının tespiti:
    İlk sayfanın değeri 0'dır.
    Eğer pagination değeri varsa +1 eklenir.
    """

    if pagination != None:

        num_of_pages = pagination.find_all('a')
        page_numbs = []
    
        for page_no in num_of_pages:
            page_numbs.append(page_no.text)
			
        last_page_no = int(page_numbs[-2])+1

    else:
        last_page_no = 2

    """
    Şikayetleri toplamak için
    Sayfalara gidilir
    pagination değeri yoksa sayfa sayısına 2 atanır
    """
    for x in range(1, last_page_no):
        page_num=x
        log = '\n '+ brand + ' için ' + str(page_num) + '. sayfa okunuyor...\n'
        print(log)

        page_source = simple_get(brand_url+'?page='+str(page_num))
        page_soup = BeautifulSoup(html_minify(page_source), 'html.parser') 

        item_pages = []

        """
        Her sayfa ziyaret edilir
        Sayfalar diziye alınır
        """
        
        for complaint in page_soup.find_all('a', {'class':'complaint-link-for-ads'}):
            item_pages.append(complaint['href'])

        for page in item_pages:

            sikayet_no = sikayet_no + 1
			
            """
            Diziden sayfalar çağırılır
            Şikayetler tek tek ziyaret edilir
            Şikayet sayfası pars edilir
            """

            sikayet_url = domain + page
            print('Okunan sayfa: ' + sikayet_url + '...')
            sikayet_source = simple_get(sikayet_url)
            sikayet_soup = BeautifulSoup(html_minify(sikayet_source), 'html.parser')
			
            """
            İndirilen kaynaktan
            İstenen veriler değişkenlere atanır
            """

            title = sikayet_soup.find('title')
            if title != None:
                title = title.text.strip('\n')
                title = title.replace(' - Şikayetvar', '')

            description = sikayet_soup.find('div', {'class':'description'})
            if description != None:
                description = description.text.strip('\n')

            date = sikayet_soup.find('span',{'class':'date date-tips'})
            if date != None:
                date = date['title'][:-5]

            views = sikayet_soup.find('span',{'class':'view-count-detail'})
            if views != None:
                views = views.b.text

            hashtags = sikayet_soup.find_all('a',{'class':'highlight'})
            tags = []
            for tag in hashtags:
                tags.append(tag['title'])

            sikayet_id = 1

            row = [sikayet_no,brand,title,description,date,views,tags]
            scraped_data.append(row)
    """
    row (satır) değişkeninde saklanan veriler
    CSV dosyalarına yazdırılır
    Marka şikayetleri bittiğinde veriler hafızadan temizlenir
    CSV dosyası kaydedilip kapatılır
    """
    with open(brand+".csv", "w", newline="") as csvfile:
        print('\n'+brand+' Bitti!\n')
        writer = csv.writer(csvfile, delimiter=';', quotechar='"')

        headers = ['ID','Marka','Başlık','Açıklama','Tarih','Görüntüleme Sayısı','Etiketler']
        writer.writerow(headers)

        for row in scraped_data:
            writer.writerow(row)
        scraped_data.clear()

print('Tüm işlemler bitti!')
