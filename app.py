from flask import Flask, make_response, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import telegram
import json
import re
import requests
from bs4 import BeautifulSoup
from bs4.element import Comment

from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] ='postgres://dhdbiabpoktcen:6b21775a670b9eeb8dc7ef4e12e5f87001f8c7fc224fe18b88858f862bbf1c56@ec2-107-22-7-9.compute-1.amazonaws.com:5432/d51gcce3c527k2'

db = SQLAlchemy(app)

from models import LinkData

global bot
global TOKEN

TOKEN = '978043287:AAEIUgZ8BlHFzC3fZ8FI_p0s5J_H1pCMVrM'
bot = telegram.Bot(token=TOKEN)
bot_user_name = "CommManagerBot"
URL = "https://comm-manager-bot.herokuapp.com/"


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

    # removes all html tags
    cleaner = re.compile('<.*?>')
    text_string = re.sub(cleaner, '', text_string)

    # removes all non words
    text_string = re.sub("[^A-Za-z]", " ", text_string) 

    # converts to lower case
    text_string = text_string.lower()                   

    return text_string

def stop_words_and_tokenize(text_string):
    tokenized_words = word_tokenize(text_string)  
    # removes all common words like 'a', 'the' etc          
    tokenized_words = [ word for word in tokenized_words if word not in set(stopwords.words("english"))] 

    return tokenized_words


def get_text_from_links(link_list):

    final_text = ''
    for link in link_list:
        r = requests.get(link)
        if r:
            # parses the request content using html parser
            soup = BeautifulSoup(r.content, 'html.parser') 
            texts = soup.findAll(text=True)
            visible_texts = filter(tag_visible, texts)  
            text_string = u" ".join(t.strip() for t in texts)
            cleaned_text = clean_up_text(text_string)
            final_text += cleaned_text
    
    return final_text

def handle_update(update):

    chat_id = update.message.chat.id
    from_id = update.message.from_user.id
    from_username = update.message.from_user.username
    text = update.message.text.encode('utf-8').decode()

    link_list = get_link_list(text)
    if not link_list == []:
        link_text = get_text_from_links(link_list)
        link_object = LinkData(chat_id=chat_id, user_id=from_id, username=from_username, text=link_text)
        db.session.add(link_object)
        db.session.commit()
        response = ""

    elif link_list == []:
        response = ""

    return response

@app.route("/")
def home():
    return "Hello, World!"

@app.route('/set_webhook', methods=['GET', 'POST'])
def set_webhook():
    # we use the bot object to link the bot to our app which live
    # in the link provided by URL
    s = bot.setWebhook('{URL}{HOOK}'.format(URL=URL, HOOK=TOKEN))
    # something to let us know things work
    if s:
        return "webhook setup ok"
    else:
        return "webhook setup failed"

@app.route("/{}".format(TOKEN), methods=['POST'])
def respond():

    try:
        update = telegram.Update.de_json(request.get_json(force=True), bot)
    except ValueError:
        return make_response('Invalid request body', 400)
    else:
        chat_id = update.message.chat.id
        msg_id = update.message.message_id
        response = handle_update(update)

        if not response == "":
            bot.sendMessage(chat_id=chat_id, text=response, reply_to_message_id=msg_id)

    return 'ok'

    
if __name__ == "__main__":
    app.run(threaded=True)