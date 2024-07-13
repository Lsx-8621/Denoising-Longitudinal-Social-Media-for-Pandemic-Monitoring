# total number of tweets: 10,042,382
# filis in /data_8t/LSX/preprocess/filter/extracted/

import re
import ast
import glob
import tqdm  
import numpy as np
import pandas as pd
import gc
import os

def extract_screenname_from_user(x):
    if not x:
        return ""
    result = re.search("screen_name\': \'(.*?)\'", x)
    if result:
        return result.group(1).strip()
    return ""

### Create logs

## create a log file to store the amount of tweets extracted from each file
if not os.path.exists("tweet_amount.log"):
    with open("tweet_amount.log","w") as file:
        file.write("## Start \n")

## create a log to keep track of which files we've processed
if not os.path.exists("processed_files.log"):
    with open("processed_files.log","w") as file:
        file.write("## Start \n")
    processed_files = []
else:  ## if exists, read it
    with open("processed_files.log","r") as log:
        log.seek(0)
        processed_files = log.read().split("\n")


altered_input_dir = "cleaned_raw/"  ## we'll do a filtering out of columns we don't need, and store the filtered data in a new dir 
out_dir = "extracted/" ## where to store outputs?

os.makedirs(out_dir, exist_ok=True)
# os.makedirs(altered_input_dir, exist_ok=True)


verbs = "get/got/have/had/diagnose/diagnosed/diagnose with/diagnosed with/catch/caught by/infected by".split("/")
nouns = "covid/corona/ncov/covid-19/covid19/coronavirus/koronavirus/sars-cov-2/covd/virus/a virus/the virus".split("/")
keys = []
for v in verbs:
    for n in nouns:
        keys.append(v.strip(" ")+" "+n.strip(" "))


passive_verbs = "positive/identified".split("/")
for n in nouns:
    for v in passive_verbs:
        keys.append(n.strip(" ")+" "+v.strip(" "))


rest = "was positive/were positive/test positive/tested positive/identified by test/recognized by test".split("/")
keys.extend(rest)
keys = "|".join(keys)

# data_dir = "/data1/COVIDTweets/21October_22April/" 
data_dir = "/data1/COVIDTweets/" 
files = sorted(glob.glob(data_dir+"*.csv"))
with open("processed_files.log","a") as processed_log:
    with open("tweet_amount.log","a") as amount_log:
        for file in tqdm.tqdm(files):
            if file in processed_files:
                continue
            print("On file "+file)
            df = pd.read_csv(file, lineterminator='\n', low_memory=False).replace(np.nan, "").astype(str).drop_duplicates()
            raw_len = len(df)
            ## filter out columns we don't use
            df = df[['created_at', 'id_str', 'full_text', 'user', 'coordinates', 'place','quote_count', 'reply_count', 'retweet_count', 'favorite_count', 'geo']].drop_duplicates()
            df["screen_name"] = df.user.apply(lambda x: extract_screenname_from_user(x))  
            
            # df.to_csv(altered_input_dir+file.split("/")[-1], index=False)
            df.full_text = df.full_text.str.replace(r"http\S+", '')
            # keywords match
            df = df[df["full_text"].str.contains(keys, case=False)].drop_duplicates()  
            df.to_csv(out_dir+file.split("/")[-1], index=False)
            n_user = len(df.screen_name.unique())
        
            message = "%s | %i tweets extracted out of %i tweets; %i unique users\n"%(file, len(df), raw_len, n_user)
            
            print(message)
            amount_log.write(message)
            processed_log.write(file+"\n")
            del df



