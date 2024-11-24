from app.extensions import db

class Ratings(db.Model):
    id = db.Column(db.BigInteger, primary_key=True)
    userId = db.Column(db.BigInteger, nullable=False, index=True)
    movieId = db.Column(db.BigInteger, nullable=False, index=True)
    rating = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"<Ratings(id={self.id}, userId={self.userId}, movieId={self.movieId}, rating={self.rating}>"