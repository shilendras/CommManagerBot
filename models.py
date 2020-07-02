from manage import db,app

class LinkData(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64))
    user_id = db.Column(db.Integer)
    chat_id = db.Column(db.Integer)
    text = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return '<User %r>' % (self.username)