import requests
import pandas as pd

url = "https://api.openchargemap.io/v3/poi/?output=json&countrycode=AU&maxresults=100"

response = requests.get(url)

data = response.json()

print(len(data))
