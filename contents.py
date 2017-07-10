# scraper.py

import random
import sqlite3
import requests
import logging
import datetime
import lxml.html

FORBIDDEN_URLS = [
    'facebook', 'google', 'twitter', 'instagram', 'pinterest', 'youtube'
]


def update_database(pk_, db, data_):
    db.execute("UPDATE contents SET `website_id` = ?, `parent_id` = ?, `url` = ?, `status` = ?, `date` = ?, "
               "`content` = ?, `collected` = ? WHERE id = ?",
               (data_.website_id, data_.parent_id, data_.url, data_.status, data_.date,
                data_.content, data_.collected, pk_))
    pass


def get_links_from_website(content, pk_, c_, r_):
    try:
        dom = lxml.html.fromstring(content)
    except Exception as e_:
        logging.warning(e_)
        set_error_and_continue(pk_, c_, r_)
        return []
    links_ = []
    for link_ in dom.xpath('//a/@href'):
        if link_ != '#' and ('https:' in link_ or 'http:' in link_):
            links_.append(link_)
    return links_


def insert_outer_links_into_db(pk_, links_, data_):
    objects = []
    contents = []
    for link_ in links_:
        link_ = strip_domain(link_)
        if any(f_url not in link for f_url in FORBIDDEN_URLS):
            elements = link_.split('/')
            date = str(datetime.datetime.now())
            if len(elements) > 1:
                root = elements[0]
                contents.append((pk_, 0, 'http://' + link_, date, 0, 0, ''))
            else:
                root = link_
            if data_.plain_domain not in root:
                objects.append((pk_, 'http://' + root, 0, 0, date, '', '', '', '', '', '', 0, 0))
            else:
                contents.append((pk_, 0, 'http://' + root, date, 0, 0, ''))
    c.executemany('INSERT OR IGNORE INTO contents'
                  '(website_id,parent_id,url,date,status,collected,content) '
                  'VALUES (?,?,?,?,?,?,?)', contents)
    c.executemany('INSERT OR IGNORE INTO website'
                  '(parent_id,domain,ssl,status,date,content,headers,cookies,session,built,whois,scraped,collected) '
                  'VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)', objects)
    pass


def insert_inner_links_into_db(pk_, links_):
    contents = []
    for link_ in links_:
        link_ = strip_domain(link_)
        if any(f_url not in link for f_url in FORBIDDEN_URLS):
            elements = link_.split('/')
            date = str(datetime.datetime.now())
            if len(elements) > 1:
                contents.append((pk_, 0, 'http://' + link_, date, 0, 0, ''))
    c.executemany('INSERT OR IGNORE INTO contents'
                  '(website_id,parent_id,url,date,status,collected,content) '
                  'VALUES (?,?,?,?,?,?,?)', contents)
    pass


def save_links(pk_, links_, data_):
    inner_links = []
    outer_links = []
    for link_ in links_:
        if data_.plain_domain in link_:
            inner_links.append(link_)
        else:
            outer_links.append(link_)
    inner_links = list(set(inner_links))
    outer_links = list(set(outer_links))
    insert_inner_links_into_db(pk_, inner_links)
    insert_outer_links_into_db(pk_, outer_links, data_)
    return


def get_plain_domain(domain_):
    domain_ = strip_domain(domain_)
    if '?' in domain_:
        parts = domain_.split('?')
        domain_ = parts[0]
    parts = domain_.split('/')
    if len(parts) > 1:
        domain_ = parts[0]
    return domain_.strip('/')


def strip_domain(domain_):
    domain_ = str(domain_)
    if domain_.startswith('http:'):
        domain_ = domain_[5:]
    if domain_.startswith('https:'):
        domain_ = domain_[6:]
    domain_ = domain_.strip('/')
    return domain_


def set_error_and_continue(pk_, db, r_):
    db.execute("UPDATE contents SET `status` = ?, `collected` = ? WHERE id = ?", (1, 1, pk_))
    pass


class Contents(object):
    def __init__(self, r_, website_):
        self.plain_domain = get_plain_domain(r_.url)
        self.website_id = website_[1]
        self.parent_id = website_[2]
        self.url = website_[3]
        self.status = r_.status_code
        self.date = str(datetime.datetime.now())
        self.content = str(r_.text)
        self.collected = 1

    pass


logging.basicConfig(filename='logs/contents_log.log', level=logging.DEBUG, format='%(asctime)s %(message)s')

conn = sqlite3.connect('vandera.db')
c = conn.cursor()

collected = (0,)
c.execute('SELECT * FROM contents WHERE collected=?', collected)
website = c.fetchone()
if website:
    link = website[3]
    pk = website[0]
    print('Beginning SCRAPE for content ID: ' + str(pk) + ' DOMAIN: ' + str(link))
    logging.info('Beginning SCRAPE for content ID: %s DOMAIN: %s', pk, link)
    headers_list = [
        'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.108 Safari/537.36 '
        '2345Explorer/7.1.0.12633',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_8) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.45 '
        'Safari/535.19',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/34.0.1847.116 '
        'Chrome/34.0.1847.116 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0',
        'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36 '
        'OPR/32.0.1948.25',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11) AppleWebKit/601.1.39 (KHTML, like Gecko) Version/9.0 '
        'Safari/601.1.39 '
    ]
    headers = requests.utils.default_headers()
    headers.update({
        'User-Agent': random.choice(headers_list)
    })
    try:
        r = requests.get(link, headers=headers, timeout=2)
    except requests.exceptions.Timeout as e:
        set_error_and_continue(pk, c, e)
        logging.warning(e)
    except requests.exceptions.TooManyRedirects as e:
        set_error_and_continue(pk, c, e)
        logging.warning(e)
    except requests.exceptions.RequestException as e:
        set_error_and_continue(pk, c, e)
        logging.warning(e)
    else:
        logging.info('Got parsed information')

        data = Contents(r, website)
        update_database(pk, c, data)

        links = get_links_from_website(r.text, pk, c, r)
        save_links(pk, links, data)

    conn.commit()

c.close()
conn.close()
