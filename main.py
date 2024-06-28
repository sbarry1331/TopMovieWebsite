from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests


app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)
# I recognize this shouldn't be uploaded, but it's not something I need to worry about.
# Also, worst case is my api_key gets rate limited
API_KEY = "98ee31cf093dfe45f50106148d94f2b4"
URL = "https://api.themoviedb.org/3/search/movie"
MOVIE_DB_IMAGE_URL = "https://image.tmdb.org/t/p/w500"
MOVIE_DETAILS_URL = "https://api.themoviedb.org/3/movie"

headers = {
            "accept": "application/json",
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI5OGVlMzFjZjA5M2RmZTQ1ZjUwMTA2MTQ4ZDk0ZjJiNCIsIm5iZiI6MTcxOTUwMTk2Ny4wMDEwMjYsInN1YiI6IjY2N2Q3YjFlYjlmOTkxNzU4ODU5MWM3NiIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.GUUoZLSNhRL1GYQHZflhp_xh5cim4zWTsCWjtRi9aU0"
        }


# CREATE DB
class Base(DeclarativeBase):
  pass


app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///movies.db"
db = SQLAlchemy(model_class=Base)
db.init_app(app)


class Movie(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(250), nullable=False)
    rating: Mapped[float] = mapped_column(Float, nullable=False)
    ranking: Mapped[int] = mapped_column(Integer, nullable=False)
    review: Mapped[str] = mapped_column(String(250), nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)


with app.app_context():
    db.create_all()


class RateMovieForm(FlaskForm):
    rating = StringField("Your Rating out of 10")
    review = StringField("Your Review")
    submit = SubmitField("Done")


class AddMovieForm(FlaskForm):
    title = StringField("Movie Title", validators=[DataRequired()])
    submit = SubmitField("Add Movie")


@app.route("/")
def home():
    result = db.session.execute(db.select(Movie).order_by(Movie.rating))
    all_movies = result.scalars().all()
    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies)-i
    db.session.commit()

    return render_template("index.html", movies=all_movies)


@app.route("/edit", methods = ["GET", "POST"])
def rate_movie():
    form = RateMovieForm()
    movie_id = request.args.get("id")
    movie = db.get_or_404(Movie, movie_id)
    if form.validate_on_submit():
        movie.rating = float(form.rating.data)
        movie.review = form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", movie=movie, form=form)

@app.route("/delete")
def delete():
    movie_id = request.args.get("id")
    movie_to_delete = db.get_or_404(Movie, movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for('home'))


@app.route("/add", methods = ["GET","POST"])
def add():
    form = AddMovieForm()
    if form.validate_on_submit():
        params = {
            "query": form.title.data
        }
        response = requests.get(URL, headers=headers, params=params)
        return render_template("select.html", response=response.json())
    return render_template("add.html", form=form)


@app.route("/find")
def find_movie():
    movie_api_id = request.args.get("id")
    # print(movie_api_id)
    if movie_api_id:
        movie_api_url = f"{MOVIE_DETAILS_URL}/{movie_api_id}"
        response = requests.get(movie_api_url, headers=headers, params={"language": "en-US"})
        data = response.json()
        new_movie = Movie(
            title=data["title"],
            year=int(data["release_date"].split("-")[0]),
            img_url=f"{MOVIE_DB_IMAGE_URL}{data['poster_path']}",
            description=data["overview"],
            rating=0,
            ranking=0, # Need to default these cause they're not-nullable
            review=''
        )
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for("rate_movie", id=new_movie.id))

if __name__ == '__main__':
    app.run(debug=True)
