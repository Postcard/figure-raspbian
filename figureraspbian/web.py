from flask import Flask

import processus

app = Flask(__name__)

@app.route('/trigger')
def trigger():
    try:
        processus.run()
        return 'Processus executed successfully'
    except Exception as e:
        return e.message, 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=False, port=8080)
