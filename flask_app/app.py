from flask import Flask, render_template, request
from recipient import Recipient

app = Flask(__name__)
curr_username = "ash.ketchum"
recipients = Recipient.from_file("recipients.txt")
recv_map = {recv.username: recv for recv in recipients}


@app.route('/')
def index():
    return render_template(
        'index.html',
        title="Secure Office Delivery",
        username=curr_username,
    )


@app.route('/deliver/')
def recipients_index():
    return render_template(
        'recipients.html',
        username=curr_username,
        recipients=recipients,
    )


@app.route('/deliver/<string:username>')
def recipient_info(username):
    recipient = recv_map[username]
    return render_template(
        'recipient_info.html',
        username=curr_username,
        recipient=recipient,
    )


@app.route('/receive/')
def receive():
    return render_template(
        'base.html',
        # username=username,
        # offices=offices,
    )


@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # TODO authenticate the user
        pass
    return "this is a login screen"


@app.route('/send-delivery', methods=['POST'])
def send_delivery():
    pass


if __name__ == '__main__':
    app.run()
