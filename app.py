from flask import Flask, render_template, send_from_directory
import os

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/download')
def download_file():
    return send_from_directory(directory=os.path.join(BASE_DIR, 'static'),
                               path='aerith_interpreter.py', as_attachment=True)

if __name__ == '__main__':
    # For ProFreeHost, Flask should run on host='0.0.0.0'
    app.run(debug=True, host='0.0.0.0', port=5000)
