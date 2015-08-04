function stripChart(args) {
    // we use an inline data source in the example, usually data would
    // be fetched from a server
    // returns a hook function to modify the plot
    var ws_uri = args.ws_uri;
    var item_id = args.item_id;
    var time_id = args.time_id
    var datakey = args.datakey;
    var debug = args.debug || false;
    var data = [], total_points = 300;
    var last_time = 0, current_time = 0;
    var colors = ["rgb(0,122,179)"];
    
    // default plot options
    var defaultoptions = {
        series: { shadowSize: 0 }, // drawing is faster without shadows
        yaxis: { min: 0.0, max: 0.2 },
        xaxis: { show: false },
        grid: { hoverable: true }
    }; // end var options
    
    function zeroData() {
        while (data.length < total_points) {
            data.push(0.0);
        }   // end while
    } // end function
    zeroData();

    function setDataPoints(value) {
        if (data.length > 0) {
            data = data.slice(1);
        } // end if
        data.push(parseFloat(value));
        console.log(value);

        // zip the data values with the generic x values
        var res = [];
        for (var i = 0; i < data.length; ++i) {
            res.push([i, data[i]]);
        } // end for
        return res;
    } // end function setDataPoints

    var count = 0;
    var dtmax = 0;
    function updateData(m, key) {
        // callback to update the plot
        console.log(key);
        var data_points = setDataPoints(m[key]);
        last_time = current_time;
        current_time = m.TIMESTAMP  // this is unix time in seconds
        var ts = new Date(current_time*1000);
        var dt = (current_time - last_time).toFixed(2);
        // we don't display time on the x-axis because time scales are pretty
        // specific and might get messy going from no data to lot's of data
        // as the min and max of the plot axis changes
        if (last_time > 0) {
            $(time_id).text("Total Points: " + total_points + 
                            " - Sample Period: " + 
                            dt +"s - " +  
                            ts.toLocaleTimeString());
        }
        if ((dt > dtmax) && (dt < 100000.0) ){
            dtmax = dt;
            console.log("dtmax: " + dtmax);
        } 
        if (dt > 6.0) {
            console.log("dt: " + dt + ", count: " + ++count + ", dtmax: " + dtmax);
        }
        // this resets the color on a color change
        strip_plot.setData([ {color: colors[0], data: data_points} ]);
        
        // since the axes don't change, we don't need to call strip_plot.setupGrid()
        strip_plot.draw();
    }   // end function updateData
    
    function modifyPlot(options) {
        // right now just modifies the color
        var color = options.color;
        colors[0] = color;
    }
    
    // create the plot
    var strip_plot = $.plot($(item_id), 
                                [ { color: colors[0], data: setDataPoints(0) } ], 
                                defaultoptions);
    
function printStackTrace() {
  var callstack = [];
  var isCallstackPopulated = false;
  try {
    i.dont.exist+=0; //doesn't exist- that's the point
  } catch(e) {
    console.log(e.stack)
    if (e.stack) { //Firefox
      var lines = e.stack.split('\n');
      for (var i=0, len=lines.length; i<len; i++) {
        if (lines[i].match(/^\s*[A-Za-z0-9\-_\$]+\(/)) {
          callstack.push(lines[i]);
        }
      }
      //Remove call to printStackTrace()
      callstack.shift();
      isCallstackPopulated = true;
    }
    else if (window.opera && e.message) { //Opera
      var lines = e.message.split('\n');
      for (var i=0, len=lines.length; i<len; i++) {
        if (lines[i].match(/^\s*[A-Za-z0-9\-_\$]+\(/)) {
          var entry = lines[i];
          //Append next line also since it has the file info
          if (lines[i+1]) {
            entry += ' at ' + lines[i+1];
            i++;
          }
          callstack.push(entry);
        }
      }
      //Remove call to printStackTrace()
      callstack.shift();
      isCallstackPopulated = true;
    }
  }
  if (!isCallstackPopulated) { //IE and Safari
    var currentFunction = arguments.callee.caller;
    while (currentFunction) {
      var fn = currentFunction.toString();
      var fname = fn.substring(fn.indexOf("function") + 8, fn.indexOf('')) || 'anonymous';
      callstack.push(fname);
      currentFunction = currentFunction.caller;
    }
  }
  output(callstack);
}

function output(arr) {
  //Optput however you want
  console.log(arr.join('\n\n'));
}


    // manage the websocket connection
    function wsconnect(){
        try {
            console.log("opening Websocket");
            if ("WebSocket" in window) {
                console.log(ws_uri);
               var socket = new WebSocket(ws_uri);
            } // end if
            else {
               // Firefox currently prefixes the WebSocket object
               var socket = new MozWebSocket(ws_uri);
            } // end else
            socket.onopen = function() {
                console.log("Websocket opened");
            }
            socket.onmessage = function(e) {
                if (debug === true) {
                    console.log("Received data: " + e.data);
                }
                measurement =  JSON.parse(e.data);
                console.log(datakey);
                updateData(measurement, datakey);
            } // end function
            socket.onclose = function(){  
                console.log("Websocket closed");
                // automatically reconnect after 1s
                window.setTimeout(wsconnect, 2000);
            }
        } catch(exception) {  // end try
            console.log("Websocket exception" + exception); 
        } // end catch
        
    } // end function wsconnect
    wsconnect();
    return modifyPlot;
} // end function stripChart
