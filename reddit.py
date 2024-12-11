import re
import json
import requests

def regex_links(text):
    #find all the links in a text
    return re.findall(r'https?://[^\s)\]]+', text)

#define recursive helper function that will scrape comment data
def link_search(comment):
    #store all the links found so far
    links = []
    #track only comments that are replies
    if comment['kind'] != 'more':
        #get the current comment text
        text = comment['data']['body']
        #add links found in current comment
        links = links + regex_links(text)
    else:
        return []

    #handle instance where comment does not have replies
    if isinstance(comment['data']['replies'], str):
        links = links + []
    #scrape the replies of the comments
    else:
        for reply in comment['data']['replies']['data']['children']:
            #get links of children
            links = links + link_search(reply)
    return links

def get_links(url):
    #manipulate url for json format
    if url[-1] == "/":
        #add json formatting
        url = url[:-1] + '.json'
    else:
        #add json formatting
        url = url + '.json'

    #make request
    headers = {'User-Agent': 'Mozilla/5.0'}
    page = requests.get(url, headers=headers)

    #load in json data
    data = json.loads(page.text)

    #get links mentioned in post
    links = regex_links(data[0]['data']['children'][0]['data']['selftext'])

    #get the comments to the original mention
    for comment in data[1]['data']['children']:
        links = links + link_search(comment)

    #remove duplicates
    links = list(set(links))

    return links