from flask import Flask, render_template, Response, jsonify, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SECRET_KEY']='KGPGH@123'
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///oghbs.db'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(30))
    last_name = db.Column(db.String(30))
    email = db.Column(db.String(50))
    username = db.Column(db.String(20),unique=True)
    password = db.Column(db.String(20))
    address = db.Column(db.String(100))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    rollstd=db.Column(db.String(20),nullable=True,unique=True)
    image_file=db.Column(db.String(20),nullable=False,default='Default.jpg')
    def __repr__(self):
        return '<Name %r>' % self.id


class GuestHouse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(100))
    description = db.Column(db.String(100))


class Rooms(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    floor = db.Column(db.Integer)
    type = db.Column(db.String(50))
    description = db.Column(db.String(100)) 
    status = db.Column(db.String(100))
    ghId = db.Column(db.Integer)
    pricePerDay = db.Column(db.Integer)
    occupancy = db.Column(db.Integer)
    ac = db.Column(db.Integer)


class FoodOptions(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pricePerDay = db.Column(db.Integer)
    type = db.Column(db.String(40))

class Amenities(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pricePerDay = db.Column(db.Integer)
    type = db.Column(db.String(40))


class BookingQueue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bookingIds = db.Column(db.String(40))


class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    userId = db.Column(db.Integer)
    roomId = db.Column(db.Integer)
    foodId = db.Column(db.Integer)
    checkindate = db.Column(db.DateTime)
    checkoutdate = db.Column(db.DateTime)
    dateOfBooking = db.Column(db.DateTime)
    confirmation = db.Column(db.Integer)
    feedback = db.Column(db.String(100))

class Authentication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    val = db.Column(db.Integer)

class payment(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    amount=db.Column(db.Float)
    paymentid=db.Column(db.String(20))

class cash(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    currency=db.Column(db.String(20))
    amountc= db.relationship('payment', backref='cash', lazy=True, uselist=False)

class creditcard(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(30))
    cardno=db.Column(db.String(20))
    cvv=db.Column(db.Integer)
    amountcc=db.relationship('payment', backref='creditcard', lazy=True, uselist=False)

class upi(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    upiid=db.Column(db.String(20))
    amountu=db.relationship('payment', backref='upi', lazy=True, uselist=False)
    
def checkAvailable(room):
    global checkindate,checkoutdate
    i=checkindate.day-datetime.now().day
    checkinindex=i
    j=checkoutdate.day-datetime.now().day
    checkoutindex=j
    if checkinindex <0 or checkoutindex<0:
        return false
    for x in room.status[checkinindex:checkoutindex+1]:
        if x=='1':
            return False
    return True

def totalbookingcost(booked):
    room = Rooms.query.filter_by(id=booked.roomid).first()
    food = Foodoptions.query.filter_by(id=booked.foodid).first()
    amenities=Amenities.query.filter_by(id=booked.amenid).first()
    dur=((booked.checkoutdate.day-booked.checkoutdate.day)+1)
    diff=booked.checkindate.day-datetime.now().day
    cost=room.priceperday*dur
    if food is not None :
        cost+=food.priceperday*days
    if amenities is not None :
        cost+=amenities.priceperday*days
    if diff>30 :
       cost=cost*0.85
    if diff>15 and diff<30 :
       cost =cost*0.9
    return 0.2*cost 
    
def updatestatus(roomid,checkindate,checkoutdate,val):
    temp=checkindate.day -datetime.now().day
    checkinindex=max(0,temp)
    temp=checkoutdate.day-datetime.now().day
    checkoutindex=temp
    room=Rooms.query.filter_by(id=roomid).first()
    newstat = room.status[0:checkinindex] +val*(checkoutindex-checkinindex+1) + room.status[checkoutindex+1:]
    room.staus = newstat
    db.session.commit()
    
def checkbooking(bookingid):
    booking = Booking.query.filter_by(id=bookingid).first()
    if booking is None:
       return False
    room = Rooms.query.filter_by(id=booking.roomid).first()
    checkindate=booking.checkindate
    checkoutdate=booking.checkoutdate
    temp=checkindate.day - datetime.now().day
    checkinindex = temp
    temp = checkoutdate.day -datetime.now().day
    checkoutindex=temp
    if checkinindex<0 or checkoutindex<0:
          return False 
    for i in room.status[checkinindex : checkoutindex+1]:
        if i=='1':
           return False
    booking.confirmation =1
    db.sesion.commit()
    updatestatus(booking.roomid,checkindate,checkoutdate,'1')
    return True
    
    
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["cache-control"]="no-cache, no-store,must-revalidate, public, max-age=0"
        response.headers["Expires"]=0
        response.headers["pragma"]="no-cache"
        return response
    
@app.route('/details', methods=['POST'])
def details():
    json=request.get_json()
    print(json)
    
    return jsonify(results="done")


if __name=='__main_':
    app.run(debug=True)