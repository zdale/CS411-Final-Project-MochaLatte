from flask import Flask, render_template, flash, request, url_for, redirect, session
from flask_paginate import Pagination, get_page_args
from content_management import Hotels, Airbnbs

from wtforms import Form, BooleanField, TextField, PasswordField, SelectField, FileField, SubmitField, validators
from passlib.hash import sha256_crypt
from MySQLdb import escape_string as thwart

from flask_socketio import SocketIO, emit

from functools import wraps

import gc
from dbconnect import connection

import datetime
import json
from urllib import parse

HOTEL_DICT = Hotels()
AIRBNB_DICT = Airbnbs()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'redsfsfsfsfis'
socketio = SocketIO(app)

class SearchForm(Form):
    searchLoc = TextField('searchLoc', render_kw={"placeholder": "Where are you going?"})
    capacity = SelectField('Travelers', choices = [("0", '--Guests--'), ("1","1"), ("2","2"), ("3","3"), 
                                                    ("4", "4"), ("5", "5"), ("6", "6"), 
                                                    ("7", "7"), ("8", "8"), ("9", "9"),
                                                    ("10", "10"), ("11", "11"), ("12", "12"),
                                                    ("13", "13"), ("14", "14"), ("15", "15"),
                                                    ("16", "16")])

@app.route('/')
def startpage():
    if session.get('Order'):
        session['Order'] = "priceDef"
    return redirect(url_for("homepage"))

@app.route('/home', methods=["GET","POST"])
def homepage():
	try:
		if not session.get('Order'):
		    session['Order'] = "priceDef"
		error = None
		fav_airbnb_data = None
		fav_hotel_data = None
		uid = None
		if session.get('logged_in'):
		    uid = session['uid']
		
		c, conn = connection()
		
		airOrderDict = {}
		airOrderDict["priceDef"] = "SELECT * FROM airbnbs"
		airOrderDict["priceRec"] = "SELECT DISTINCT * FROM airbnbs, (SELECT itemid, count(itemid) AS p FROM favorite WHERE type = 0 GROUP BY itemid) AS b WHERE p > 2 AND b.itemid = aid" 
		airOrderDict["priceLH"] = "SELECT DISTINCT * FROM airbnbs ORDER BY price ASC"
		airOrderDict["priceHL"] = "SELECT DISTINCT * FROM airbnbs ORDER BY price DESC"
		
		hotOrderDict = {}
		hotOrderDict["priceDef"] = "SELECT * FROM hotels"
		hotOrderDict["priceRec"] = "SELECT DISTINCT * FROM hotels, (SELECT itemid, count(itemid) AS p FROM favorite WHERE type = 1 GROUP BY itemid) AS b WHERE p > 2 AND b.itemid = hid" 
		hotOrderDict["priceLH"] = "SELECT DISTINCT * FROM hotels ORDER BY price1 ASC"
		hotOrderDict["priceHL"] = "SELECT DISTINCT * FROM hotels ORDER BY price1 DESC"
		
		airbnbSql = airOrderDict.get(session['Order'])
		airbnbdata = c.execute(airbnbSql)
		airnum = int(airbnbdata)
		airbnbdata = c.fetchmany(airnum)
		
		#pagination
		page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
		pagination = Pagination(page=page, per_page=per_page, total=airnum,
                            css_framework='bootstrap4')
		
		hotelSql = hotOrderDict.get(session['Order'])
		hoteldata = c.execute(hotelSql)
		hotelnum = int(hoteldata)
		hoteldata = c.fetchmany(hotelnum)
		
		form = SearchForm(request.form)
		
		if request.method == "POST":
		    #Get currently user's favorite list
		    if session.get('logged_in')==True:
		        favoriteHotelSql = "SELECT itemid FROM favorite WHERE uid = (%s) AND type=1"
		        fav_hotel_data = c.execute(favoriteHotelSql, (session['uid'],))
		        fav_hotel_data = c.fetchmany(int(fav_hotel_data))
		        fav_hotel_data = [x[0] for x in fav_hotel_data]
		        
		        favoriteAirbnbSql = "SELECT itemid FROM favorite WHERE uid = (%s) AND type=0"
		        fav_airbnb_data = c.execute(favoriteAirbnbSql, (session['uid'],))
		        fav_airbnb_data = c.fetchmany(int(fav_airbnb_data))
		        fav_airbnb_data = [x[0] for x in fav_airbnb_data]
		        
		    if request.form["button"] == "Search":
		        if form.searchLoc.data:
			        session['Location'] = form.searchLoc.data
			        session['Capacity'] = int(form.capacity.data)
			    
			        if session.get('logged_in') == True:
				        c.execute("INSERT INTO search_history (uid, query, time) VALUES (%s, %s, %s)",
						    (session['uid'], thwart(session['Location']), datetime.datetime.now()))
				        conn.commit()
			        session['Order'] = "priceDef"
			        return redirect(url_for("searchResPage"))
		        else:
		            error = "Please enter a destination."
		            return render_template("search-page.html", AIRBNB=airbnbdata, AIRNUM=airnum, 
		                        HOTEL=hoteldata, HOTELNUM=hotelnum, form=form, order=session['Order'], error=error,
		                        fav_airbnbs=fav_airbnb_data, fav_hotels=fav_hotel_data, uid=uid, pagination=pagination, page=page, per_page=per_page)
			    

		    else:
		        session['Order'] = request.form["button"]
		        airbnbSql = airOrderDict.get(session['Order'])
		        hotelSql = hotOrderDict.get(session['Order'])
		        
		        
		    airbnbdata = c.execute(airbnbSql)
		    airnum = int(airbnbdata)
		    airbnbdata = c.fetchmany(airnum)
		    
		    hoteldata = c.execute(hotelSql)
		    hotelnum = int(hoteldata)
		    hoteldata = c.fetchmany(hotelnum)
            	
            	
		    return render_template("search-page.html", AIRBNB=airbnbdata, AIRNUM=airnum, 
		                        HOTEL=hoteldata, HOTELNUM=hotelnum, form=form, order=session['Order'], error=error,
		                        fav_airbnbs=fav_airbnb_data, fav_hotels=fav_hotel_data, uid=uid, pagination=pagination, page=page, per_page=per_page)
		        
		if session.get('logged_in')==True:
		        favoriteHotelSql = "SELECT itemid FROM favorite WHERE uid = (%s) AND type=1"
		        fav_hotel_data = c.execute(favoriteHotelSql, (session['uid'],))
		        fav_hotel_data = c.fetchmany(int(fav_hotel_data))
		        fav_hotel_data = [x[0] for x in fav_hotel_data]
		        
		        favoriteAirbnbSql = "SELECT itemid FROM favorite WHERE uid = (%s) AND type=0"
		        fav_airbnb_data = c.execute(favoriteAirbnbSql, (session['uid'],))
		        fav_airbnb_data = c.fetchmany(int(fav_airbnb_data))
		        fav_airbnb_data = [x[0] for x in fav_airbnb_data]
		
		c.close()
		conn.close()
		gc.collect()
		return render_template("search-page.html", AIRBNB=airbnbdata, AIRNUM=airnum, 
		                        HOTEL=hoteldata, HOTELNUM=hotelnum, form=form, order=session['Order'], error=error,
		                        fav_airbnbs=fav_airbnb_data, fav_hotels=fav_hotel_data, uid=uid, pagination=pagination, page=page, per_page=per_page)
	except Exception as e: #TODO: need to remove after done
		return render_template("search-page.html", error = e)


@app.route('/searchRes', methods=["GET","POST"])
def searchResPage():
	try:
		c, conn = connection()
		cap = session['Capacity']
		error = None
		remain = cap % 4
		num4 = int(cap / 4)
		num2 = 0
		fav_airbnb_data = None
		fav_hotel_data = None
		uid = None
		if not session.get('Order'):
		    session['Order'] = "priceDef"
		
		if session.get('logged_in'):
		    uid = session['uid']
		
		#Determine price display for hotels based on capacity
		priceType = 1 # default display price 1
		hotelOrder = " ORDER BY price1"
		if cap != 0:
		    if cap > 2 and cap <= 4:
		        priceType = 2 # display price 2
		        hotelOrder = " ORDER BY price2"
		    elif cap > 4:
		        priceType = 3 # display both price
		
		airOrderDict = {}
		airOrderDict["priceDef"] = "SELECT * FROM airbnbs WHERE (state = (%s) OR city = (%s)) AND capacity >= (%s)" 
		airOrderDict["priceRec"] = "SELECT DISTINCT * FROM airbnbs, (SELECT itemid, count(itemid) AS p FROM favorite WHERE type = 0 GROUP BY itemid) AS b WHERE p > 2 AND b.itemid = aid AND (state = (%s) OR city = (%s)) AND capacity >= (%s)" 
		airOrderDict["priceLH"] = airOrderDict.get("priceDef") + " ORDER BY price ASC, capacity ASC" 
		airOrderDict["priceHL"] = airOrderDict.get("priceDef") + " ORDER BY price DESC, capacity ASC"
		
		hotOrderDict = {}
		hotOrderDict["priceDef"] = "SELECT * FROM hotels WHERE state = (%s) OR city = (%s)"
		hotOrderDict["priceRec"] = "SELECT DISTINCT * FROM hotels, (SELECT itemid, count(itemid) AS p FROM favorite WHERE type = 1 GROUP BY itemid) AS b WHERE p > 2 AND b.itemid = hid AND (state = (%s) OR city = (%s))"
		hotOrderDict["priceLH"] = hotOrderDict.get("priceDef") + hotelOrder + " ASC"
		hotOrderDict["priceHL"] = hotOrderDict.get("priceDef") + hotelOrder + " DESC"
		
		airbnbSql = airOrderDict.get(session['Order'])
		airbnbdata = c.execute(airbnbSql, (thwart(session['Location']),thwart(session['Location']), cap))
		airnum = int(airbnbdata)
		airbnbdata = c.fetchmany(airnum)
		
		hotelSql = hotOrderDict.get(session['Order'])
		hoteldata = c.execute(hotelSql, (thwart(session['Location']),thwart(session['Location'])))
		hotelnum=int(hoteldata)
		hoteldata = c.fetchmany(hotelnum)
		
		#pagination
		total = airnum
		if hotelnum > airnum:
		    total = hotelnum
		page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
		pagination = Pagination(page=page, per_page=per_page, total=total,
                            css_framework='bootstrap4')
		
		airbnbTradata = None
		hotelTradata = None
		airTranum = 0
		hotelTranum = 0
		if session.get('logged_in')==True:
		    airbnbtTraSql = "SELECT DISTINCT username, email, profileImg FROM (users NATURAL JOIN search_history) NATURAL JOIN favorite WHERE query = (%s) AND uid <> (%s)"
		  #  hotelTraSql = "SELECT DISTINCT username, email, profileImg FROM (users NATURAL JOIN search_history) NATURAL JOIN favorite WHERE query = (%s) AND type = 1 AND uid <> (%s)"
		    
		    airbnbTradata = c.execute(airbnbtTraSql, (thwart(session['Location']), (session['uid'])))
		    airTranum = int(airbnbTradata)
		    airbnbTradata = c.fetchmany(airTranum)
		    
		  #  hotelTradata = c.execute(hotelTraSql,(thwart(session['Location']), (session['uid'])))
		  #  hotelTranum=int(hotelTradata)
		  #  hotelTradata = c.fetchmany(hotelTranum)
		
		form = SearchForm(request.form)
		#Check whether user is changing displayed order
		if request.method == "POST":
		    #Get currently user's favorite list
		    if session.get('logged_in')==True:
		        favoriteHotelSql = "SELECT itemid FROM favorite WHERE uid = (%s) AND type=1"
		        fav_hotel_data = c.execute(favoriteHotelSql, (session['uid'],))
		        fav_hotel_data = c.fetchmany(int(fav_hotel_data))
		        fav_hotel_data = [x[0] for x in fav_hotel_data]
		        
		        favoriteAirbnbSql = "SELECT itemid FROM favorite WHERE uid = (%s) AND type=0"
		        fav_airbnb_data = c.execute(favoriteAirbnbSql, (session['uid'],))
		        fav_airbnb_data = c.fetchmany(int(fav_airbnb_data))
		        fav_airbnb_data = [x[0] for x in fav_airbnb_data] 
		    
		    #Search Part
		    if request.form["button"] == "Search":
		        if form.searchLoc.data:
			        session['Location'] = form.searchLoc.data
			        session['Capacity'] = int(form.capacity.data)
			    
			        if session.get('logged_in') == True:
				        c.execute("INSERT INTO search_history (uid, query, time) VALUES (%s, %s, %s)",
						    (session['uid'], thwart(session['Location']), datetime.datetime.now()))
				        conn.commit()
				        session['Order'] = "priceDef"
			        return redirect(url_for("searchResPage"))
		        else:
		            error = "Please enter a destination."
		            return render_template("searchRes.html", AIRBNB=airbnbdata, AIRNUM=airnum, 
		                        HOTEL=hoteldata, HOTELNUM=hotelnum, 
		                        searchLoc=session['Location'], cap=cap, remain=remain,num4=num4,num2=num2,priceType=priceType,
		                        form=form, order=session['Order'], error=error,
		                        fav_airbnbs=fav_airbnb_data, fav_hotels=fav_hotel_data, uid=uid, 
		                        airbnb_trav=airbnbTradata, hotel_trav=hotelTradata, airbnb_trav_num=airTranum, hotel_trav_num=hotelTranum, 
		                        pagination=pagination, page=page, per_page=per_page)
		                        
		    else:
		        session['Order'] = request.form["button"]
		        airbnbSql = airOrderDict.get(session['Order'])
		        hotelSql = hotOrderDict.get(session['Order'])
		    
		        if request.form["button"] == "priceRec":
		            airbnbdata = c.execute(airbnbSql, (thwart(session['Location']),thwart(session['Location']), cap))
		            airnum = int(airbnbdata)
		            airbnbdata = c.fetchmany(airnum)
		    
		            hoteldata = c.execute(hotelSql, (thwart(session['Location']),thwart(session['Location'])))
		            hotelnum=int(hoteldata)
		            hoteldata = c.fetchmany(hotelnum)
		    
		        elif request.form["button"] == "priceLH":
		            airbnbdata = c.execute(airbnbSql, (thwart(session['Location']),thwart(session['Location']), cap))
		            airnum = int(airbnbdata)
		            airbnbdata = c.fetchmany(airnum)
		    
		            hoteldata = c.execute(hotelSql, (thwart(session['Location']),thwart(session['Location'])))
		            hotelnum=int(hoteldata)
		            hoteldata = c.fetchmany(hotelnum)
		    
		        elif request.form["button"] == "priceHL":
		            airbnbdata = c.execute(airbnbSql, (thwart(session['Location']),thwart(session['Location']), cap))
		            airnum = int(airbnbdata)
		            airbnbdata = c.fetchmany(airnum)
		    
		            hoteldata = c.execute(hotelSql, (thwart(session['Location']),thwart(session['Location'])))
		            hotelnum=int(hoteldata)
		            hoteldata = c.fetchmany(hotelnum)
		    
		    
		    return render_template("searchRes.html",AIRBNB=airbnbdata, AIRNUM=airnum,
				                HOTEL=hoteldata,HOTELNUM=hotelnum,
								searchLoc=session['Location'], cap=cap, remain=remain,num4=num4,num2=num2,
								priceType=priceType,  form=form, order=session['Order'], error=error,
								fav_airbnbs=fav_airbnb_data, fav_hotels=fav_hotel_data, uid=uid,
								airbnb_trav=airbnbTradata, hotel_trav=hotelTradata, airbnb_trav_num=airTranum, hotel_trav_num=hotelTranum,
								pagination=pagination, page=page, per_page=per_page)
		
		if session.get('logged_in')==True:
		        favoriteHotelSql = "SELECT itemid FROM favorite WHERE uid = (%s) AND type=1"
		        fav_hotel_data = c.execute(favoriteHotelSql, (session['uid'],))
		        fav_hotel_data = c.fetchmany(int(fav_hotel_data))
		        fav_hotel_data = [x[0] for x in fav_hotel_data]
		        
		        favoriteAirbnbSql = "SELECT itemid FROM favorite WHERE uid = (%s) AND type=0"
		        fav_airbnb_data = c.execute(favoriteAirbnbSql, (session['uid'],))
		        fav_airbnb_data = c.fetchmany(int(fav_airbnb_data))
		        fav_airbnb_data = [x[0] for x in fav_airbnb_data] 
		
		c.close()
		conn.close()
		gc.collect()
		return render_template("searchRes.html",AIRBNB=airbnbdata, AIRNUM=airnum,
				                HOTEL=hoteldata,HOTELNUM=hotelnum,
								searchLoc=session['Location'], cap=cap, remain=remain,num4=num4,num2=num2,
								priceType=priceType,  form=form, order=session['Order'], error=error,
								fav_airbnbs=fav_airbnb_data, fav_hotels=fav_hotel_data, uid=uid, 
								airbnb_trav=airbnbTradata, hotel_trav=hotelTradata, airbnb_trav_num=airTranum, hotel_trav_num=hotelTranum,
								pagination=pagination, page=page, per_page=per_page)


	except Exception as e: #TODO: need to remove after done
		flash(e)
		return redirect(url_for("homepage"))


@app.route('/profile-page', methods=["GET","POST"])
def profile():
	if session.get('Order'):
	    session['Order'] = "priceDef"
	uid = session['uid']

	c, conn = connection()
	user = c.execute("SELECT * FROM users WHERE uid = (%s)",
					(session['uid'],))
	user = c.fetchone()
	username = user[1]
	userImg = user[6]
	email = user[3]
	session['email'] = email

	historySql = "SELECT * FROM search_history WHERE uid = (%s)"
	historydata = c.execute(historySql, (session['uid'],))
	queryCountHist = int(historydata)
	historydata = c.fetchall()
	
	favoriteHotelSql = "SELECT * FROM hotels WHERE hid IN ( SELECT itemid FROM favorite WHERE uid = (%s) AND type=1)"
	fav_hotel_data = c.execute(favoriteHotelSql, (session['uid'],))
	hotelCount = int(fav_hotel_data)
	fav_hotel_data = c.fetchall()
	
	favoriteAirbnbSql = "SELECT * FROM airbnbs WHERE aid IN ( SELECT itemid FROM favorite WHERE uid = (%s) AND type=0)"
	fav_airbnb_data = c.execute(favoriteAirbnbSql, (session['uid'],))
	airbnbCount = int(fav_airbnb_data)
	fav_airbnb_data = c.fetchall()

	if request.method == "POST":
		if request.form["clear-button"] == "Clear all history":
			deleteAllSql = "DELETE FROM search_history WHERE uid = (%s)"
			deleteAll = c.execute(deleteAllSql, (session['uid'],))
			conn.commit()
			queryCountHist = 0

	c.close()
	conn.close()
	gc.collect()

	return render_template("profile-page.html",
	                        HOTEL_DICT=HOTEL_DICT,
							AIRBNB_DICT=AIRBNB_DICT,
	                        username=username, uid=uid, email=email, userImg=userImg,
	                        history=historydata, queryCountHist=queryCountHist,
	                        fav_hotels=fav_hotel_data, hotelCount=hotelCount,
	                        fav_airbnbs=fav_airbnb_data, airbnbCount=airbnbCount)

@app.route('/edit-profile', methods=["GET","POST"])
def editProfile():
    try:
        c, conn = connection()
        # error = None
        
        imgSql = "SELECT * FROM pictures"
        imgdata = c.execute(imgSql)
        imgNum = int(imgdata)
        imgdata = c.fetchmany(imgNum)
        
        if request.method == "POST":
            if request.form["editProButton"] == "Save":
                if request.form['username'] and request.form['email']:
                    c.execute("UPDATE users SET username = (%s), email = (%s) WHERE uid = (%s)",
                    (thwart(request.form["username"]), thwart(request.form["email"]), session['uid']))
                    conn.commit()
                    flash("Save Successfully!")
                    return redirect(url_for("profile"))
                elif request.form['username']:
                    c.execute("UPDATE users SET username = (%s) WHERE uid = (%s)",(thwart(request.form["username"]), session['uid']))
                    conn.commit()
                    flash("Save Successfully!")
                    return redirect(url_for("profile"))
                elif request.form['email']:
                    c.execute("UPDATE users SET email = (%s) WHERE uid = (%s)",(thwart(request.form["email"]), session['uid']))
                    conn.commit()
                    flash("Save Successfully!")
                    return redirect(url_for("profile"))
                else:
                    error = "Please enter new information."
                    return render_template("edit-profile.html", error=error, IMGDATA=imgdata, IMGNUM=imgNum)
            elif request.form["editProButton"] == "BackEdit":
                return redirect(url_for("profile"))
            elif request.form["editProButton"] == "ImageSave" and request.form["proImg"]:
                error = request.form["proImg"]
                c.execute("UPDATE users SET profileImg = (%s) WHERE uid = (%s)", (thwart(request.form["proImg"]), session['uid']))
                conn.commit()
                flash("Save Successfully!")
                return redirect(url_for("profile")) 
                
            return redirect(url_for("profile")) 
        c.close()
        conn.close()
        gc.collect()
        return render_template("edit-profile.html", IMGDATA=imgdata, IMGNUM=imgNum)
    except Exception as e:
        flash("Update Unsuccessfully :(")
        return redirect(url_for("profile"))

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

@app.route('/favorite', methods=["POST"])
def favorite_action():
    try: 
        c, conn = connection()
        data = request.get_data().decode('utf8')
        vals = data.split("&")
        uid = vals[0].split("=")
        uid = uid[1]
        uid = int(uid)
        itemid = vals[1].split("=")
        itemid = itemid[1]
        itemid = int(itemid)
        h_type = vals[2].split("=")
        h_type = h_type[1]
        
        if h_type=="airbnb":
            h_type = "0"
        else:
            h_type = "1"
        
        sql_check = "SELECT * FROM favorite WHERE uid = (%s) AND itemid = (%s) AND type = (%s)"
        entry = c.execute(sql_check,( uid, itemid, h_type))
        
        if int(entry)>0:
            sql_query = "DELETE FROM favorite WHERE uid = (%s) AND itemid = (%s) AND type = (%s)"
        else:
            sql_query = "INSERT INTO favorite (uid, itemid, type) VALUES (%s, %s, %s)"
        
        c.execute(sql_query, ( uid, itemid, h_type))
        conn.commit()
        return "success"
    except Exception as e:
        return "exception" + e


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
		error = "Invalid password, try again."
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
				c.execute("INSERT INTO users (username, password, email, profileImg) VALUES (%s, %s, %s, %s)",
						(thwart(username), thwart(password), thwart(email), thwart("media/default-avatar.png")))

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