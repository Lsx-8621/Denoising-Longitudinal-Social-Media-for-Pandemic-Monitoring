import re
import glob
import tqdm 
import pandas as pd


pattern_1 = re.compile(r"(\b(if|or|nor|may)\b|tell|told|manage|say|said|want|wanna|try|tried|guess|have not|havent|haven't|didn|don|would|will|can|could|rather|might|dream|hate|likely|seem|scare|pretend|chance|prolly|probably|look to|possibly|think|thought|imagine|feel|felt|plan|wonder|doubt|wish|hope|maybe|unless|almost|wether|whether|in case|chance|paranoid|assume|worried|worry|pray|afraid|suspect|either)(?=.{0,25}(covid|corona|virus|ncov|koronavirus|sars-cov-2|covd|rona|positive))",flags=re.I)
pattern_2 = re.compile(r'(\b(do|am|were)\b\si)(?=.{0,20}(covid|corona|virus|ncov|koronavirus|sars-cov-2|covd|rona|positive))',flags=re.I)
pattern_3 = re.compile(r"(\bi\b)(?=.{0,30}(covid|corona|virus|ncov|koronavirus|sars-cov-2|covd|rona|positive))",flags=re.I)

def pattern_match(text):
    if not re.search(pattern_1,text) == None:
        return False
    elif not re.search(pattern_2,text) == None:
        return False
    elif not re.search(pattern_3,text) == None:
        return True
