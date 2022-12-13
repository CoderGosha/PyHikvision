# import main Flask class and request object
import logging

from flask import Flask, request

# create the Flask app
from loggerinitializer import initialize_logger

app = Flask(__name__)


def get_local_address():
    from netifaces import interfaces, ifaddresses, AF_INET
    for ifaceName in interfaces():
        addresses = [i['addr'] for i in ifaddresses(ifaceName).setdefault(AF_INET, [{'addr': 'No IP addr'}])]
        for a in addresses:
            if str(a).startswith("192"):
                return a


@app.route('/test', methods=['POST'])
def test():
    if request.method == 'POST':
        logging.info(f"{request} with data: {request.data}")
        return "Ok"


if __name__ == '__main__':
    initialize_logger("log")
    # run app in debug mode on port 5000
    app.run(debug=True, port=5010, host="0.0.0.0")
