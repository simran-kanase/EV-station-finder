from geopy import distance
import webbrowser
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
import pandas as pd
from flask import Flask, render_template, redirect, url_for, request
import json
from flask_sqlalchemy import SQLAlchemy
import os





def nearChargingStations(lat, log):
    # Read the dataset
    dataset = pd.read_csv('ev-charging-stations-india.csv')

    # Check the number of rows in the dataset
    # print("Number of rows in the dataset:", len(dataset))

    # Check if there are any missing values
    # print("Number of missing values in 'lattitude':", dataset['lattitude'].isnull().sum())
    # print("Number of missing values in 'longitude':", dataset['longitude'].isnull().sum())

    # Provide default latitude and longitude values
    lat = lat
    log = log

    # Create a list to store all distances
    all_Distance = []
    data = dataset.dropna(subset=['lattitude', 'longitude'], how='all')
    # print("Number of rows in the dataset:", len(dataset))
    # print(len(data))

    nearestLocation = []

    # Iterate through the dataset and calculate distances
    for i in range(len(dataset)):
        if not pd.isnull(dataset['lattitude'][i]) and not pd.isnull(dataset['longitude'][i]):
            dist = distance.distance((lat, log), (dataset['lattitude'][i], dataset['longitude'][i])).km
            all_Distance.append(dist)
            if len(nearestLocation) == 0:
                nearestLocation.append((dataset['address'][i], dataset['name'][i], dist, dataset['lattitude'][i], dataset['longitude'][i]))
            else:
                if len(nearestLocation) <= 4:
                    for j in range(len(nearestLocation)):
                        if nearestLocation[j][2] > dist:
                            nearestLocation.append((dataset['address'][i], dataset['name'][i], dist, dataset['lattitude'][i],
                                                    dataset['longitude'][i]))
                else:
                    for j in range(len(nearestLocation)):
                        if nearestLocation[j][2] > dist and (dataset['address'][i], dataset['name'][i], dist, dataset['lattitude'][i],
                                                    dataset['longitude'][i]) not in nearestLocation:
                            nearestLocation[j] = (dataset['address'][i], dataset['name'][i], dist, dataset['lattitude'][i],
                                                    dataset['longitude'][i])

    return nearestLocation


# Locations = nearChargingStations(0,0)
# for i in Locations:
#     print(i)



app = Flask(__name__)
# create the extension
db = SQLAlchemy()
# configure the SQLite database, relative to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

# initialize the app with the extension
db.init_app(app)
app.app_context().push()

app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'


# Creating the Database


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50))
    password = db.Column(db.String(50))
    name = db.Column(db.String(50))
    address = db.Column(db.String(70))
    phone = db.Column(db.Integer)


db.create_all()

# Login Manager
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_name):
    return User.query.get(int(user_name))


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if not user:
            flash("Invalid Username!")
            print("Invalid User")
        elif password != user.password:
            flash("Invalid Password!")
            print("Invalid Password")
        else:
            login_user(user)
            print("Log In")
            return redirect(url_for('home'))

    return render_template('login.html')


@app.route('/register', methods=['GET','POST'])
def register():
    if request.method=='POST':
        username = request.form.get('username')
        password = request.form.get('password')
        name = request.form.get('name')
        address = request.form.get('address')
        phone_No = request.form.get('phone')
        newUser  = User(
            username=username,
            password=password,
            name=name,
            address=address,
            phone=phone_No
        )
        db.session.add(newUser)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register.html')

lat = 0
long = 0
@app.route('/process/<string:userinfo>', methods=['GET', 'POST'])
def process(userinfo):
    userinfo = json.loads(userinfo)
    print(f"User type :: {userinfo['values']}")
    global lat, long
    lat, long = (userinfo['values'][7:-1]).split(',')

    return redirect(url_for('location'))

@app.route('/location', methods=['GET','POST'])
def location():
    # print(lat, long)
    nearLocations = []
    if request.method == "POST":
        nearLocations = nearChargingStations(lat, long)
        if len(nearLocations)>5:
            nearLocations = nearLocations[0:5]
    return render_template('Location.html', nearLocations=nearLocations, nearLocationsLen=len(nearLocations))


@app.route('/map', methods=['GET', 'POST'])
def map():
    print("Working")
    if request.method == 'POST':
        D_lat = request.form.get('lat')
        D_long = request.form.get('long')
        webbrowser.open(f"https://www.google.com/maps/dir/{lat},{long}/{D_lat},{D_long}")
    return redirect(url_for('location'))


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/contact')
def contact():
    return render_template('contact.html')



@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))



if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # Use Render's provided port
    app.run(host='0.0.0.0', port=port)




