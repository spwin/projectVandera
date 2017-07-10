# create_database.py

import sqlite3
import csv
import datetime

conn = sqlite3.connect('vandera.db')
c = conn.cursor()

c.execute("create table if not exists website ("
          "id integer primary key,"
          "parent_id integer,"
          "domain varchar unique,"
          "ip varchar,"
          "ssl integer,"
          "status integer,"
          "date varchar,"
          "content text,"
          "headers text,"
          "cookies text,"
          "session text,"
          "built varchar,"
          "whois text,"
          "scraped integer,"
          "collected integer)")

c.execute("create table if not exists contents ("
          "id integer primary key,"
          "website_id integer,"
          "parent_id integer,"
          "url text unique,"
          "status integer,"
          "date varchar,"
          "content text,"
          "collected integer)")

with open('top500domains.csv', 'rt') as csvfile:
    reader = csv.reader(csvfile, delimiter=',', quotechar='"')
    objects = []
    for row in reader:
        url = str(row[1]).strip('/')
        date = str(datetime.datetime.now())
        objects.append((
            0,  # parent_id
            'http://'+url,  # domain
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
        ))
    c.executemany('insert or ignore into website'
                  '(parent_id,domain,ssl,status,date,content,headers,cookies,session,built,whois,scraped,collected) '
                  'values (?,?,?,?,?,?,?,?,?,?,?,?,?)', objects)
    conn.commit()

c.close()
conn.close()
