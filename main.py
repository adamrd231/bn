from flask import Flask, request, redirect, render_template, session, flash, make_response
from flask_sqlalchemy import SQLAlchemy
import pdfkit
from datetime import datetime
from momentjs import momentjs


#SET UP FLASK APP
app = Flask(__name__)
app.config['DEBUG'] = True
#SET ROUTE FOR DATABASE
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://get-it-done@localhost:8889/get-it-done'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
app.secret_key = "thebarenecessities"

#TASK USER CLASS, CURRENTLY FILTERS BY
    # USER ACCOUNT
    # QUADRANT (1-6)
    # COMPLETED (TRUE OR FALSE)
class Task(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    completed = db.Column(db.Boolean)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    quad_id = db.Column(db.Integer)
    created = db.Column(db.DateTime)

    def __init__(self, name, owner, quad_id):
        self.name = name
        self.completed = False
        self.created  = datetime.utcnow()
        self.owner = owner
        self.quad_id = quad_id

#USER ACCOUNT CLASS
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(120))
    tasks = db.relationship('Task', backref='owner')

    def __init__(self, email, password):
        self.email = email
        self.password = password


app.jinja_env.globals['momentjs'] = momentjs


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

    quad_id = request.args.get('quad_id')
    owner = User.query.filter_by(email=session['email']).first()
    tasks = Task.query.filter_by(completed=False, owner=owner).all()
    completed_tasks = Task.query.filter_by(completed=True, owner=owner).all()

    return render_template('index.html',
            timestamp = datetime.now().replace(minute = 0),
            owner=owner,
            tasks=tasks,
            completed_tasks=completed_tasks,
            title="Bare Necessities, Bitch.",)


#THIS ROUTE BRINGS THE USER TO THE TASKS PAGE, FILTERED BY WHICH QUADRANT THEY CLICK INTO
@app.route('/bn', methods=['POST', 'GET'])
def bn():

    owner = User.query.filter_by(email=session['email']).first()
    tasks = Task.query.filter_by(completed=False, owner=owner).all()
    completed_tasks = Task.query.filter_by(completed=True, owner=owner).all()
    quad_id = request.args.get('quad_id')

    #IF THE USER WANTS TO CREATE A NEW TASK
    if request.method == 'POST':
        task_name = request.form['task']
        new_task = Task(task_name, owner, quad_id)
        db.session.add(new_task)
        db.session.commit()

    #CHECK WHICH QUADRANT THE USER CLICKED INTO
    if (quad_id):

        #USER THE OWNER ACCOUNT SIGNED IN TO ONLY FILTER ONLY THEIR TASKS
        #FILTER BY COMPLETED TRUE VS FALSE TO SHOW BOTH CATEGORIES.
        #USE THE QUAD_ID VARIABLE TO FILTER THE TASKS
        quad_tasks = Task.query.filter_by(quad_id=quad_id, owner=owner, completed=False).all()
        completed_quad_tasks = Task.query.filter_by(quad_id=quad_id, owner=owner, completed=True).all()

        return render_template('bn.html',
                        title="Bare Necessity",
                        owner=owner,
                        tasks=quad_tasks,
                        quad_id=quad_id,
                        completed_quad_tasks=completed_quad_tasks,)

        #TODO create a 404 / error page to land on
    return render_template('error_page.html',
          title="Error")


#PRINT YOUR BN!
@app.route('/pdf_template', methods=['POST', 'GET'])
def pdf_templates():

    owner = User.query.filter_by(email=session['email']).first()
    tasks = Task.query.filter_by(completed=False, owner=owner).all()

    options = {
        'page-size' : 'Letter',
        'margin-top': '0in',
        'margin-right': '0in',
        'margin-bottom': '0in',
        'margin-left': '0in',
    }
    css = 'static/styles.css'

    rendered = render_template('pdf_template.html',
                                owner = owner,
                                tasks=tasks,
                                )

    pdf = pdfkit.from_string(rendered, False, options=options)
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline'

    return response


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


#LOGS USER OF OF THE SESSION
@app.route('/logout')
def logout():
    del session['email']
    return redirect('/')







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
@app.route('/delete-task', methods=['POST'])
def delete_task():

    task_id = int(request.form['task-id'])
    task = Task.query.get(task_id)
    task.completed = True
    db.session.delete(task)
    db.session.commit()
    url_id = task.quad_id

    url = '/bn?quad_id=' + str(url_id)

    return redirect(url)



if __name__ == '__main__':
    app.run()
