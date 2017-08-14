from flask import Flask, request, redirect, render_template, session, flash, make_response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from momentjs import momentjs
import os
from flask_weasyprint import HTML, render_pdf



#SET UP FLASK APP
app = Flask(__name__)
app.config['DEBUG'] = True
#SET ROUTE FOR DATABASE
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://get-it-done@localhost:8889/get-it-done'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
app.secret_key = "thebarenecessities"
app.jinja_env.globals['momentjs'] = momentjs

class Quadrant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    feature_name = db.Column(db.String(50))
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    location = db.Column(db.Integer)


    def __init__(self, feature_name, owner, location):
        self.feature_name = feature_name
        self.owner = owner
        self.location = location




#USER ACCOUNT CLASS
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(120))
    quadrants = db.relationship('Quadrant', backref='owner')
    tasks = db.relationship('Task', backref='owner')


    def __init__(self, email, password):
        self.email = email
        self.password = password





#TASK USER CLASS, CURRENTLY FILTERS BY
    # USER ACCOUNT
    # QUADRANT (1-6)
    # COMPLETED (TRUE OR FALSE)
class Task(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    completed = db.Column(db.Boolean)
    quad_id = db.Column(db.Integer)
    created = db.Column(db.DateTime)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, name, quad_id, owner):
        self.name = name
        self.completed = False
        self.created  = datetime.utcnow()
        self.quad_id = quad_id
        self.owner = owner



#BLOCKING ROUTES FOR USERS WHO ARE NOT SIGNED IN
#JUSTIN CURRENTLY CREATES ACCOUNTS, NEW USERS ARE MADE BY HIM
@app.before_request
def require_login():
    allowed_routes = ['login', 'register', 'static', 'pdf_template', '/']
    if request.endpoint not in allowed_routes and 'email' not in session:
        return redirect('/login')


#APP LANDS ON THIS PAGE IF USER IS NOT CURRENTLY SIGNED IN
#CHECKS TO MAKE SURE USER IS REGISTED IN THE DATABASE
#CHECKS THAT THE PASSWORD MATCHES THE USERS PASSWORD SAVED
@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        #Checks if there is a user email that matches the provided login
        if not (User.query.filter_by(email=email).first()):
            flash("username is incorrect or not registered.")
            return render_template('login.html')
        #if there is a user, get the user from the database
        #verify the password provided matches the database password
        if (User.query.filter_by(email=email).first()):
            check_password = User.query.filter_by(email=email).first()
            if password != check_password.password:
                flash("password is incorrect.")
                #KEEP THE USERNAME IF IT WAS CORRECT
                return render_template('login.html', check_password=check_password.email)
            #if password matches, log user in
            if password == check_password.password:
                session['email'] = email
                flash("Logged in")
                return redirect('/')

    return render_template('login.html')


#HOME PAGE ROUTE, SHOWS THE DASHBOARD FOR THE TASK MANAGEMENT APP
@app.route('/', methods=['POST', 'GET'])
def index():

    owner = User.query.filter_by(email=session['email']).first()


    if request.method == 'POST':
        quadrant_name = request.form['quadrant']
        quadrant_location = request.form['location']

        check_existing = Quadrant.query.filter_by(owner_id=owner.id).all()
        for check in check_existing:
            if str(check.location) == quadrant_location:
                db.session.delete(check)
                db.session.commit()

        if (quadrant_name, owner, quadrant_location):
            new_quadrant = Quadrant(quadrant_name, owner, quadrant_location)
            db.session.add(new_quadrant)
            db.session.commit()


    if (owner):
        quadrants = Quadrant.query.filter_by(owner_id=owner.id).all()

        return render_template('index.html',
                timestamp = datetime.now().replace(minute = 0),
                user=owner,
                quadrants=quadrants,)
    else:
        return render_template('index.html',
                timestamp = datetime.now().replace(minute = 0),
                user=user,)


#THIS ROUTE BRINGS THE USER TO THE TASKS PAGE, FILTERED BY WHICH QUADRANT THEY CLICK INTO
@app.route('/bn', methods=['POST', 'GET'])
def bn():

    user = User.query.filter_by(email=session['email']).first()
    quad_id = Quadrant.query.filter_by(owner_id=user.id).all()

    #IF THE USER WANTS TO CREATE A NEW TASK
    if request.method == 'POST':
        task_name = request.form['task']
        new_task = Task(task_name, quad_id, owner)
        db.session.add(new_task)
        db.session.commit()

    #CHECK WHICH QUADRANT THE USER CLICKED INTO
    if (quad_id):
        return render_template('bn.html',
                        title="Bare Necessity",
                        user=user,
                        quad_id=quad_id,)

        #TODO create a 404 / error page to land on
    return render_template('error_page.html',
          title="Error")


#PRINT YOUR BN!
@app.route('/pdf_template', methods=['POST', 'GET'])
def pdf_templates():
    owner = User.query.filter_by(email=session['email']).first()
    tasks = Task.query.filter_by(completed=False, owner=owner).all()
    html = render_template('pdf_template.html',
                                owner = owner,
                                tasks=tasks,
                                )
    return render_pdf(HTML(string=html))


#LOGS USER OF OF THE SESSION
@app.route('/logout')
def logout():
    del session['email']
    return redirect('/')


#REGISTER USERS
@app.route('/really-long-registration_name-throws-off-hackers', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        verify = request.form['verify']

        # - Validate the users data
        if not password == verify:
            return '<h1>Password does not match Verification</h1>'

        existing_user = User.query.filter_by(email=email).first()
        if not existing_user:
            new_user = User(email, password)
            db.session.add(new_user)
            db.session.commit()
            #todo - Remember the user
            session['email'] = email
            return redirect('/')
        else:
            # todo - user better response message
            return "<h1>Duplicate User</h1>"

    return render_template('register.html')





#######################
## FUTURE FEATURES  ###
#######################
#ROUTE HANDLER IS ORDER TO CHANGE COMPLETED TASK ATTRIBUTE OF TRUE/FALSE
@app.route('/complete-task', methods=['POST'])
def complete_task():

    task_id = int(request.form['task-id'])
    task = Task.query.get(task_id)
    task.completed = True
    db.session.add(task)
    db.session.commit()
    url_id = task.quad_id

    url = '/bn?quad_id=' + str(url_id)

    return redirect(url)

#ROUTE HANDLER IS ORDER TO CHANGE COMPLETED TASK ATTRIBUTE OF TRUE/FALSE
@app.route('/un-complete-task', methods=['POST'])
def un_complete_task():

    task_id = int(request.form['task-id'])
    task = Task.query.get(task_id)
    task.completed = False
    db.session.add(task)
    db.session.commit()
    url_id = task.quad_id

    url = '/bn?quad_id=' + str(url_id)

    return redirect(url)

#REMOVE TASK FROM THE DATABASE
@app.route('/delete-quadrant', methods=['POST'])
def delete_task():

    quadrant_id = int(request.form['quadrant-id'])
    quadrant = Quadrant.query.get(quadrant_id)
    db.session.delete(quadrant)
    db.session.commit()

    return redirect('/')



if __name__ == '__main__':
    app.run()
