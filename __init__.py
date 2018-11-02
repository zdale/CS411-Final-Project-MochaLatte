from flask import Flask, render_template, flash, request, url_for, redirect, session
from content_management import Hotels, Airbnbs

from wtforms import Form, BooleanField, TextField, PasswordField, validators
from passlib.hash import sha256_crypt
from MySQLdb import escape_string as thwart

from functools import wraps

import gc
from dbconnect import connection

HOTEL_DICT = Hotels()
AIRBNB_DICT = Airbnbs()

app = Flask(__name__)

class SearchForm(Form):
	searchLoc = TextField('searchLoc', [validators.Length(min=1, max=20)])

@app.route('/', methods=["GET","POST"])
def homepage():
	try:
		c, conn = connection()
		form = SearchForm(request.form)
		if request.method == "POST":
			session['Location'] = form.searchLoc.data
			return redirect(url_for("searchResPage"))

		airbnbSql = "SELECT * FROM airbnbs" #TODO: improve efficiency
		airbnbdata = c.execute(airbnbSql)
		airbnbdata = c.fetchmany(10)

		hotelSql = "SELECT * FROM hotels"
		hoteldata = c.execute(hotelSql)
		hoteldata = c.fetchmany(10)

		c.close()
		conn.close()
		gc.collect()
		return render_template("search-page.html", AIRBNB=airbnbdata, HOTEL=hoteldata)
	except Exception as e: #TODO: need to remove after done
		return render_template("search-page.html", error = e)


@app.route('/searchRes')
def searchResPage():
	try:
		c, conn = connection()
		airbnbSql = "SELECT * FROM airbnbs WHERE state = (%s)"
		airbnbdata = c.execute(airbnbSql, (thwart(session['Location']),))

		hotelSql = "SELECT * FROM hotels WHERE state = (%s)"
		location = ' '+ session['Location']
		hoteldata = c.execute(hotelSql, (thwart(location),))

		if int(airbnbdata) > 0:
			airbnbdata = c.fetchall()
		else:
			airbnbdata = None

		if int(hoteldata) > 0:
			hoteldata = c.fetchone()
		else:
			hoteldata = None

		return render_template("searchRes.html",AIRBNB=airbnbdata,
										HOTEL=hoteldata)


		c.close()
		conn.close()
		gc.collect()
		return redirect(url_for("homepage"))


	except Exception as e: #TODO: need to remove after done
		flash(e)
		return redirect(url_for("homepage"))


@app.route('/profile-page')
def profile():
	uid = session['uid']
	username = session['username']
	email = session['email']

	return render_template("profile-page.html",
							HOTEL_DICT=HOTEL_DICT,
							AIRBNB_DICT=AIRBNB_DICT,
							username=username, uid=uid, email=email)


#login in decorator
def login_required(f):
	@wraps(f)
	def wrap(*args, **kwargs):
		if 'logged_in' in session:
			return f(*args, **kwargs)
		else:
			flash("You need to login first")
			return redirect(url_for("loginpage"))
	return wrap


@app.route("/logout")
@login_required
def logout():
	session.clear()
	flash("You have been logged out!")
	gc.collect()
	return redirect(url_for("homepage"))



@app.route('/login-page', methods=["GET", "POST"])
def loginpage():
	error = ''
	try:
		c, conn = connection()
		if request.method == "POST":
			data = c.execute("SELECT * FROM users WHERE email = (%s)",
					(thwart(request.form['email']),))
			data = c.fetchone()
			pswd = data[2] #hashed password

			#comparing password
			if sha256_crypt.verify(request.form['password'], pswd):
				#change session info
				session['logged_in'] = True
				session['uid'] = data[0]
				session['username'] = data[1]
				session['email'] = data[3]


				flash("Your are now logged in!")
				return redirect(url_for("homepage"))

			else:
				error = "Invalid password, try again."
		c.close()
		conn.close()
		gc.collect()
		return render_template("login.html", error = error)


	except Exception as e: #TODO: need to remove after done
		error = "Invalid username, try again."
		return render_template("login.html", error = error)


class RegistrationForm(Form):
    username = TextField('Username', [validators.Length(min=4, max=20)])
    email = TextField('Email Address', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.Required(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Repeat Password')
    accept_tos = BooleanField('I accept the <a href="/tos/">Terms of Service</a> and the <a href="/privacy/">Privacy Notice</a> (updated Jan 22, 2015)', [validators.Required()])


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
						(thwart(username),))

			if int(x) > 0:
				flash("That username is already taken, please choose another")
				return render_template("register.html", form = form)

			else:
				c.execute("INSERT INTO users (username, password, email) VALUES (%s, %s, %s)",
						(thwart(username), thwart(password), thwart(email)))

				conn.commit()

				flash("Thanks for registering!")

				data = c.execute("SELECT * FROM users WHERE username = (%s)",
						(thwart(username),))
				data = c.fetchone()

				session['logged_in'] = True
				session['uid'] = data[0]
				session['username'] = data[1]
				session['email'] = data[3]

				c.close()
				conn.close()
				gc.collect() #need to use gc collect when conenct to database

				return redirect(url_for('homepage'))
		return render_template("register.html", form=form)

	except Exception as e: #TODO: debugging purpose, delete when done
		return (str(e))


if __name__ == "__main__":
	app.secret_key = 'mocha latte'

	app.run()
