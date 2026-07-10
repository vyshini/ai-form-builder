from flask import(
Flask, render_template, url_for, request, 
redirect, session, flash, Response, jsonify
)
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import bcrypt
from bson import ObjectId
import os
import csv
from io import StringIO
from werkzeug.utils import secure_filename
load_dotenv()

app = Flask(__name__)
app.secret_key = "supersecretkey"

MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["google_form_clone"]

users_col = db["users"]
forms_col = db["forms"]
responses_col = db["responses"]
questions_col = db["questions"]


@app.route('/')
def home():
    return redirect('/dashboard')

@app.route('/register',methods = ['GET','POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        if users_col.find_one({"email":email}):
            flash("user already exist ")
            return redirect('/register')
        
        hashed = bcrypt.hashpw(password.encode('utf-8'),bcrypt.gensalt())

        users_col.insert_one({
            "name":name,
            "email":email,
            "password": hashed
        })
        return redirect('/login')
    return render_template("register.html")

@app.route('/login',methods =['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = users_col.find_one({"email":email})
        #if user not found
        if not user:
            flash("user does not exist .Please register")
            return redirect('/login')
        
        #if wrong password
        if not bcrypt.checkpw(password.encode('utf-8'),user['password']):
            flash("wrong password")
            return redirect('/login')
        
        
        if user and  bcrypt.checkpw(password.encode('utf-8'),user['password']):
            session['user_id'] = str(user['_id'])
            session['user_name'] =  user['name']
            return redirect('/dashboard')
        
        return 'invalid login'
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    
    user_id = session['user_id']
    #get all forms created by logged -in user
    forms = list(forms_col.find({"user_id": user_id}))
    for form in forms:
        count = responses_col.count_documents({
            "form_id": form["_id"]
        })
        form["response_count"] = count
    return render_template('dashboard.html',forms = forms,user_name = session['user_name'])

@app.route('/create_form',methods = ['GET','POST'])
def create_form():
    if 'user_id' not in session:
        return redirect("/login")
    
    if request.method == "POST":
        title = request.form['title']

        form_data = {
            "title":title,
            "user_id":session['user_id']
        }

        forms_col.insert_one(form_data)

        return redirect('/dashboard')
    return render_template('create_form.html')

@app.route('/delete_form/<form_id>')
def delete_form(form_id):
    forms_col.delete_one({"_id":ObjectId(form_id)})
    return redirect('/dashboard')

@app.route("/view_form/<form_id>")
def view_form(form_id):

    form = forms_col.find_one({"_id": ObjectId(form_id)})
    questions = questions_col.find({"form_id": ObjectId(form_id)})

    return render_template("view_form.html",form=form,questions=questions)

@app.route('/edit_form/<form_id>',methods = ['GET','POST'])
def edit_form(form_id):
    form = forms_col.find_one({"_id":ObjectId(form_id)})
    if request.method == 'POST':
        question_text = request.form['question_text']
        question_type = request.form['question_type']
        

        question_data = {
            "form_id":ObjectId(form_id),
            "question_text":question_text,
            "question_type":question_type
        }

        if question_type == "mcq":
            options = request.form.getlist('options[]')
            options = [opt.strip() for opt in options if opt.strip() != ""]

            # 🔥 Validate minimum 2 options
            if len(options) < 2:
                return "MCQ must have at least 2 filled options"
            question_data["options"] = options
        
        questions_col.insert_one(question_data)
        
        return redirect(f'/edit_form/{form_id}')

    questions = questions_col.find({"form_id": ObjectId(form_id)})
    return render_template("edit_form.html",form = form, questions = questions)

@app.route('/delete_question/<question_id>/<form_id>')
def delete_question(question_id,form_id):
    questions_col.delete_one({"_id":ObjectId(question_id)})
    return redirect(f'/form/{form_id}')

@app.route('/add_question/<form_id>',methods = ['GET','POST'])
def add_question(form_id):
    if request.method == 'POST':
        question_text = request.form['question_text']
        question_type = request.form['question_type']

        image_file = request.files.get('question_image')
        image_filename = None

        if image_file and image_file.filename != "":
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'],filename)
            image_file.save(image_path)
            image_filename = filename

        question_data = {
            "form_id" : ObjectId(form_id),
            "question_text":question_text,
            "question_type":question_type,
            "image":image_filename
        }

        questions_col.insert_one(question_data)
    return redirect(f'/view_form/{form_id}')
    

@app.route("/submit/<form_id>", methods=["POST"])
def submit_form(form_id):
    user_email = request.form.get("user_email")
    
    # 🔴 TERMINAL X-RAY: Print exactly what the browser sent!
    print("\n--- NEW SUBMISSION RECEIVED ---")
    print(f"Browser sent this data: {request.form}")
    
    # Safely find questions (looking for both string and ObjectId just in case)
    questions = list(questions_col.find({
        "$or": [
            {"form_id": ObjectId(form_id)},
            {"form_id": form_id}
        ]
    }))
    print(f"Database found {len(questions)} questions to check.")

    responses = {}

    # Scoop up the answers
    for question in questions:
        qid = str(question["_id"])
        
        if question.get("question_type") == "image":
            image_file = request.files.get(f"answer_{qid}")
            if image_file and image_file.filename != "":
                filename = secure_filename(image_file.filename)
                # Ensure your static/uploads folder exists!
                if not os.path.exists("static/uploads"):
                    os.makedirs("static/uploads")
                image_file.save(os.path.join("static/uploads", filename))
                responses[qid] = filename
        else:
            answer = request.form.get(f"answer_{qid}")
            responses[qid] = answer
            # Print each matched answer
            print(f"Matched Question {qid} -> Answer: {answer}")

    # Save to MongoDB
    responses_col.insert_one({
        "form_id": ObjectId(form_id),
        "email": user_email,
        "responses": responses
    })
    
    print("--- SUBMISSION SAVED SUCCESSFULLY ---\n")
    
    form = forms_col.find_one({"_id": ObjectId(form_id)})
    form_title = form["title"] if form else "Form"
    return render_template("submit.html", form_id=form_id, form_title=form_title)

@app.route("/view_responses/<form_id>")
def view_responses(form_id):
    if 'user_id' not in session:
        return redirect('/login')

    form = forms_col.find_one({"_id": ObjectId(form_id)})
    questions = list(questions_col.find({
        "$or": [{"form_id": ObjectId(form_id)}, {"form_id": str(form_id)}]
    }))
    responses = list(responses_col.find({
        "$or": [{"form_id": ObjectId(form_id)}, {"form_id": str(form_id)}]
    }))

    # 📊 NEW: Calculate Chart Analytics for MCQ questions
    analytics_data = {}
    for q in questions:
        if q.get("question_type") == "mcq":
            qid = str(q["_id"])
            analytics_data[qid] = {
                "question": q["question_text"],
                "labels": q["options"],
                "data": [0] * len(q["options"]) # Creates a list of zeros like [0, 0, 0]
            }

    # Count up the actual answers
    for response in responses:
        user_answers = response.get("responses", {})
        for q in questions:
            if q.get("question_type") == "mcq":
                qid = str(q["_id"])
                answer = user_answers.get(qid)
                
                # If they picked a valid option, add 1 to that specific slice of the pie!
                if answer in analytics_data[qid]["labels"]:
                    idx = analytics_data[qid]["labels"].index(answer)
                    analytics_data[qid]["data"][idx] += 1

    # Notice we added `analytics_data=analytics_data` to the end of this return statement!
    return render_template("view_responses.html", form=form, questions=questions, responses=responses, analytics_data=analytics_data)


@app.route("/api/bot_create_form", methods=["POST"])
def bot_create_form():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    title = data.get("title", "Bot Generated Form")
    questions_data = data.get("questions", [])

    # 1. Create the Form
    new_form = {
        "title": title,
        "user_id": session['user_id']
    }
    form_id = forms_col.insert_one(new_form).inserted_id

    # 2. Insert all the questions the bot collected
    for q in questions_data:
        new_question = {
            "form_id": form_id,
            "question_text": q.get("text"),
            "question_type": q.get("type"),
            "options": q.get("options", [])
        }
        questions_col.insert_one(new_question)

    # 3. Return the ID so the bot can redirect the user to the Edit page!
    return jsonify({"success": True, "form_id": str(form_id)})


@app.route("/export_csv/<form_id>")
def export_csv(form_id):
    if 'user_id' not in session:
        return redirect('/login')

    form = forms_col.find_one({"_id": ObjectId(form_id)})
    if not form:
        return "Form not found", 404

    questions = list(questions_col.find({"form_id": ObjectId(form_id)}))
    
    # THE CRITICAL FIX: This tells MongoDB to grab the data whether it was 
    # saved as a special ObjectId (new submissions) OR a String (old submissions).
    responses = list(responses_col.find({
        "$or": [
            {"form_id": ObjectId(form_id)},
            {"form_id": str(form_id)}
        ]
    }))

    # Debugging: This will print in your VS Code terminal so you can verify!
    print(f"DEBUG: Successfully found {len(responses)} responses!")

    si = StringIO()
    cw = csv.writer(si)

    # 1. Create the Header Row
    headers = ["Email"] + [q["question_text"] for q in questions]
    cw.writerow(headers)

    # 2. Add the Data Rows
    for response in responses:
        row = [response.get("email", "N/A")]
        for q in questions:
            # Safely grab the answers dictionary, then grab the specific answer
            answer = response.get("responses", {}).get(str(q["_id"]), "No Answer")
            row.append(answer)
        cw.writerow(row)

    # 3. Return the file
    output = si.getvalue()
    safe_title = "".join([c for c in form['title'] if c.isalnum() or c==' ']).strip()
    
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={safe_title}_responses.csv"}
    )

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


if __name__ == "__main__":
    app.run(debug=True)