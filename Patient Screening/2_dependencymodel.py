# total number of tweets: 501427
# filis in /data_8t/LSX/preprocess/filter/positive/

import spacy #version:3.1.0  en_core_web_sm:3.1.0
import string
import glob
import tqdm 
import pandas as pd
import re
import os

def getSubsFromConjunctions(subs):
    moreSubs = []
    for sub in subs:
        # rights is a generator
        rights = list(sub.rights)
        rightDeps = {tok.lower_ for tok in rights}
        if "and" in rightDeps:
            moreSubs.extend([tok for tok in rights if tok.dep_ in SUBJECTS or tok.pos_ == "NOUN"])
            if len(moreSubs) > 0:
                moreSubs.extend(getSubsFromConjunctions(moreSubs))
    return moreSubs

def findSubs(tok):
    head = tok.head
    while head.pos_ != "VERB" and head.pos_ != "NOUN" and head.head != head:
        head = head.head
    if head.pos_ == "VERB":
        subs = [tok for tok in head.lefts if tok.dep_ == "SUB"]
        if len(subs) > 0:
            verbNegated = isNegated(head)
            subs.extend(getSubsFromConjunctions(subs))
            return subs, verbNegated
        elif head.head != head:
            return findSubs(head)
    elif head.pos_ == "NOUN":
        return [head], isNegated(tok)
    return [], False

def isNegated(tok):
    for dep in list(tok.lefts) + list(tok.rights):
        if dep.lower_ in negations:
            return True
    return False

def getAllSubs(v):
    verbNegated = isNegated(v)
    subs = [tok for tok in v.lefts if tok.dep_ in SUBJECTS and tok.pos_ != "DET"]
    if len(subs) > 0:
        subs.extend(getSubsFromConjunctions(subs))
    else:
        foundSubs, verbNegated = findSubs(v)
        subs.extend(foundSubs)
    return subs, verbNegated

def getObjsFromConjunctions(objs):
    moreObjs = []
    for obj in objs:
        # rights is a generator
        rights = list(obj.rights)
        rightDeps = {tok.lower_ for tok in rights}
        if "and" in rightDeps:
            moreObjs.extend([tok for tok in rights if tok.dep_ in OBJECTS or tok.pos_ == "NOUN"])
            if len(moreObjs) > 0:
                moreObjs.extend(getObjsFromConjunctions(moreObjs))
    return moreObjs

def getObjFromXComp(deps):
    for dep in deps:
        if dep.pos_ == "VERB" and dep.dep_ == "xcomp":
            v = dep
            rights = list(v.rights)
            objs = [tok for tok in rights if tok.dep_ in OBJECTS]
            objs.extend(getObjsFromPrepositions(rights))
            if len(objs) > 0:
                return v, objs
    return None, None

def getObjsFromPrepositions(deps):
    objs = []
    for dep in deps:
        if dep.pos_ == "ADP" or dep.dep_ == "prep":
            for tok in dep.rights:
                if tok.dep_ in OBJECTS or (tok.pos_ == "PRON" and tok.lower_ == "me") or tok.pos_ == "NOUN":
                    objs.append(tok)
                    
    return objs

def getAllObjs(v):
    # rights is a generator
    rights = list(v.rights)
    objs = [tok for tok in rights if tok.dep_ in OBJECTS or tok.pos_ == "PROPN" or tok.pos=="NOUN"]
    objs.extend(getObjsFromPrepositions(rights))
    potentialNewVerb, potentialNewObjs = getObjFromXComp(rights)
    if potentialNewVerb is not None and potentialNewObjs is not None and len(potentialNewObjs) > 0:
        objs.extend(potentialNewObjs)
        v = potentialNewVerb
    if len(objs) > 0:
        objs.extend(getObjsFromConjunctions(objs))
    return v, objs

def generate_right_adjectives(verb):
    verb_desc_tokens = []

    for tok in verb.rights:
        if tok.pos_ == "ADJ":
            verb_desc_tokens.extend(generate_right_adjectives(tok))
    
    if verb_desc_tokens:
        return " ".join([adj.lemma_ for adj in verb_desc_tokens])
    return ""

def isSubjunctive(tok):
    """
    checks if the sub-sentence did not happen
    """
    try:
        for item in tok.ancestors:
            if item.text in subj:
                return True
    except:
        pass
    return False

def find_intention_verbs(toks):
    """
    e.g. looks for 'have' in 'would have'
    """
    find_verb = False
    intentional_verbs = []
    for tok in toks:
        if find_verb:
            if tok.pos_ == "VERB":
                intentional_verbs.append(tok)
                find_verb = False
        elif tok.pos_ == "AUX" and tok.lemma_ in intentions:
            find_verb = True
    return intentional_verbs

def generate_right_adjectives(verb):
    verb_desc_tokens = []

    for tok in verb.rights:
        if tok.pos_ == "ADJ":
            verb_desc_tokens.append(tok.lemma_)
    
    if verb_desc_tokens:
        return " ".join(verb_desc_tokens)

def find_nonsubj_SVOs(tokens):
    svos = []
#     intentional_verbs = find_intention_verbs(tokens)
    intentional_verbs = intentions
    verbs = [tok for tok in tokens if tok.pos_ == "VERB" and "aux" not in tok.dep_ and tok.text not in intentional_verbs]
    for v in verbs:
        if isSubjunctive(v):
            continue
        subs, verbNegated = getAllSubs(v)
        # hopefully there are subs, if not, don't examine this verb
        if len(subs) > 0:
            v, objs = getAllObjs(v)
            for sub in subs:
                if sub.lemma_ == "it":
                    verb_adj = generate_right_adjectives(v)
                    v_lemma = v.lemma_+" "+verb_adj if verb_adj and "positive" in verb_adj else v.lemma_
                else:
                    v_lemma = v.lemma_

                if objs:
                    for obj in objs:
                        objNegated = isNegated(obj)
                        svos.append((sub.lemma_, "!"+v_lemma if verbNegated or objNegated else v_lemma, obj.lemma_))
                else:
                    svos.append((sub.lemma_, "!"+v_lemma if verbNegated else v_lemma))

    return svos

def noq(x):
    for a in astro:
        if a in x:
            x = x.replace(a,"'")
    
    x = re.sub("'.*?'", '', x)
    x = re.sub('".*?"', '', x)
    return x

def is_positive(text):
    ## for detecting as obj
    text = noq(text).replace("\n"," ").strip().replace("  ","").replace("covid","COVID").replace("ncov","NCOV")
    if not text:
        return False
    if text[-1] not in string.punctuation:
        text += "."
    
    toks = spacy_nlp(text)
    svos = find_nonsubj_SVOs(toks)
    global_words = []
    for clause in svos:
        clause = " "+" ".join(clause).lower()
        if "!" in clause:
            continue
        if "it" in clause:
            global_words.append(clause)

    for clause in svos:
        # print(clause)
        clause = " "+" ".join(clause).lower()

        if "!" in clause:
            continue

        for pk in pronoun_keywords_set:
            if pk in clause:
                for ff in first_filter:
                    if ff in clause:
                        for sf in second_filter:
                            if sf in clause:
                                return True 
                        if "positive" in " ".join(global_words):
                            return True

    return False


spacy_nlp = spacy.load('en_core_web_sm')

pronoun_keywords_set = [" I ", " i "]

SUBJECTS = ["nsubj", "nsubjpass", "csubj", "csubjpass", "agent", "expl"]
OBJECTS = ["pobj","dobj", "dative", "attr", "oprd", "advmod"]
negations = {"no", "not", "n't", "never", "none","n’t", "if","like","unless","in case","must","should","ought to","wont","in case if"}
subj = ["think","thought","plan","planned","wonder","wondered","doubt","doubted","believe","believed","wish","wished","hope","hoped","say","said"]
intentions = ["will","'d", "do", "can", "could", "should", "may", "might", "will", "would", "did"]

first_filter = [" get "," catch ", " have "," test "," recover "," diagnose "," infect "]
second_filter = "covid/corona/ncov/covid-19/covid19/coronavirus/koronavirus/sars-cov-2/ covd/virus/a virus/the virus/rona".split("/")

astro = ["‘",'"',"’","“","”"]

if not os.path.exists("positive.log"):
    with open("positive.log","w") as log:
        log.write("## start\n")

if not os.path.exists("processed_files.log"):
    with open("processed_files.log","w") as log:
        log.write("## start\n")
else:
    with open("processed_files.log","r") as log:
        processed_files = [f.split(" ")[-1] for f in log.read().split("\n")]

'------------------------------------------------------------------------------------------'
out_dir = "./positive/"

data_dir = "./extracted/" 
files = sorted(glob.glob(data_dir+"*.csv"))

filters = "stomach virus|computer virus|cold virus|a virus" 

with open("positive.log","a") as log:
    for file in tqdm.tqdm(files):
        if file in processed_files:
            continue
        print("On %s..."%file)
        file_name = file.split("/")[-1]
        pos_filename = f"{out_dir}{file_name}"

        sample_i_df = pd.read_csv(file, header=0, lineterminator='\n',  keep_default_na=False,low_memory =False, usecols = ['created_at', 'id_str', 'full_text', 'user', 'coordinates', 'place','quote_count', 'reply_count', 'retweet_count', 'favorite_count', 'geo','screen_name'])
        sample_i_df = sample_i_df[sample_i_df["full_text"].str.contains(" i ", case=False)]
        sample_i_df = sample_i_df[~sample_i_df.full_text.str.contains(filters, case=False)]
        sample_i_df["is_positive"] = sample_i_df["full_text"].apply(lambda x: is_positive(x)) 
        sample_i_df = sample_i_df.loc[lambda d: d['is_positive'] == True]
                
        sample_i_df.to_csv(pos_filename, index=False, encoding = 'utf-8-sig')
            
        message = "%i positive tweets written to %s from %s\n"%(len(sample_i_df), pos_filename, file)
        print(message)
        log.write(message+"\n")

