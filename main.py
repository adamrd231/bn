from flask import Flask, request, redirect, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://get-it-done@localhost:8889/get-it-done'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
app.secret_key = "abc"


class Task(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    completed = db.Column(db.Boolean)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    quad_id = db.Column(db.Integer)

    #TODO how to figure out to assign the quadrant clicked with the variable

    def __init__(self, name, owner, quad_id):
        self.name = name
        self.completed = False
        self.owner = owner
        self.quad_id = quad_id




class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(120))
    tasks = db.relationship('Task', backref='owner')

    def __init__(self, email, password):
        self.email = email
        self.password = password




@app.before_request
def require_login():
    allowed_routes = ['login', 'register', 'static']
    if request.endpoint not in allowed_routes and 'email' not in session:
        return redirect('/login')


@app.route('/', methods=['POST', 'GET'])
def index():

    quad_id = request.args.get('quad_id')
    if (quad_id):
        print(quad_id)


    return render_template('index.html',
          title="Bare Necessities, Bitch.",)

#THIS ROUTE BRINGS THE USER TO THE HOME PAGE TO CHOOSE HOW TO FILTER THEIR TASKS.
@app.route('/bn', methods=['POST', 'GET'])
def bn():

    owner = User.query.filter_by(email=session['email']).first()
    tasks = Task.query.filter_by(completed=False, owner=owner).all()
    completed_tasks = Task.query.filter_by(completed=True, owner=owner).all()
    quad_id = request.args.get('quad_id')

    #Captures the new task and adds it to the databse
    if request.method == 'POST':
        task_name = request.form['task']
        new_task = Task(task_name, owner, quad_id)
        db.session.add(new_task)
        db.session.commit()

    #When clicking on a quadrant, this will assign the quad_id variable with a value of 1-6


    #quadrant2 filter
    if (quad_id):

        quad_tasks = Task.query.filter_by(quad_id=quad_id).all()

        return render_template('bn.html',
                        title="Quadrant2",
                        tasks=quad_tasks)

    return render_template('bn.html',
          title="Get Er' Done",
          tasks=tasks,
          completed_tasks=completed_tasks)




@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and user.password == password:
            # to do - "remember that the user has logged in"
            session['email'] = email
            flash("Logged in")
            # session['password'] = password
            return redirect('/')
        else:
            flash('User password Incorrect, or user does not exist', 'error')


    return render_template('login.html')


@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        verify = request.form['verify']

        # - Validate the users data

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





@app.route('/delete-task', methods=['POST'])
def delete_task():

    task_id = int(request.form['task-id'])
    task = Task.query.get(task_id)
    task.completed = True
    db.session.add(task)
    db.session.commit()

    return redirect('/')

@app.route('/logout')
def logout():
    del session['email']
    return redirect('/')


if __name__ == '__main__':
    app.run()
