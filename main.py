from flask import Flask, make_response, jsonify, request
import telegram
import json

app = Flask(__name__)

global bot
global TOKEN

TOKEN = '978043287:AAEIUgZ8BlHFzC3fZ8FI_p0s5J_H1pCMVrM'
bot = telegram.Bot(token=TOKEN)
bot_user_name = "@CommManagerBot"
URL = "https://comm-manager-bot.herokuapp.com/"


def get_response(text):
    response = "Thank you for sending me {}".format(text)
    return response

@app.route("/")
def home():
    return "Hello, World!"

@app.route('/setwebhook', methods=['GET', 'POST'])
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
        print("got text message :", text)
        response = get_response(text)
        bot.sendMessage(chat_id=chat_id, text=response, reply_to_message_id=msg_id)

    return 'ok'

    
if __name__ == "__main__":
    app.run(threaded=True)