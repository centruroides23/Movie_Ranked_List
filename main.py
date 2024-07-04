import os

from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField
from wtforms.validators import DataRequired
import requests
from config import Config

# ------------------------------------------------- APP CONFIG ------------------------------------------------------- #
app = Flask(__name__)
app.config.from_object(Config)
Bootstrap5(app)


# -------------------------------------------------- CREATE DB ------------------------------------------------------- #
class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
db.init_app(app)


class Movies(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    rating: Mapped[float] = mapped_column(Float, nullable=False)
    ranking: Mapped[int] = mapped_column(Integer)
    review: Mapped[str] = mapped_column(String(250), nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)


with app.app_context():
    db.create_all()


# -------------------------------------------------- APP FORMS ------------------------------------------------------- #
class EditForm(FlaskForm):
    rating = FloatField(label="Your Rating out of 10 (e.g., 7.4)", validators=[DataRequired()])
    review = StringField(label="Your Review", validators=[DataRequired()])
    submit = SubmitField(label="Done")


class AddForm(FlaskForm):
    movie = StringField(label="Add a Movie", validators=[DataRequired()])
    submit = SubmitField(label="Done")


# ------------------------------------------------- APP ROUTES ------------------------------------------------------- #
@app.route("/")
def home():
    result = db.session.execute(db.select(Movies).order_by(Movies.rating.desc()))
    movies = result.scalars().all()
    for i in range(len(movies)):
        movies[i].ranking = i + 1
    db.session.commit()
    return render_template("index.html",
                           movies=movies)


@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    edit_form = EditForm()
    if edit_form.validate_on_submit():
        result = db.get_or_404(Movies, id)
        result.rating = edit_form.rating.data
        result.review = edit_form.review.data
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("edit.html",
                           form=edit_form)


@app.route("/delete/<int:id>")
def delete(id):
    delete_record = db.get_or_404(Movies, id)
    db.session.delete(delete_record)
    db.session.commit()
    return redirect(url_for("home"))


@app.route("/add", methods=["GET", "POST"])
def add():
    add_form = AddForm()
    if add_form.validate_on_submit():
        params = {
            "query": add_form.movie.data,
            "api_key": os.environ.get("MOVIE_API_KEY")
        }
        response = requests.get("https://api.themoviedb.org/3/search/movie", params=params)
        response.raise_for_status()
        result = response.json()["results"]
        print(result)
        return render_template("select.html",
                               results=result)
    return render_template("add.html",
                           form=add_form)


@app.route("/new_movie/<title>/<year>/<overview>/<image>")
def new_movie(title, year, overview, image):
    new_data = Movies(
                title=title,
                year=year,
                description=overview,
                rating=0,
                ranking=0,
                review="Add entry",
                img_url="http://image.tmdb.org/t/p/w500/" + image
            )
    db.session.add(new_data)
    db.session.commit()
    result = db.session.execute(db.select(Movies.id).where(Movies.title == title))
    id = result.scalar()
    return redirect(url_for("edit",
                            id=id))


if __name__ == '__main__':
    app.run(debug=True)
