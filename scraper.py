# scraper.py

import json
import random
import socket
import pythonwhois
import sqlite3
import requests
import logging
import datetime
import lxml.html
import signal
from wig.wig import wig
from pprint import pprint

FORBIDDEN_URLS = [
    'facebook', 'google', 'twitter', 'instagram', 'pinterest', 'youtube'
]


class timeout:
    def __init__(self, seconds=1, error_message='Timeout'):
        self.seconds = seconds
        self.error_message = error_message

    def handle_timeout(self, signum, frame):
        raise TimeoutError(self.error_message)

    def __enter__(self):
        signal.signal(signal.SIGALRM, self.handle_timeout)
        signal.alarm(self.seconds)

    def __exit__(self, type, value, traceback):
        signal.alarm(0)


def convert_whois_date(whois_info_, date_name):
    try:
        whois_info_[date_name] = str(whois_info_[date_name])
    except KeyError:
        logging.warning('No ' + date_name + ' field in whois')
    pass


def get_whois(plain_domain_):
    logging.info('Getting WHOIS information...')
    try:
        whois_info = pythonwhois.get_whois(plain_domain_)
    except ConnectionError as e_:
        print(e_)
        logging.warning(e_)
        return ''
    except BaseException as e_:
        print(e_)
        logging.warning(e_)
        return ''
    else:
        convert_whois_date(whois_info, 'creation_date')
        convert_whois_date(whois_info, 'expiration_date')
        convert_whois_date(whois_info, 'updated_date')
        return str(json.dumps(whois_info))


def set_ssl(domain_):
    return 1 if 'https' in domain_ else 0


def strip_domain(domain_):
    domain_ = str(domain_)
    if domain_.startswith('http:'):
        domain_ = domain_[5:]
    if domain_.startswith('https:'):
        domain_ = domain_[6:]
    domain_ = domain_.strip('/')
    return domain_


def get_plain_domain(domain_):
    domain_ = strip_domain(domain_)
    if '?' in domain_:
        parts = domain_.split('?')
        domain_ = parts[0]
    parts = domain_.split('/')
    if len(parts) > 1:
        domain_ = parts[0]
    return domain_.strip('/')


def get_built_info(domain_):
    logging.info('Getting build information...')
    w = wig(url=domain_)
    w.run()
    return str(w.get_results())


class Website(object):
    def __init__(self, r_):
        self.ssl = set_ssl(str(r_.url))
        self.status = r_.status_code
        self.plain_domain = get_plain_domain(r_.url)
        self.date = str(datetime.datetime.now())
        self.content = str(r_.text)
        self.collected = 1
        self.headers = str(r_.headers)
        self.cookies = str(vars(r.cookies).__getitem__('_cookies'))
        self.whois = str(get_whois(self.plain_domain))
        self.ip = str(socket.gethostbyname(self.plain_domain))
        self.built = get_built_info(self.plain_domain)

    pass


def update_database(pk_, db, data_):
    logging.info('updating database...')
    db.execute("UPDATE website SET `ip` = ?, `ssl` = ?, `status` = ?, `date` = ?, `content` = ?, "
               "`headers` = ?, `cookies` = ?, `whois` = ?, collected = ?, built = ? WHERE id = ?",
               (data_.ip, data_.ssl, data_.status, data_.date, data_.content,
                data_.headers, data_.cookies, data_.whois, data_.collected, data_.built, pk_))
    pass


def get_links_from_website(content):
    logging.info('Gathering links from website...')
    links_ = []
    try:
        dom = lxml.html.fromstring(content)
    except Exception as e_:
        set_error_and_continue(pk, c, e_)
        logging.warning(e_)
    else:
        for link in dom.xpath('//a/@href'):
            if link != '#' and ('https:' in link or 'http:' in link):
                links_.append(link)
    return links_


def insert_outer_links_into_db(pk_, links_, data_):
    logging.info('Processing outer links...')
    objects = []
    contents = []
    for link in links_:
        link = strip_domain(link)
        if any(f_url not in link for f_url in FORBIDDEN_URLS):
            elements = link.split('/')
            date = str(datetime.datetime.now())
            if len(elements) > 1:
                root = elements[0]
                contents.append((pk_, 0, 'http://' + link, date, 0, 0, ''))
            else:
                root = link
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
    logging.info('Processing inner links...')
    contents = []
    for link in links_:
        link = strip_domain(link)
        if any(f_url not in link for f_url in FORBIDDEN_URLS):
            elements = link.split('/')
            date = str(datetime.datetime.now())
            if len(elements) > 1:
                contents.append((pk_, 0, 'http://' + link, date, 0, 0, ''))
    c.executemany('INSERT OR IGNORE INTO contents'
                  '(website_id,parent_id,url,date,status,collected,content) '
                  'VALUES (?,?,?,?,?,?,?)', contents)
    pass


def save_links(pk_, links_, data_):
    logging.info('Saving links...')
    inner_links = []
    outer_links = []
    for link in links_:
        if data_.plain_domain in link:
            inner_links.append(link)
        else:
            outer_links.append(link)
    inner_links = list(set(inner_links))
    outer_links = list(set(outer_links))
    insert_inner_links_into_db(pk_, inner_links)
    insert_outer_links_into_db(pk_, outer_links, data_)
    return


def set_error_and_continue(pk_, db, e_):
    db.execute("UPDATE website SET `status` = ?, `collected` = ?, `content` = ? WHERE id = ?", (1, 1, str(e_), pk_))
    pass


logging.basicConfig(filename='logs/scraper_log.log', level=logging.DEBUG, format='%(asctime)s %(message)s')

conn = sqlite3.connect('vandera.db')
c = conn.cursor()

collected = (0,)
c.execute('SELECT * FROM website WHERE collected=?', collected)
website = c.fetchone()
if website:
    domain = website[2]
    pk = website[0]
    print('Beginning SCRAPE for website ID: ' + str(pk) + ' DOMAIN: ' + str(domain))
    logging.info('Beginning SCRAPE for website ID: %s DOMAIN: %s', pk, domain)
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
        r = requests.get(domain, headers=headers, timeout=60)
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

        data = Website(r)
        update_database(pk, c, data)

        links = get_links_from_website(r.text)
        save_links(pk, links, data)

    conn.commit()
else:
    logging.warning('No Websites with COLLECTED = 0 found')

c.close()
conn.close()
