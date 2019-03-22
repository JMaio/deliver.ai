// get current user
let user = null;
$.get({
    url: '/api/current_user',
    success: function (msg) {
        console.log(`user (msg) = ${msg}`);
        user = msg
    }
});

let send_cmd = cmd => {
    console.log(`sending command: '${cmd}'`);
    $.get(`/cmd/${cmd}`);
};

let alert_checker = () => {
    console.log(`user = ${user}`);
    $.get({
        url: '/api/confirm',
        data: {
            user: user,
        },
        success: function (msg) {
            let pending = JSON.parse(msg);
            for (let ticket of pending) {
                let text =
                    `Delivery from: ${ticket.sender} (${ticket.message}) arriving in 2 minutes. Accept?`;
                console.log(ticket.id);
                let accept = confirm(text);
                console.log(accept);
                $.post({
                    url: '/api/confirm',
                    data: {
                        user: user,
                        ticket: ticket.id,
                        accepted: accept,
                    },
                    success: function (msg) {
                        console.log(msg);
                    }
                });
            }
        }
    })
};
setInterval(alert_checker, 5 * 1000);

$(document).ready(function () {
    // door open / close user controls
    $('button[data-cmd]').click(function (e) {
        if (!$(this).prop('disabled')) {
            let cmd = $(this).attr('data-cmd');
            // toggle state on open
            if (cmd === 'OPEN') {
                // show the alert dialog here
                alert("message");
                prompt("what's the pass?");
                // take return value and create request to costum url like /api/password
                // input the User and entered pincode

                // Response will be JSON
                // parse this response and then if it's something like "accepted"==true, open the box
                // o/w possibly asked to reenter for a certain number of times
                $(this)
                    .prop('disabled', true)
                    .toggleClass('btn-success')
                    .toggleClass('btn-outline-secondary');
                setTimeout(function () {
                    $('button[data-cmd=CLOSE]')
                        .prop('disabled', false)
                        .toggleClass('btn-danger')
                        .toggleClass('btn-outline-danger')
                }, 3000)
            } else if (cmd === 'CLOSE') {
                // wait a little before engaging 'close' button
                $(this)
                    .prop('disabled', true)
                    .toggleClass('btn-danger')
                    .toggleClass('btn-outline-secondary');
            }
            send_cmd(cmd);
        }
    });
});