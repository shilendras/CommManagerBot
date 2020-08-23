from app import celery
from app import db
from app import tfidf_vectorizer
import pandas as pd
import numpy as np
import pickle
from models import LinkData, ChatTfidf, UserVectors

@celery.task()
def save_tfidf_group_models():

    text_query = LinkData.query.with_entities(LinkData.chat_id, LinkData.text)
    text_dataframe = pd.read_sql(text_query.statement, text_query.session.bind)
    grouped_text_dataframe = text_dataframe.groupby('chat_id')['text'].apply(list)
    for chat_id, corpus in grouped_text_dataframe.iteritems():
        tfidf_model = tfidf_vectorizer.fit(corpus)
        tfidf_pickle_string = pickle.dumps(tfidf_vectorizer)
        try:
            chat_tf_obj = ChatTfidf.query.filter_by(chat_id=chat_id).first()
            chat_tf_obj.tfidf_model = tfidf_pickle_string
        except:
            db.session.rollback()
            chat_tf_obj = ChatTfidf(chat_id=chat_id, tfidf_model=tfidf_pickle_string)
            db.session.add(chat_tf_obj)
        
        db.session.commit()


    return "ok"

@celery.task()
def save_user_models():
    text_query = LinkData.query.with_entities(LinkData.chat_id, LinkData.user_id, LinkData.firstname, LinkData.text)
    text_dataframe = pd.read_sql(text_query.statement, text_query.session.bind)
    grouped_text_dataframe = text_dataframe.groupby(['chat_id', 'user_id', 'firstname'], as_index=False)['text'].apply(list)
    for key, value in grouped_text_dataframe.iteritems():
        chat_id = key[0]
        user_id = key[1]
        firstname = key[2]
        tfidf_model_obj = ChatTfidf.query.filter_by(chat_id=chat_id).first()
        tfidf_vectorizer = pickle.loads(tfidf_model_obj.tfidf_model)
        total_user_text = " ".join(text_string for text_string in value)
        total_user_text_list = [total_user_text]
        user_tfidf_vector = tfidf_vectorizer.transform(total_user_text_list)
        user_tfidf_arrays = user_tfidf_vector.toarray()
        user_tfidf_array = user_tfidf_arrays[0]
        try:
            user_vector_obj = UserVectors.query.filter_by(chat_id=chat_id, user_id=user_id).first()
            user_vector_obj.vector = user_tfidf_array
        except:
            db.session.rollback()
            user_vector_obj = UserVectors(chat_id=chat_id, user_id=user_id, firstname=firstname, vector=user_tfidf_array)
            db.session.add(user_vector_obj)
        
        db.session.commit()
        
    return "ok"