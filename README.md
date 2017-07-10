# Project Vandera
Experimental version
Websites metas, details and content scraper robot written in Python3.5
There are 2 Databases and 2 Robots.<br/><br/>
**Robot 1** looking over the `website` table, collecting information<br/>
**Robot 2** looking over the `contents` table and collecting all the content of inner pages
<br/>
Both are adding new links either to the `website` (if it is new domain) or `contents` table accordingly

## Running the project
It was written using python3.5 so make sure you are using the same version to prevent any problems.
Use These commands to run:
```
python3.5 create_database.py
./website_parser.sh 10
./content_parser.sh 10
```
The result is stored in sqlite3 database. There is no GUI to display and manipulate the information, all the searches and operations on the data you should perform directly from sqlite3 iterface using vandera.db file.
<br/>
#### Database
First of all you need to initialise the database by running the command:
```
python3.5 create_database.py
```
It will create `vandera.db` sqlite3 database file in project root directory. There are two tables, one for websites information and one for website content.
<br/><br/>
**Websites table**
<br/>
```
`id`        # ID of the record
`parent_id` # If website is found while scraping another, this is the parent ID
`domain`    # Domain name
`ip`        # Websites IP
`ssl`       # Boolean telling if there is an SSL Certificate used
`status     # Response status
`date`      # Date information scraped
`content`   # Raw content of the website
`headers`   # Headers received by a HTTP response
`cookies`   # Cookies set
`session`   # Unused
`built`     # Website build and vulnerabilities information (using wig)
`whois`     # Whois information
`scraped`   # Boolean if the website is already scraped
`collected` # Boolean if the content for the website is already collected
```
<br/><br/>
**Contents table**
<br/>
```
`id`          # ID of the record
`website_id`  # ID of the record from website table for which this link was added (0 if added from contents table)
`parent_id`   # ID of the record from contents table where the link was found (0 if added from websites table)
`url`         # Link URL
`status`      # HTTP response status
`date`        # Date information was scraped
`content`     # Raw website content
`collected`   # Boolean if the information for the url has been already collected
```

#### Scraping robots
I have created bash scripts to iterate python script for parsing websites and contents.
To run the `website` table parser robot use:
```
./website_parser.sh 10
```
Where 10 is the number of iterations. You can change this value.<br/><br/>

To run `contents` table scraper robot use:
```
./content_parser.sh 10
```
Again, 10 is the number of iteration, you can use yours count.

**I do not recommend adding very large content scraper iterations number as it stores raw data and it is about 50GB in 2h**
