from flask import Flask, render_template

from content_management import Hotels, Airbnbs

HOTEL_DICT = Hotels()
AIRBNB_DICT = Airbnbs()

app = Flask(__name__)

@app.route('/')
def homepage():
	return render_template("search-page.html", HOTEL_DICT=HOTEL_DICT, AIRBNB_DICT=AIRBNB_DICT)


@app.route('/profile-page')
def loginpage():
	return render_template("profile-page.html")

if __name__ == "__main__":
	app.run()