from flask import Flask
app = Flask(__name__)

@app.route("/")
def home():
    return "Hello, this is a test web app/n I am running this to test security tools"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
