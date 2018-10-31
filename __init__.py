from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def homepage():
	return render_template("index.html")


@app.route('/profile-page')
def loginpage():
	return render_template("profile-page.html")

if __name__ == "__main__":
	app.run()