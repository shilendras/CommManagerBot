import re
import requests
from bs4 import BeautifulSoup
from bs4.element import Comment
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
import numpy as np
import pickle
import spacy
from app import tfidf_vectorizer, db
from models import LinkData, ChatTfidf, UserVectors

lemmatizer = spacy.load('en_core_web_sm', disable=['parser', 'ner'])
stopwords_english = set(stopwords.words("english"))

def my_tokenizer(text_string):
    tokens = lemmatizer(text_string)
    return([token.lemma_ for token in tokens])

tfidf_vectorizer = TfidfVectorizer(ngram_range = (1,1), max_features=1000, tokenizer = my_tokenizer)

def get_link_list(text):
    link_list = re.findall(r'(https?://\S+)', text)
    return link_list

def tag_visible(element):
    if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
        return False
    if isinstance(element, Comment):
        return False
    return True

# function to clean the scrapped threat data and return a string 
def clean_up_text(text_string):

    global stopwords_english

    # removes all html tags
    cleaner = re.compile('<.*?>')
    text_string = re.sub(cleaner, '', text_string)

    # removes all non words
    text_string = re.sub("[^A-Za-z]", " ", text_string) 

    # converts to lower case
    text_string = text_string.lower()

    tokenized_words = word_tokenize(text_string)  
    # removes all common words like 'a', 'the' etc          
    tokenized_words = [ word for word in tokenized_words if word not in stopwords_english]

    text_string = " ".join(word for word in tokenized_words)                    

    return text_string


def get_text_from_links(link_list):

    final_text = ''
    for link in link_list:
        r = requests.get(link)
        if r:
            # parses the request content using html parser
            soup = BeautifulSoup(r.content, 'html.parser') 
            # finds all text in webpage
            texts = soup.findAll(text=True)
            #filters out non visible text
            visible_texts = filter(tag_visible, texts)  
            text_string = u" ".join(t.strip() for t in visible_texts)
            #clean up text by removing tags and non words
            cleaned_text = clean_up_text(text_string)
            final_text += cleaned_text
    
    return final_text

def isQuery(text):
    ''' 
    description: Takes in a text string and return true if it is a query.
    args: input text string
    returns: boolean
    '''
    wh_words = ['what', 'when', 'why', 'how']
    words = text.split()
    words = [word.lower() for word in words]
    print(words)

    if re.match(r'.*\?.*', text):
        print("Entered ? match")
        return True
    elif bool([word for word in words if word in wh_words]):
        print("Entered wh match")
        return True
    
    return False


def handle_update(update):

    chat_id = update.message.chat.id
    from_id = update.message.from_user.id
    from_username = update.message.from_user.username
    from_firstname = update.message.from_user.first_name
    text = update.message.text.encode('utf-8').decode()

    link_list = get_link_list(text)
    if not link_list == []:
        link_text = get_text_from_links(link_list)
        link_object = LinkData(chat_id=chat_id, user_id=from_id, username=from_username, firstname=from_firstname, text=link_text)
        db.session.add(link_object)
        db.session.commit()

        response = ""

    elif link_list == []:
        isQuestion = isQuery(text)
        if isQuestion:
            tfidf_model_obj = ChatTfidf.query.filter_by(chat_id=chat_id).first()
            tfidf_vectorizer = pickle.loads(tfidf_model_obj.tfidf_model)
            cleaned_query_string = clean_up_text(text)
            query_string_list = [cleaned_query_string]
            query_tfidf_vector = tfidf_vectorizer.transform(query_string_list)
            query_tfidf_array = query_tfidf_vector.toarray()[0]
            
            user_vector_query = UserVectors.query.filter_by(chat_id=chat_id).with_entities(UserVectors.chat_id, UserVectors.user_id, UserVectors.firstname, UserVectors.vector)
            user_vector_dataframe = pd.read_sql(user_vector_query.statement, user_vector_query.session.bind)
            user_vectors_list = user_vector_dataframe['vector'].to_list()

            new_user_vectors_list = []
            for user_vector_list in user_vectors_list:
                user_vector_array = np.array(user_vector_list, dtype='float')
                new_user_vectors_list.append(user_vector_array)

            user_vectors_array = np.stack(new_user_vectors_list)
            user_id_list = user_vector_dataframe['user_id'].to_list()
            user_firstname_list = user_vector_dataframe['firstname'].to_list()

            cosine_similarity_matrix = cosine_similarity(user_vectors_array, query_tfidf_array.reshape(1, -1))
            cosine_similarity_list = [value for sublist in cosine_similarity_matrix for value in sublist]
            top_index = np.argsort(cosine_similarity_list)[-1]
            top_similarity_value = cosine_similarity_list[top_index]
            top_user_id = user_id_list[top_index]
            top_user_name = user_firstname_list[top_index]

            response = "[{}](tg://user?id={}) might be able to answer your question with a confidence of {}".format(top_user_name, top_user_id, top_similarity_value)
        else:
            response = ""

    return response