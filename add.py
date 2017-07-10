# test.py

import sys
import sqlite3


def strip_domain(domain_):
    domain_ = str(domain_)
    if domain_.startswith('http:'):
        domain_ = domain_[5:]
    if domain_.startswith('https:'):
        domain_ = domain_[6:]
    domain_ = domain_.strip('/')
    return domain_


conn = sqlite3.connect('vandera.db')
c = conn.cursor()

arg = sys.argv[1]
if arg:
    url = strip_domain(arg)
    date = str(sqlite3.datetime.datetime.now())
    object_ = (
        0,  # parent_id
        'http://' + url,  # domain
        0,  # ssl
        0,  # status
        date,  # date
        '',  # content
        '',  # headers
        '',  # cookies
        '',  # session
        '',  # built
        '',  # whois
        0,  # scraped
        0  # collected
    )
    c.execute('insert or ignore into website'
                  '(parent_id,domain,ssl,status,date,content,headers,cookies,session,built,whois,scraped,collected) '
                  'values (?,?,?,?,?,?,?,?,?,?,?,?,?)', object_)
    conn.commit()

c.close()
conn.close()