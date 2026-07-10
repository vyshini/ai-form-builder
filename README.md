# 🚀 AI Form Builder

A full-stack, dynamic web application that allows users to create, manage, and share custom forms—inspired by Google Forms. Built with a Python/Flask backend and a MongoDB Atlas cloud database, featuring a cinematic, fully responsive UI.

**[🔴 Live Demo: Try the App Here!](https://ai-form-builder-rblq.onrender.com)**

---

## ✨ Features

* **Secure Authentication:** Complete user registration and login system with encrypted password hashing.
* **Dynamic Form Creation:** Users can build custom forms with multiple question types:
  * Short Answer (Text)
  * Multiple Choice (Radio Buttons)
  * Image Uploads
* **Personalized Dashboard:** A centralized hub where users can view and manage all the forms they have created.
* **Shareable Links:** Generate unique URLs for each form to send to users and collect responses.
* **Cinematic UI:** Beautifully styled frontend with smooth fade-in animations, responsive design, and intuitive user feedback.
* **Cloud Database:** Fully integrated with MongoDB Atlas for secure, remote data storage.

---

## 🛠️ Tech Stack

* **Frontend:** HTML5, CSS3, Vanilla JavaScript, Jinja2 Templating
* **Backend:** Python 3, Flask framework
* **Database:** MongoDB Atlas (via `pymongo`)
* **Security:** `bcrypt` / `werkzeug.security` (Password Hashing), `certifi` (Secure SSL Connections)
* **Deployment:** Render (Gunicorn WSGI)

---

## 💻 Local Setup & Installation

If you want to run this project locally on your own machine, follow these steps:

### 1. Clone the repository
```bash
git clone [https://github.com/vyshini/ai-form-builder.git](https://github.com/vyshini/ai-form-builder.git)
cd ai-form-builder
pip install -r requirements.txt
Create a file named .env in the root directory (or export these in your terminal) and add your secret keys:MONGO_URI="mongodb+srv://<your_username>:<your_password>@cluster0.xxxx.mongodb.net/?retryWrites=true&w=majority"
SECRET_KEY="your_super_secret_flask_key"
python app.py

📂 Project Structure

ai-form-builder/
│
├── static/                 # CSS stylesheets, client-side JS, and images
│   ├── style.css
│   └── style2.css
│
├── templates/              # HTML Jinja2 templates
│   ├── base.html
│   ├── login.html
│   ├── dashboard.html
│   └── form_editor.html
│
├── app.py                  # Main Flask application and API routes
├── requirements.txt        # Python dependencies
└── README.md               # Project documentation