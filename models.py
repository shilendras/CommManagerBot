from manage import db,app

class UserData(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    # username = db.Column(db.String(64), index=True, unique=True)
    # user_id = db.Column(db.Integer, index=True, unique=True)
    chat_id = db.Column(db.Text, index=True, unique=True)
    keywords = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return '<User %r>' % (self.username)