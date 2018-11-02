from flask import Flask, render_template, flash, request, url_for, redirect, session
from content_management import Hotels, Airbnbs

from wtforms import Form, BooleanField, TextField, PasswordField, validators
from passlib.hash import sha256_crypt
from MySQLdb import escape_string as thwart
import gc
from dbconnect import connection

HOTEL_DICT = Hotels()
AIRBNB_DICT = Airbnbs()

app = Flask(__name__)

@app.route('/')
def homepage():
	return render_template("search-page.html", HOTEL_DICT=HOTEL_DICT, AIRBNB_DICT=AIRBNB_DICT)


@app.route('/profile-page')
def profilepage():
	return render_template("profile-page.html")


@app.route('/login-page', methods=["GET", "POST"])
def loginpage():
	#error = None
	try:
		if request.method == "POST":
			#Get data from html form
			attempted_username = request.form['username']
			attempted_password = request.form['password']

			#TODO: delete afterward
			flash(attempted_username)
			flash(attempted_password)

			if attempted_username == "admin" and attempted_password == "password":
				return redirect(url_for("homepage"))
			else:
				error = "Invalid credentials. Try Again."

		return render_template("login.html")


	except Exception as e: #TODO: need to remove after done
		flash(e)
		return render_template("login.html")


class RegistrationForm(Form):
	username = TextField('Username', [validators.Length(min=4, max=20)])
	email = TextField('Email Address', [validators.Length(min=6, max=50)])
	password = PasswordField('Password', [validators.Required(),
											validators.EqualTo('confirm', message="Passwords must match")])
	confirm = PasswordField('Repeat Password')

	accept_tos = BooleanField('I accept the <a href="/tos/">Terms of Service</a> and the <a href="/privacy/">Privacy Notice</a> (updated Nov 1, 2018 )', [validators.Required()])


@app.route('/register-page', methods=["GET", "POST"])
def registerpage():
	try:
		form = RegistrationForm(request.form)

		if request.method == "POST" and form.validate():
			username = form.username.data
			email = form.email.data
			password = sha256_crypt.encrypt((str(form.password.data)))
			c, conn = connection()

			x = c.execute("SELECT * FROM users WHERE username = (%s)",
						(thwart(username)))

			if int(len(x)) > 0:
				flash("That username is already taken, please choose another")
				return render_template("register.html", form = form)

			else:
				c.execute("INSERT INTO users (username, password, email) VALUES (%s, %s, %s)",
						(thatwart(username), thatwart(password), thatwart(email)))

				conn.commit()

				flash("Thanks for registering!")

				c.close()
				conn.close()
				gc.collect() #need to use gc collect when conenct to database

				session['logged_in'] = True
				session['username'] = username

				return redirect(url_for('homepage'))
		return render_template("register.html", form=form)

	except Exception as e: #TODO: debugging purpose, delete when done
		return (str(e))


if __name__ == "__main__":
	app.run()
