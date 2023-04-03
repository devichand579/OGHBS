from flask import Flask, render_template, Response, jsonify, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from mail import send_mail ,send_confirmation_mail,send_payment_confirmation_mail

app = Flask(__name__)
app.config['SECRET_KEY']='KGPGH@123'
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///oghbs.db'
db = SQLAlchemy(app)

curuserd = -1
checkindate = datetime.now()
checkoutdate = datetime.now()
srt = '0'
foodid = '0'
availableonly = '0'
roomid = 0
rooms = []
avail = []
days = []
urls = []
roomAvail = []
emptystatus = ""
for i in range(40):
    emptystatus+="0"


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(30))
    last_name = db.Column(db.String(30))
    email = db.Column(db.String(50))
    username = db.Column(db.String(50),unique=True)
    password = db.Column(db.String(20))
    address = db.Column(db.String(200))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    rollstd = db.Column(db.String(20),nullable=True,unique=True)
    usertype = db.Column(db.String(50))
    #image_file=db.Column(db.String(50),nullable=False)
    #doc=db.Column(db.String(50),nullable=False)
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

class Payment(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    amount=db.Column(db.Float)
    paymentid=db.Column(db.String(20))

class Cash(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    currency=db.Column(db.String(20))
    amountc=db.Column(db.Float,db.ForeignKey('payment.amount'))

class Creditcard(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(30))
    cardno=db.Column(db.String(20))
    cvv=db.Column(db.Integer)
    amountcc=db.Column(db.Float,db.ForeignKey('payment.amount'))
   

class Upi(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    upiid=db.Column(db.String(20))
    amountu=db.Column(db.Float,db.ForeignKey('payment.amount'))
    
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

@app.route('/', methods=["POST", "GET"])
def welcome():
    if request.method == "POST":
        print(request.form['username'])
        user = User.query.filter_by(username=request.form['username']).first()
        print(request.form['password'])
        if user is not None and user.password == request.form['password']:
            global currentuserid
            currentuserid = user.id
            if user.usertype =="Admin":
                return admin()
            else:
                auth = Authentication.query.filter_by(id=user.id).first()
                print(auth.val)
                if auth.val != 1:
                    return render_template('index.html',flag=auth.val)
                return render_template('calender.html')
        else:
            return render_template('index.html',flag=1)
    return render_template('index.html',flag=-1)



@app.route('/signup', methods=["POST", "GET"])
def sign_up():
    if request.method == "POST":
        new_id = User.query.count()+1
        username = request.form['username']
        password = request.form['password']
        first_name= request.form['first_name']
        last_name= request.form['last_name']
        email = request.form['email']
        address = request.form['address1']+", "+request.form['address2']+", City : "+request.form['city']+", State :"+request.form['state']        
        gender = request.form['gender']            
        age = request.form['age']     
        roll_Std = request.form['roll']
        #image_file = request.form['image']
        #doc = request.form['doc']
        usertype = request.form['role']
            
        
        checkusername = User.query.filter_by(username=request.form['username']).first()
        checkemail = User.query.filter_by(username=request.form['email']).first()
        if checkusername is None and checkemail is None:
            newUser = User(id=new_id, first_name=first_name,last_name=last_name, email=email, username=username, password=password, address=address, age=age, gender=gender, rollstd=roll_Std, usertype=usertype)
            newAuthReq = Authentication(id=new_id, val=0)
            db.session.add(newAuthReq)
            db.session.commit()
        elif checkemail is not None:
            return render_template('regform.html', flag=2)
        else:
            return render_template('regform.html', flag=0)
        # push to db
        try:
            db.session.add(newUser)
            db.session.commit()
            print("User added successfully")
            return redirect('/otp')
        except:
            print("Could not add new user to the database")
    return render_template('regform.html', flag=1)

@app.route('/otp', methods=['POST','GET'])
def check():
    if request.method =="POST":
        i=User.query.count()
        user=User.query.filter_by(id=i).first()
        otp=send_mail("OTP for registration","Enter the otp for verification",user.email)
        if otp==request.form['otp']:
            return redirect('/',flag=3)
        else:
            return render_template('otp.html',flag=1)
    return render_template('otp.html',flag=0)

    

@app.route('/admin', methods=["POST", "GET"])
def admin():
    authRequests = []
    requests = Authentication.query.filter_by(val=0)
    for req in requests:
        authRequests.append(User.query.filter_by(id=req.id).first())
    return render_template('admin.html', users=authRequests)


@app.route('/adminDates', methods=["POST", "GET"])
def adminDates():
    return render_template('adminCalendar.html')

@app.route('/adminHistory', methods=["POST", "GET"])
def adminHistory():
    bookings = Booking.query.all()
    rooms = [Rooms.query.filter_by(id=i.roomId).first() for i in bookings]
    user = [User.query.filter_by(id=i.userId).first() for i in bookings]
    cost = [TotalBookingCost(i) for i in bookings]
    return render_template('adminPrevBooking.html', bookings=bookings, user=user, rooms=rooms, prices=cost)


@app.route('/authorize/<userId>/<desc>', methods=["POST", "GET"])
def authorize(userId, desc):
    userId = int(userId)
    desc = int(desc)
    userVal = Authentication.query.filter_by(id=userId).first()
    userVal.val = desc
    db.session.commit()
    return admin()

if __name__ == '__main__':
    app.run(debug = True)

