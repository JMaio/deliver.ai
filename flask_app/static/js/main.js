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
                let text = `Delivery from: ${ticket.sender} (${ticket.message}) arriving in 2 minutes. Accept?`;
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
                $(this)
                    .prop('disabled', true)
                    .removeClass('btn-success')
                    .removeClass('btn-outline-secondary')
                    .addClass('btn-outline-secondary');
                setTimeout(function () {
                    $('button[data-cmd=CLOSE]')
                        .prop('disabled', false)
                        .removeClass('btn-outline-danger')
                        .addClass('btn-danger')
                }, 3000)
            } else if (cmd === 'CLOSE') {
                // wait a little before engaging 'close' button
                $(this)
                    .prop('disabled', true)
                    .removeClass('btn-danger')
                    .addClass('btn-outline-secondary');
            }
            send_cmd(cmd);
        }
    });

    $('form[name=user-pin-code-form]').submit(function (e) {
        e.preventDefault();
        $.get({
            url: '/api/user_pin',
            data: {
                user: user,
                code: $(this).find('#code-box').val(),
            },
            success: function (msg) {
                if (JSON.parse(msg)) {
                    $('#code-box-feedback')
                        .text("Correct PIN entered!")
                        .removeClass('text-danger')
                        .addClass('text-success');
                    $('#verify-pin-button').prop('disabled', true);
                    setTimeout(function () {
                        $('#open-door-modal').modal('hide')
                    }, 1500);
                    $('button[data-cmd=OPEN]')
                        .prop('disabled', false)
                        .removeClass('btn-outline-success')
                        .addClass('btn-success');
                } else {
                    // verify failed!
                    $('#code-box-feedback')
                        .text("PIN code incorrect!")
                        .addClass('text-danger');
                }
            },
        });
    })
});