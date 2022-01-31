var cookiesNotice = {

    init: function(){
        const cookies_accept = localStorage.getItem('cookies_accept');

        $('#alertCookies').hide();

        if(cookies_accept != "true"){
            $('#alertCookies').show();

            $('#alertCookies').on('close.bs.alert', function () {
                localStorage.setItem('cookies_accept', 'true');
            });
        }
    }
}

$(document).ready(function() {
    cookiesNotice.init();
});