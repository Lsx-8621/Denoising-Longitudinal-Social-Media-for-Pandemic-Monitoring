# remove organization accounts

import json
import pandas as pd 

# Download the user's image from the Tweet JSON Object
from m3inference import M3Twitter

m3twitter=M3Twitter(cache_dir="/home/m3/cache") #Change the cache_dir parameter to control where profile images are downloaded
m3twitter.transform_jsonl(input_file="/data/frame.json",output_file="/data/m3_input.jsonl")


from m3inference import M3Inference

# If image information is missing, set use_full_model=False
m3 = M3Inference() 
#the prediction for each user's gender, age and organization
pred = m3.infer('m3_input.jsonl') 
