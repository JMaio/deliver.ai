from datetime import datetime

from flask import Flask, render_template, request, abort
from recipient import Recipient

app = Flask(__name__)
recipients = Recipient.from_file("recipients.txt")
rec_map = {rec.username: rec for rec in recipients}
user = rec_map.pop("ash.ketchum", None)


@app.route('/')
def index():
    return render_template(
        'index.html',
        title="Secure Office Delivery",
    )


@app.route('/deliver/')
def recipients_index():
    return render_template(
        'recipients.html',
        recipients=rec_map.values(),
    )


@app.route('/deliver/<string:username>')
def recipient_info(username):
    if username == user.username:
        return error_page(
            icon="far fa-check-circle",
            line1="Hey",
            line2="looks like you've found yourself!",
            button_text="View inbox",
            button_href='/receive/'
        )
    if username not in rec_map:
        return error_page(
            icon="fas fa-robot",
            line1="Oops...",
            line2="it looks like that person doesn't exist!",
        )
    recipient = rec_map[username]
    return render_template(
        'recipient_info.html',
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
    return "{}".format(request.form)


@app.errorhandler(404)
def error_page(
        error,
        icon='far fa-question-circle',
        line1="Whoa!",
        line2="<em>This is not the page you're looking for</em>",
        button_href='/',
        button_text='Go back'):
    return render_template(
        'error.html',
        error=error,
        icon=icon,
        line1=line1,
        line2=line2,
        button_href=button_href,
        button_text=button_text,
    )


@app.context_processor
def inject_template_globals():
    return {
        # an html-friendly time construct to force CSS refresh
        'now': datetime.utcnow().strftime("%Y-%m-%d-%H%M%S"),
        'user': user,
    }


if __name__ == '__main__':
    app.run()
