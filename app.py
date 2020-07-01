from flask import Flask, make_response, jsonify, request
import telegram
import json
import re
import requests
from bs4 import BeautifulSoup
from bs4.element import Comment

from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from collections import Counter 

app = Flask(__name__)

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
def clean_and_tokenize_data(data):

    # removes all html tags
    cleaner = re.compile('<.*?>')
    data = re.sub(cleaner, '', data)

    # removes all non words
    data = re.sub("[^A-Za-z]", " ", data) 

    # converts to lower case
    data = data.lower()                   

    # converts to list of words
    data = word_tokenize(data)  


    # removes all common words like 'a', 'the' etc          
    data = [ word for word in data if word not in set(stopwords.words("english"))] 

    return data

def get_keywords(link_list):

    text_in_links = ''
    for link in link_list:
        r = requests.get(link)
        if r:
            # parses the request content using html5lib parser
            soup = BeautifulSoup(r.content, 'html.parser') 
            texts = soup.findAll(text=True)
            visible_texts = filter(tag_visible, texts)  
            text_string = u" ".join(t.strip() for t in visible_texts)
            text_in_links += text_string
    
    cleaned_words_list = clean_and_tokenize_data(text_in_links)
    counter = Counter(cleaned_words_list)
    most_freq_words = counter.most_common(6)
    
    return most_freq_words

def get_response(update):
    chat_id = update.message.chat.id
    msg_id = update.message.message_id
    text = update.message.text.encode('utf-8').decode()

    link_list = get_link_list(text)
    if not link_list == []:
        keywords_tuple = get_keywords(link_list)
        words_str = 'The top keywords in the links are: '
        for keyword in keywords_tuple:
            words_str += keyword[0] + ", "
        response = words_str
    elif link_list == []:
        response = "You have not shared any links"
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
        text = update.message.text.encode('utf-8').decode()
        response = get_response(update)
        bot.sendMessage(chat_id=chat_id, text=response, reply_to_message_id=msg_id)

    return 'ok'

    
if __name__ == "__main__":
    app.run(threaded=True)