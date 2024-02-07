from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from dotenv import load_dotenv
import requests
import os

load_dotenv()

API_KEY = os.environ.get('API_KEY')
MOVIE_DB_IMAGE_URL = 'https://image.tmdb.org/t/p/w500'

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)


# CREATE DB
class Base(DeclarativeBase):
    pass


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movies-collection.db'

db = SQLAlchemy(model_class=Base)
db.init_app(app)


class Movie(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(250), nullable=False)
    rating: Mapped[float] = mapped_column(Float, nullable=True)
    ranking: Mapped[int] = mapped_column(Integer, nullable=True)
    review: Mapped[str] = mapped_column(String(250), nullable=True)
    img_url: Mapped[str] = mapped_column(String, nullable=False)


with app.app_context():
    db.create_all()


# CREATE TABLE

# with app.app_context():
#     new_movie = Movie(
#         title="Avatar The Way of Water",
#         year=2022,
#         description="Set more than a decade after the events of the first film, learn the story of the Sully family
#         (Jake, Neytiri, and their kids), the trouble that follows them, the lengths they go to keep each other safe,
#         the battles they fight to stay alive, and the tragedies they endure.",
#         rating=7.3,
#         ranking=9,
#         review="I liked the water.",
#         img_url="https://image.tmdb.org/t/p/w500/t6HIqrRAclMCA60NsSmeqe9RmNV.jpg"
#     )
#     db.session.add(new_movie)
#     db.session.commit()

# CREATE FORM

class UpdateMovie(FlaskForm):
    rating = StringField('Your Rating Out of 10 e.g. 7.5', validators=[DataRequired()])
    review = StringField('Your Review', validators=[DataRequired()])
    submit = SubmitField('Done')


class AddMovie(FlaskForm):
    movie_title = StringField('Movie Title', validators=[DataRequired()])
    submit = SubmitField('Add Movie')


# SEARCH API MOVIE

api_href = 'https://api.themoviedb.org/3/search/movie'
headers = {
    'Authorization': f'Bearer {API_KEY}'
}


@app.route("/")
def home():
    with app.app_context():
        result = db.session.execute(db.select(Movie).order_by(Movie.rating))
        all_movies = result.scalars().all()

        for i in range(len(all_movies)):
            all_movies[i].ranking = len(all_movies) - i
        db.session.commit()
        return render_template("index.html", movies=all_movies)


@app.route('/delete')
def delete():
    movie_id = request.args.get('id')
    select_movie = db.get_or_404(Movie, movie_id)
    db.session.delete(select_movie)
    db.session.commit()
    return redirect(url_for('home'))


@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        params = {
            'query': request.form['movie_title']
        }
        response = requests.get(url=api_href, headers=headers, params=params).json()
        return render_template('select.html', movies=response)
    form = AddMovie()
    return render_template('add.html', form=form)


@app.route('/add_movie')
def add_movie():
    movie_id = request.args.get('id')
    response = requests.get(url=f'https://api.themoviedb.org/3/movie/{movie_id}', headers=headers).json()
    with app.app_context():
        new_movie = Movie(title=response['original_title'],
                          description=response['overview'],
                          img_url=f"{MOVIE_DB_IMAGE_URL}{response['poster_path']}",
                          year=response['release_date'].split('-')[0],
                          rating=0,
                          ranking=0,
                          review='None'
                          )
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for('update', id=new_movie.id))


@app.route('/update', methods=['GET', 'POST'])
def update():
    form = UpdateMovie()
    if request.method == 'POST' and form.validate_on_submit():
        movie_id = request.args.get('id')
        movie_to_update = db.get_or_404(Movie, movie_id)
        movie_to_update.rating = request.form['rating']
        movie_to_update.review = request.form['review']
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('edit.html', form=form)


if __name__ == '__main__':
    app.run(debug=True)
