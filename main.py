from flask import Flask, render_template, Response, jsonify, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import string
from mail import send_mail ,send_confirmation_mail

app = Flask(__name__)
app.config['SECRET_KEY']='KGPGH@123'
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///oghbs.db'
db = SQLAlchemy(app)

curuserid = -1
checkindate = datetime.now()
checkoutdate = datetime.now()
srt = '0'
foodId = '0'
amenitiesId='0'
availableOnly = '0'
roomid = 0
bookid=0
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
    firstname = db.Column(db.String(30))
    lastname = db.Column(db.String(30))
    email = db.Column(db.String(50))
    username = db.Column(db.String(50),unique=True)
    password = db.Column(db.String(20))
    address = db.Column(db.String(200))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    rollstd = db.Column(db.String(20),nullable=True,unique=True)
    usertype = db.Column(db.String(50))
    def __repr__(self):
        return '<Name %r>' % self.id


class GuestHouse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(100))
    description = db.Column(db.String(100))


class Rooms(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    floor = db.Column(db.Integer)
    roomtype = db.Column(db.String(50))
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
    amenitiesId = db.Column(db.Integer)
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
    amountc=db.Column(db.Float,db.ForeignKey('payment.amount'))

class Creditcard(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(30))
    cardno=db.Column(db.String(20))
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
        return False
    for x in room.status[checkinindex:checkoutindex+1]:
        if x=='1':
            return False
    return True

def totalbookingcost(booked):
    room = Rooms.query.filter_by(id=booked.roomid).first()
    food = FoodOptions.query.filter_by(id=booked.foodid).first()
    amenities=Amenities.query.filter_by(id=booked.amenitiesId).first()
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
    

def AddBaseAdmin():
    st='0'
    for i in range(30):
        st=st+'0'
    
    rooms = [Rooms(id=1, floor=0, roomtype="D/B AC Rooms", description="Double Bed", status=st, ghId=1, pricePerDay=1000, occupancy=2, ac=1),
                Rooms(id=2, floor=0, roomtype="D/B NON AC Rooms", description="Double Bed", status=st, ghId=1, pricePerDay=800, occupancy=2, ac=0),
                Rooms(id=3, floor=1, roomtype="Suite Rooms", description="Single Bed", status=st, ghId=1, pricePerDay=2000, occupancy=2, ac=0),
                Rooms(id=4, floor=2, roomtype="Meeting Room", description="for meeting", status=st, ghId=1, pricePerDay=5000, occupancy=10, ac=1),
                Rooms(id=5, floor=0, roomtype="D/B AC Rooms", description="Double Bed", status=st, ghId=2, pricePerDay=600, occupancy=3, ac=1),
                Rooms(id=6, floor=0, roomtype="D/B Non AC Rooms", description="Double Bed", status=st, ghId=2, pricePerDay=400, occupancy=3, ac=0),
                Rooms(id=7, floor=2, roomtype="Dormitory Beds AC", description="Single Bed", status=st, ghId=2, pricePerDay=250, occupancy=1, ac=1)]

    for i in rooms:
        db.session.add(i)
        db.session.commit()

    houses = [GuestHouse(id=1, address="IIT Kharagpur, Kharagpur 721302", description="Technology Guest House"),
                GuestHouse(id=2, address="IIT Kharagpur, Kharagpur 721302", description="Visveswaraya Guest House"),
                GuestHouse(id=3, address="HC Block, Sector-III Salt Lake City Kolkata-700106", description="Kolkata Guest House")]

    for i in houses:
        db.session.add(i)
        db.session.commit()

    foods = [FoodOptions(id=0, pricePerDay=0, type='none'),
                FoodOptions(id=1, pricePerDay=200, type='North Indian Veg'),
                FoodOptions(id=2, pricePerDay=300, type='North Indian Non-Veg'),
                FoodOptions(id=3, pricePerDay=250, type='South Indian Veg'),
                FoodOptions(id=4, pricePerDay=350, type='South Indian Non-Veg'),
                FoodOptions(id=5, pricePerDay=300, type='Chinese'),
                FoodOptions(id=6, pricePerDay=450, type='Italian'),
                FoodOptions(id=7, pricePerDay=400, type='Continental')]

    for i in foods:
        db.session.add(i)
        db.session.commit()

    amenities = [Amenities(id=0,pricePerDay=0, type="none"),
                Amenities(id=1,pricePerDay=200, type="Gym"),
                Amenities(id=2,pricePerDay=200, type="Swimming Pool"),
                Amenities(id=3,pricePerDay=100, type="Library"),
                Amenities(id=4,pricePerDay=100, type="Laundry"),
                Amenities(id=5, pricePerDay=400,type="Movie Hall"),
                Amenities(id=6, pricePerDay=800,type="Bar")]

    for i in amenities:
        db.session.add(i)
        db.session.commit()
    admin = User(id=0, firstname="devichand",lastname="budagam", email="devichand579@gmail.com",username="devichand", password="Devichand@123", address="Bhadrachalam , Telangana", age=19, gender="Male", rollstd="21CS30012",usertype="Admin")
    val=Authentication(id=0,val=1)
    db.session.add(admin)
    db.session.add(val)
    db.session.commit()


if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["cache-control"]="no-cache, no-store,must-revalidate, public, max-age=0"
        response.headers["Expires"]=0
        response.headers["pragma"]="no-cache"
        return response

@app.before_first_request
def create_tables():
     db.drop_all()
     db.create_all()
     AddBaseAdmin()
     

@app.route('/', methods=["POST", "GET"])
def welcome():
    if request.method == "POST":
        print(request.form['username'])
        user = User.query.filter_by(username=request.form['username']).first()
        print(request.form['password'])
        if user is not None and user.password == request.form['password']:
            global currentuserid,currentusertype
            currentuserid = user.id
            currentusertype = user.usertype
            if user.usertype =="Admin":
                auth = Authentication.query.filter_by(id=user.id).first()
                print(auth.val)
                if auth.val != 1:
                    return render_template('index.html',flag=auth.val)
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
    global otp
    if request.method == "POST":
        newid = User.query.count()
        username = request.form['username']
        password = request.form['password']
        firstname= request.form['first_name']
        lastname= request.form['last_name']
        email = request.form['email']
        address = request.form['address1']+", "+request.form['address2']+", City : "+request.form['city']+", State :"+request.form['state']        
        gender = request.form['gender']            
        age = request.form['age']    
        rollStd = request.form['roll']
        usertype = request.form['role']
            
        
        checkusername = User.query.filter_by(username=request.form['username']).first()
        if checkusername is None:
            newUser = User(id=newid, firstname=firstname,lastname=lastname, email=email, username=username, password=password, address=address, age=age, gender=gender, rollstd=rollStd, usertype=usertype)
            newAuthReq = Authentication(id=newid, val=0)
            db.session.add(newAuthReq)
            db.session.commit()
        else:
            return render_template('regform.html', flag=0)
        # push to db
        try:
            db.session.add(newUser)
            db.session.commit()
            print("User added successfully")
            i=User.query.count()-1
            user=User.query.filter_by(id=i).first()
            otp=send_mail("OTP for registration","Enter the otp for verification",user.email)
            return redirect('/otp')
        except:
            print("Could not add new user to the database")
    return render_template('regform.html', flag=1)


@app.route('/otp', methods=['POST','GET'])
def check():
    if request.method =="POST":
        i=User.query.count()-1
        newAuthReq = Authentication.query.filter_by(id=i).first()
        user=User.query.filter_by(id=i).first()
        if otp==int(request.form['otp']):
            return render_template('index.html',flag=3)
        else:
            db.session.delete(user)
            db.session.delete(newAuthReq)
            print("User deleted successfully")
            db.session.commit()
            return render_template('index.html',flag=4)
    return render_template('otp.html')

    

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
    cost = [totalbookingcost(i) for i in bookings]
    return render_template('adminPrevBooking.html', bookings=bookings, user=user, rooms=rooms, prices=cost)


@app.route('/authorize/<userId>/<desc>', methods=["POST", "GET"])
def authorize(userId, desc):
    userId = int(userId)
    desc = int(desc)
    userVal = Authentication.query.filter_by(id=userId).first()
    userVal.val = desc
    db.session.commit()
    return admin()


@app.route('/rooms', methods=["POST", "GET"])
def show_rooms():
    global flag1
    global checkInDate
    global checkOutDate
    global srt
    global foodId
    global amenitiesId
    global availableOnly
    global rooms
    global avail
    global days
    global urls
    global roomAvail
    flag1=0
    if 'availableonly' in request.form:
        print("checking availability")
        if request.form['availableonly'] == '1':
            availableOnly = '1'
            rooms = [i for i in rooms if checkAvailable(i)]
        else:
            availableOnly = '0'
            rooms = Rooms.query.all()

    elif 'srt' in request.form:
        print("sorting")
        if request.form['srt'] == '0':
            srt = '0'
            rooms.sort(key=lambda x: x.pricePerDay)
        else:
            srt = '1'
            rooms.sort(key=lambda x: x.pricePerDay, reverse=True)

    if 'foodId' in request.form:
        print("adding food")

        for i in rooms:
            temp = Rooms.query.filter_by(id=i.id).first()
            i.pricePerDay = temp.pricePerDay
        foodId = request.form['foodId']

        idx = int(foodId)
        foodItem = FoodOptions.query.filter_by(id=idx).first()
        if foodItem is not None:
            for i in rooms:
                i.pricePerDay += foodItem.pricePerDay
                flag1=1
    
    elif 'amenitiesId' in request.form:
        print("adding amenities")
 
        if flag1==0:
            for i in rooms:
                temp = Rooms.query.filter_by(id=i.id).first()
                i.pricePerDay = temp.pricePerDay
        amenitiesId = request.form['foodId']

        idx = int(amenitiesId)
        amenity = Amenities.query.filter_by(id=idx).first()
        if amenity is not None:
            for i in rooms:
                i.pricePerDay += amenity.pricePerDay
    else:
        print("booking1")
        if 'checkintime' in request.form:
            checkindate = datetime.strptime(request.form['checkintime'], '%Y-%m-%d')
            checkoutdate = datetime.strptime(request.form['checkouttime'], '%Y-%m-%d')
            checkInDate = checkindate
            checkOutDate = checkoutdate
            if datetime.now() <= checkInDate <= checkOutDate and (checkOutDate-datetime.now()).days < 100:
                pass
            else:
                if currentusertype== "Admin":
                    return render_template('adminCalendar.html', flag=0)
                return render_template('calender.html', flag=0)
        print("booking2")
        print(checkInDate)
        print(checkOutDate)
        flag1=0
        if availableOnly == '1':
            rooms = [i for i in rooms if checkAvailable(i)]
        else:
            rooms = Rooms.query.all()
        if srt == '0':
            rooms.sort(key=lambda x: x.pricePerDay)
        else:
            rooms.sort(key=lambda x: x.pricePerDay, reverse=True)
        if foodId != '0':
            for i in rooms:
                temp = Rooms.query.filter_by(id=i.id).first()
                i.pricePerDay = temp.pricePerDay
            idx = int(foodId)
            foodItem = FoodOptions.query.filter_by(id=idx).first()
            if foodItem is not None:
                for i in rooms:
                    i.pricePerDay += foodItem.pricePerDay
                    flag1=1
        if amenitiesId != '0':
            if flag1==0:
                for i in rooms:
                    temp = Rooms.query.filter_by(id=i.id).first()
                    i.pricePerDay = temp.pricePerDay
            idx = int(amenitiesId)
            amenity = Amenities.query.filter_by(id=idx).first()
            if foodItem is not None:
                for i in rooms:
                    i.pricePerDay += foodItem.pricePerDay
        curdate = datetime.now()
        startDay = max(curdate, checkInDate-timedelta(days=3)).day - curdate.day
        startIdx = startDay
        startdate = max(curdate, checkInDate-timedelta(days=3))
        for i in range(7):
            temp = startdate + timedelta(days=i)
            days.append(temp.day)
        avail = []
        for room in rooms:
            temp = []
            urls.append("/room/"+str(room.id))
            print(room.status)
            for j in range(7):
                temp.append(int(room.status[startIdx+j]))
            avail.append(temp)

    print(avail)
    print(len(rooms))
    roomAvail = [0]*len(rooms)
    for i, room in enumerate(rooms):
        roomAvail[i] = 1 if checkAvailable(room) else 0
    print(roomAvail)
    return render_template('Booking.html', rooms=rooms, avail=avail, days=days, urls=urls, availableOnly=availableOnly, srt=srt, foodId=foodId, amenitiesId=amenitiesId, roomAvail=roomAvail)

@app.route('/room/<roomid>', methods=["POST", "GET"])
def room(roomid):
    global roomId
    global cost

    roomId = int(roomid)
    bookedroom = Rooms.query.filter_by(id=roomId).first()
    bookedfood = FoodOptions.query.filter_by(id=foodId).first()
    bookedamenity= Amenities.query.filter_by(id=amenitiesId).first()
    roomCost = bookedroom.pricePerDay*((checkoutdate.day-checkindate.day)+1)
    foodCost = 0
    amenityCost=0
    if bookedfood is not None:
        foodCost = bookedfood.pricePerDay*((checkoutdate.day-checkindate.day)+1)
    if bookedamenity is not None:
        amenityCost = bookedamenity.pricePerDay*((checkoutdate.day-checkindate.day)+1)
    diff=checkindate.day-datetime.now().day
    cost = 0.2*(roomCost+foodCost+ amenityCost)
    if diff>30 :
       cost=cost*0.85
    if diff>15 and diff<30 :
       cost =cost*0.9
    user=User.query.filter_by(id=curUserId).first()
    otp=send_mail("OTP for payment verification","Enter the otp for verification", user.email)
    return render_template('payment.html', roomPrice=roomCost, foodPrice=foodCost,amenityPrice=amenityCost, payable=cost)

@app.route('/cash', methods=["POST", "GET"])
def cash():
    if otp==request.form['otp']:
        newcash=Cash(id=bookid,amountc=cost)
        db.session.add(newcash)
        db.session.commit()
        user=User.query.filter_by(id=curUserId).first()
        otp=send_confirmation_mail("Successful Booking","Enter the otp for verification", user.email)
        return redirect('/paymentComplete')
    else:
        user=User.query.filter_by(id=curUserId).first()
        otp=send_mail("OTP for payment verification","Enter the otp for verification", user.email)
        return render_template('cash.html', flag=1)
    return render_template('cash.html', flag=0)

@app.route('/credit', methods=["POST", "GET"])
def credit():
    if otp==request.form['otp']:
        name=request.form['name']
        cardno=request.form['card number']
        newcredit=Credit(id=bookid, name=name, cardno=cardno, amountcc=cost)
        db.session.add(newcredit)
        db.session.commit()
        return redirect('/paymentComplete')
    else:
        user=User.query.filter_by(id=curUserId).first()
        otp=send_mail("OTP for payment verification","Enter the otp for verification", user.email)
        return render_template('credit.html', flag=1)
    return render_template('credit.html', flag=0)

@app.route('/upi', methods=["POST", "GET"])
def upi():
    if otp==request.form['otp']:
        upiid=request.form['upi']
        newupi=UPI(id=bookid, upiid=upiid, amountu=cost)
        db.session.add(newupi)
        db.session.commit()
        return redirect('/paymentComplete')
    else:
        user=User.query.filter_by(id=curUserId).first()
        otp=send_mail("OTP for payment verification","Enter the otp for verification", user.email)
        return render_template('upi.html', flag=1)
    return render_template('upi.html', flag=0)

@app.route('/dates', methods=["POST", "GET"])
def dates():
    return render_template('calender.html')


@app.route('/history', methods=["POST", "GET"])
def history():
    currentDate = datetime.now()
    userBookings = Booking.query.filter_by(userId=curUserId).all()
    for i in userBookings:
        if currentDate > i.checkInDate and i.confirmation == 1:
            i.confirmation = 4
            db.session.commit()    
    rooms = [Rooms.query.filter_by(id=i.roomId).first() for i in userBookings]
    costs = [TotalBookingCost(i) for i in userBookings]
    user = User.query.filter_by(id=curUserId).first()
    return render_template('prevBooking.html', bookings=userBookings, user=user, rooms=rooms, prices=costs)


@app.route('/paymentComplete', methods=["POST", "GET"])
def paymentComplete():
    print("Payment Completed")
    id = Booking.query.count()
    curRoom = Rooms.query.filter_by(id=roomId).first()
    if checkAvailable(curRoom):
        conf = 1

    else:
        conf = 0
    queueIds = BookingQueue.query.filter_by(id=roomId).first()
    if conf == 1:
        updateStatus(roomId, checkInDate, checkOutDate, '1')
        print(curRoom.status)
    else:
        if queueIds is None:
            print("first")
            newId = str(id)
            newId = newId.rjust(4, '0')
            stat = newId
            stat = stat.ljust(40, '0')
            temp = BookingQueue(id=roomId, bookingIds=stat)
            print(stat)
            db.session.add(temp)
            db.session.commit()
        else:
            print("second")
            addhere = 36
            newId = str(id)
            newId = newId.rjust(4, '0')
            for idx in range(0, 40, 4):
                checker = queueIds.bookingIds[idx:idx+4]
                print(checker)
                if int(checker) == 0:
                    addhere = idx
                    break
            newstat = queueIds.bookingIds[:addhere] + newId + (queueIds.bookingIds[addhere+4:] if addhere+4 < 39 else "")
            queueIds.bookingIds = newstat
            db.session.commit()

    newBooking = Booking(id=id, userId=curUserId, roomId=roomId, foodId=foodId, checkInDate=checkInDate, checkOutDate=checkOutDate, dateOfBooking=datetime.now().date(), confirmation=conf, feedback="")
    try:
        db.session.add(newBooking)
        db.session.commit()
        print("Booking added successfully")
    except:
        print("Could not add new Booking to db")
    return history()

@app.route('/cancelBooking<bookingId>', methods=["POST", "GET"])
def cancelBooking(bookingId):
    print("Cancelling")
    booking = Booking.query.filter_by(id=bookingId).first()
    roomId = booking.roomId
    queueIds = BookingQueue.query.filter_by(id=roomId).first()
    if booking.confirmation == 0:
        tempIds = ""
        for idx in range(0, 40, 4):
            test = queueIds.bookingIds[idx:idx + 4]
            if int(test) != booking.id:
                tempIds += test
        tempIds = tempIds.ljust(40, '0')
        queueIds.bookingIds = tempIds
        db.session.commit()
    else:
        updateStatus(roomId, booking.checkInDate, booking.checkOutDate, '0')
        if queueIds is not None:
            tempIds = ""
            for idx in range(0, 40, 4):
                test = queueIds.bookingIds[idx:idx + 4]
                if checkBooking(int(test)):
                    pass
                else:
                    tempiDs += test
            tempIds = tempIds.ljust(40, '0')
            queueIds.bookingIds = tempIds
            db.session.commit()

    booking.confirmation = 3
    db.session.commit()
    if curUserId == 0:
        return adminHistory()
    return history()

@app.route('/feedback/<bookingId>', methods=["POST", "GET"])
def feedback(bookingId):
    return render_template('feedback.html', bookingId=bookingId)

@app.route('/setfeedback/<bookingId>', methods=["POST", "GET"])
def setfeedback(bookingId):
    getfeedback = request.form['text']
    booking = Booking.query.filter_by(id=bookingId).first()
    booking.feedback = getfeedback
    booking.confirmation = 5
    db.session.commit()
    return history()

if __name__ == '__main__':
    app.run(debug = True)

