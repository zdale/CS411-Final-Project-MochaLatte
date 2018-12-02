from flask import Flask, render_template, flash, request, url_for, redirect, session
from content_management import Hotels, Airbnbs

from wtforms import Form, BooleanField, TextField, PasswordField, SelectField, validators
from passlib.hash import sha256_crypt
from MySQLdb import escape_string as thwart

from functools import wraps

import gc
from dbconnect import connection

import datetime

HOTEL_DICT = Hotels()
AIRBNB_DICT = Airbnbs()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'redsfsfsfsfis'

class SearchForm(Form):
    searchLoc = TextField('searchLoc', [validators.Required(message="Enter a destination to begin searching.")],
                            render_kw={"placeholder": "Where are you going?"})
    capacity = SelectField('Travelers', choices = [("0", 'Number of Guest'), ("1","1"), ("2","2"), ("3","3"),
                                                    ("4", "4"), ("5", "5"), ("6", "6"),
                                                    ("7", "7"), ("8", "8"), ("9", "9"),
                                                    ("10", "10"), ("11", "11"), ("12", "12"),
                                                    ("13", "13"), ("14", "14"), ("15", "15"),
                                                    ("16", "16")])

@app.route('/', methods=["GET","POST"])
def homepage():
	try:
		session['Order'] = "priceRec"

		c, conn = connection()
		form = SearchForm(request.form)
		if request.method == "POST":
		    #Get user select order
		    if request.form["order"]:
		        if request.form["order"] == "priceRec":
		            session['Order'] = "priceRec"
		            airbnbSql = "SELECT DISTINCT * FROM airbnbs"
		            hotelSql = "SELECT DISTINCT * FROM hotels"
		        elif request.form["order"] == "priceLH":
		            session['Order'] = "priceLH"
		            airbnbSql = "SELECT DISTINCT * FROM airbnbs ORDER BY price ASC"
		            hotelSql = "SELECT DISTINCT * FROM hotels ORDER BY price1 ASC"
		        else:
		            session['Order'] = "priceHL"
		            airbnbSql = "SELECT DISTINCT * FROM airbnbs ORDER BY price DESC"
		            hotelSql = "SELECT DISTINCT * FROM hotels ORDER BY price1 DESC"

		        airbnbdata = c.execute(airbnbSql)
		        airnum = int(airbnbdata)
		        airbnbdata = c.fetchmany(airnum)

		        hoteldata = c.execute(hotelSql)
		        hotelnum = int(hoteldata)
		        hoteldata = c.fetchmany(hotelnum)
		        return render_template("search-page.html", AIRBNB=airbnbdata, AIRNUM=airnum,
		                        HOTEL=hoteldata, HOTELNUM=hotelnum, form=form, order=session['Order'])

		    if request.form["search"] == "Search"and form.validate():
			    session['Location'] = form.searchLoc.data
			    session['Capacity'] = int(form.capacity.data)

			    if session.get('logged_in') == True:
				    c.execute("INSERT INTO search_history (uid, query, time) VALUES (%s, %s, %s)",
						(session['uid'], thwart(session['Location']), datetime.datetime.now()))
				    conn.commit()
			    return redirect(url_for("searchResPage"))


		airbnbSql = "SELECT * FROM airbnbs" #TODO: improve efficiency
		airbnbdata = c.execute(airbnbSql)
		airnum = int(airbnbdata)
		airbnbdata = c.fetchmany(airnum)

		hotelSql = "SELECT * FROM hotels"
		hoteldata = c.execute(hotelSql)
		hotelnum = int(hoteldata)
		hoteldata = c.fetchmany(hotelnum)

		c.close()
		conn.close()
		gc.collect()
		return render_template("search-page.html", AIRBNB=airbnbdata, AIRNUM=airnum,
		                        HOTEL=hoteldata, HOTELNUM=hotelnum, form=form, order=session['Order'])
	except Exception as e: #TODO: need to remove after done
		return render_template("search-page.html", error = e)


@app.route('/searchRes')
def searchResPage():
	try:
		c, conn = connection()
		cap = session['Capacity']

		if cap == 0:
		    airbnbSql = "SELECT * FROM airbnbs WHERE (state = (%s) OR city = (%s))"
		    airbnbdata = c.execute(airbnbSql, (thwart(session['Location']),thwart(session['Location'])))
		else:
		    airbnbSql = "SELECT * FROM airbnbs WHERE (state = (%s) OR city = (%s)) AND capacity >= (%s)" #TODO: improve efficiency
		    airbnbdata = c.execute(airbnbSql, (thwart(session['Location']),thwart(session['Location']), cap))
		airnum = int(airbnbdata)
		airbnbdata = c.fetchmany(airnum)

		#Determine price display for hotels based on capacity
		priceType = 1 # default display price 1
		if cap != 0:
		    if cap > 2 and cap <= 4:
		        priceType = 2 # display price 2
		    elif cap > 4:
		        priceType = 3 # display both price

		hotelSql = "SELECT * FROM hotels WHERE state = (%s) OR city = (%s)"
		hoteldata = c.execute(hotelSql, (thwart(session['Location']),thwart(session['Location'])))
		hotelnum=int(hoteldata)
		hoteldata = c.fetchmany(hotelnum)

		return render_template("searchRes.html",AIRBNB=airbnbdata, AIRNUM=airnum,
				                HOTEL=hoteldata,HOTELNUM=hotelnum,
								searchLoc=session['Location'], cap=cap, priceType=priceType)


		c.close()
		conn.close()
		gc.collect()
		return redirect(url_for("homepage"))


	except Exception as e: #TODO: need to remove after done
		flash(e)
		return redirect(url_for("homepage"))


@app.route('/profile-page', methods=["GET","POST"])
def profile():
	uid = session['uid']
	email = session['email']

	c, conn = connection()
	username = c.execute("SELECT * FROM users WHERE uid = (%s)",
					(session['uid'],))
	username = c.fetchone()
	username = username[1]

	historySql = "SELECT * FROM search_history WHERE uid = (%s)"
	historydata = c.execute(historySql, (session['uid'],))
	queryCount = int(historydata)
	historydata = c.fetchall()

	if request.method == "POST":
		if request.form["clear-button"] == "Clear all history":
			deleteAllSql = "DELETE FROM search_history WHERE uid = (%s)"
			deleteAll = c.execute(deleteAllSql, (session['uid'],))
			conn.commit()
			queryCount = 0

	c.close()
	conn.close()
	gc.collect()

	return render_template("profile-page.html",
	                        HOTEL_DICT=HOTEL_DICT,
							AIRBNB_DICT=AIRBNB_DICT,
	                        username=username, uid=uid, email=email,
	                        history=historydata, queryCount=queryCount)


@app.route('/edit-profile', methods=["GET","POST"])
def editProfile():
	try:
		c, conn = connection()
		if request.method == "POST":

			c.execute("UPDATE users SET username = (%s) WHERE uid = (%s)",
				(thwart(request.form['username']), session['uid']))
			conn.commit()
			flash("Save Successfully!")
			return redirect(url_for("profile"))
		c.close()
		conn.close()
		gc.collect()
		return render_template("edit-profile.html")

	except Exception as e: #TODO: debugging purpose, delete when done
		return render_template("edit-profile.html")



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
    accept_tos = BooleanField('I accept the <a href="/tos/">Terms of Service</a> and the <a href="/privacy/">Privacy Notice</a>', [validators.Required()])


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
				session['email'] = data[3]

				c.close()
				conn.close()
				gc.collect() #need to use gc collect when conenct to database

				return redirect(url_for('homepage'))
		return render_template("register.html", form=form)

	except Exception as e: #TODO: debugging purpose, delete when done
		return (str(e))


if __name__ == "__main__":
    # app.debug = True
	app.run()
