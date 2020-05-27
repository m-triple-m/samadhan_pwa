from flask import Flask,render_template,jsonify,request,redirect, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os
from datetime import date

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'pdf'])

app = Flask(__name__)
app.secret_key = "45678"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///samadhan.db'
app.config['ADMIN_NAME'] = 'admin'
app.config['ADMIN_PASS'] = 'admin'
db = SQLAlchemy(app)

#database models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    roll_no = db.Column(db.String(120), unique=True, nullable=False)
    imgPath = db.Column(db.String(20), nullable=False)

    def __repr__(self):
        return f'username : {self.username}, password : {self.password}'

class Query(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    block = db.Column(db.String(80), nullable=False)
    dept = db.Column(db.String(120), nullable=False)
    room_no = db.Column(db.String(120), nullable=False)
    issue_type = db.Column(db.String(120), nullable=False)
    img_path = db.Column(db.String(120), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'),
        nullable=False)
    user = db.relationship('User', backref=db.backref('user', lazy=True))
    date=db.Column(db.String(20),nullable=False)
    status=db.Column(db.String(20),nullable=False)
    # def __repr__(self):
    #     return f'username : {self.username}, password : {self.password}'

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(120), unique=True, nullable=False)
    attachment = db.Column(db.String(120), unique=True)
    upload_date = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(120), unique=True, nullable=False)
    

    def __repr__(self):
        return f'username : {self.title}, password : {self.description}'

db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/login',methods=['POST','GET'])
def login():
    if request.method=="POST":
        form = request.form
        if form['username']==app.config['ADMIN_NAME'] and form['password']==app.config['ADMIN_PASS']:
            session['login_type'] = 'admin'
            session['username'] = form['username']
            session['password'] = form['password']
            
            return redirect('/notification')
        user = User.query.filter_by(username=form['username']).first()
        print(user)
        if(user != None):
            if user.password == form['password']:
                session['login_type'] = 'user'
                session['username'] = form['username']
                session['password'] = form['password']
                session['user_id'] = user.id
                return redirect('/page')
            
            print('invalid password')
        
        print('user not found')
        return render_template('login.html', message = "invalid username or password!!")

    return render_template('login.html')

@app.route('/register',methods=['POST','GET'])
def register():
    if request.method=="POST":

        aadhar_file = request.files['aadharimg']    
        if aadhar_file:
            filename = secure_filename(aadhar_file.filename)
            aadhar_file.save(os.path.join(app.config['UPLOAD_FOLDER'],'adhaar',  filename))

        form = request.form
        username, email, password, roll_no = form['username'], form['email'], form['password'], form['rollno']

        #create user object
        user = User(username = username, email = email, password = password, roll_no = roll_no, imgPath = filename)

        #add user to table
        db.session.add(user)
        db.session.commit()

        return redirect('/login')

    return render_template('register.html')


@app.route('/page',methods=['POST','GET'])
def page():
    
    notifications = Notification.query.all()

    print(notifications)

    return render_template('page.html', notifications = notifications)


@app.route('/compose', methods=['POST', 'GET'])
def compose():
    if not session.get('username'):
        return redirect('/login')

    if request.method=="POST":
        
        image = request.files['img']    
        if image:
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'],'queries', filename))

        form = request.form
        print(form)
        block, dept, room_no, issue_type, img_path = form['block'], form['department'], form['room'], form['type'], ''
        #create user object
        query = Query(block = block, dept = dept, room_no = room_no, 
        issue_type = issue_type, img_path = filename, user_id = session.get('user_id'), 
        date = date.today().strftime("%d/%m/%Y"),
        status = 'generated')
        #add user to table
        db.session.add(query)
        db.session.commit()
        return render_template('compose.html', message="Query submitted successfully!!")
    return render_template('compose.html')

@app.route('/querydetail')
def QDetails():
    _id = request.args.get('_id')
    query = Query.query.get(_id)
    print(query)
    return render_template('query_details.html', query = query)

@app.route('/getstatus')
def getStatus():
    _id = request.args.get('query_id')
    user = Query.query.get(_id)
    return jsonify(user.status)

@app.route('/setstatus')
def setStatus():
    _id = request.args.get('id')
    status = request.args.get('status')
    user = Query.query.get(_id)
    print(user.status)
    user.status = status
    db.session.commit()
    return jsonify('success')

@app.route('/notification',methods=['POST','GET'])
def notify():
    if request.method == "POST":

        image = request.files['attachment']    
        filename = None
        if image:
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'],'attachments', filename))
        
        form = request.form
        noty = Notification(title = form['title'], description = form['description'], attachment = filename, upload_date = date.today().strftime("%d/%m/%Y"), category = form['category'])

        #add notification to table
        db.session.add(noty)
        db.session.commit()

        return render_template('notification.html', message = "Notification successfully added")
    return render_template('notification.html')

@app.route('/queries',methods=['POST','GET'])
def ListQueries():
    allQueries = Query.query.all()
    return render_template('list_queries.html', allQueries = allQueries)


@app.route('/page2',methods=['POST','GET'])
def page2():
    print(Notification.query.all())
    return render_template('page2.html')

@app.route('/userqueries')
def UserQueries():
    allQueries = Query.query.all()
    return render_template('user_queries.html', allQueries = allQueries)


if __name__ == '__main__':
    app.run(debug=True ) 