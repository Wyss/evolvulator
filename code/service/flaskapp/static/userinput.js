// Create a function that will toggle a button state and log the result to 
// a console like things
function toggleSwitch(item, updateurl, label_on, label_off, param_string) {
    $(item).bind('click', function() {
        var paramsOff = {};
        paramsOff[param_string] = 0;
        var paramsOn = {};
        paramsOn[param_string] = 1;
        if ($(this).text() === label_off) {
            $(this).removeClass("stop");
            $(this).text(label_on)
            $.getJSON(updateurl, 
                    paramsOff, 
                    function(data) {
                        $("#console_messages").text(data.result);
                        console.log(data.result);
                    } // end function
            ); // end getJSON
        } // end if
        else {
            $(this).addClass("stop");
            $(this).text(label_off)
            $.getJSON(updateurl, 
                    paramsOn, 
                    function(data) {
                        $("#console_messages").text(data.result);
                        console.log(data.result);
                    } // end function
            ); // end getJSON
        } // end else
    }); // end function and bind
};