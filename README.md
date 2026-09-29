🧑‍💻 Launch the project in VS Code

1. Open VS Code

2. Go to File → Open Folder

3. Select your project folder.

4. Open Terminal → New Terminal.

5. Run these commands one by one:

python -m venv venv

Activate it:

Mac/Linux:

source venv/bin/activate

Windows:

venv\Scripts\activate

You should now see something, like:

(venv) your-name@computer %

6. Install the projects packages:

pip install -r requirements.txt

7. Create the database + demo accounts:

python seed.py

8. Start the website:

python run.py

The terminal should display that Flask is running. The file run.py starts the Flask application.   Run

9. Open Chrome/Safari. Go to:

http://127.0.0.1:5000

🎉 The college management system is now running.

🔑 Try logging in

Admin

admin@college.edu

admin123

Teacher

teacher@college.edu

teacher123

Student

student@college.edu

student123

All these accounts were created by seed.py.   Seed

Every time you want to start the project

source venv/bin/activate

python run.py

Then open http://127.0.0.1:5000. 🚀
