from app.extensions import db

class Movies(db.Model):
    __tablename__ = "movies"
    movieId = db.Column(db.BigInteger, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    genres = db.Column(db.String(200), nullable=False)
    release_year = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"<Movies(movieId={self.movieId}, title={self.title}, genres={self.genres}>"