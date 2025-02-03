from time import sleep
from bs4 import BeautifulSoup
from requests import get
from urllib.parse import unquote #used to decode the url
from .user_agents import get_useragent