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
}

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
    // allow only digits in the pin
    // $("input[type=number]").bind({
    //     keydown: function(e) {
    //         if (e.shiftKey === true ) {
    //             if (e.which == 9) {
    //                 return true;
    //             }
    //             return false;
    //         }
    //         if (e.which > 57) {
    //             return false;
    //         }
    //         if (e.which==32) {
    //             return false;
    //         }
    //         return true;
    //     }
    // });
});