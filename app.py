from flask import Flask, make_response, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import telegram
import json
from celery import Celery
import spacy
from utilities import handle_update
from tasks import save_tfidf_group_models, save_user_models

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] ='postgres://dhdbiabpoktcen:6b21775a670b9eeb8dc7ef4e12e5f87001f8c7fc224fe18b88858f862bbf1c56@ec2-107-22-7-9.compute-1.amazonaws.com:5432/d51gcce3c527k2'

db = SQLAlchemy(app)
celery = Celery(app)
celery.config_from_object('celery_settings')

global bot
global TOKEN

TOKEN = '978043287:AAEIUgZ8BlHFzC3fZ8FI_p0s5J_H1pCMVrM'
bot = telegram.Bot(token=TOKEN)
bot_user_name = "CommManagerBot"
URL = "https://comm-manager-bot.herokuapp.com/"

@app.route("/")
def home():
    return "Hello, World!"

@app.route('/set_webhook', methods=['GET', 'POST'])
def set_webhook():
    # we use the bot object to link the bot to our app which live
    # in the link provided by URL
    s = bot.set_webhook(URL + TOKEN, allowed_updates=['message', 'callback_query'])
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
        if not update.message.text == None:
            chat_id = update.message.chat.id
            msg_id = update.message.message_id
            response = handle_update(update)

            if not response == "":
                bot.sendMessage(chat_id=chat_id, text=response, reply_to_message_id=msg_id, parse_mode="Markdown")

    return 'ok'

@app.route("/group_model", methods=['POST'])
def update_group_models():
    save_tfidf_group_models.delay()
    return make_response(("new group models are being created"), 200)

@app.route("/user_model", methods=['POST'])
def update_user_models():
    save_user_models.delay()
    return make_response(("new user models are being created"), 200)


    
if __name__ == "__main__":
    app.run()