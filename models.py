from manage import db,app
from sqlalchemy.dialects import postgresql

class LinkData(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64))
    user_id = db.Column(db.Integer)
    chat_id = db.Column(db.Integer)
    text = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return '<User %r>' % (self.username)

class ChatTfidf(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer)
    tfidf_model = db.Column(db.PickleType, nullable=True)

    def __repr__(self):
        return '<Chat id %r>' % (self.chat_id)

class UserVectors(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer)
    user_id = db.Column(db.Integer)
    vector = db.Column(db.ARRAY(db.Float), default=dict)


