/*
Copyright (c) 2011 Wyss Institute at Harvard University

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

http://www.opensource.org/licenses/mit-license.php

WebClientTest.ino - Arduino Web client For Evolvulator

This sketch connects to a webserver with a GET request
and uses the webservers response to set local variables. 

Originally designed for a client based deployment, it is now most useful
for logging a DHCP ip address for the arduino
 
Ethernet shield attached to pins 10, 11, 12, 13
*/

#include <SPI.h>
#include <Ethernet.h>

#define SERVER_IP 10,11,32,65
#define SERVER_PORT 8080


// Enter a MAC address for your controller below.
// Newer Ethernet shields have a MAC address printed on a sticker on the shield
//byte mac[] = {  0x90, 0xA2, 0xDA, 0x00, 0x75, 0xCC };
byte mac[] = {  0x90, 0xA2, 0xDA, 0x00, 0x75, 0xCD };
IPAddress server(SERVER_IP);

boolean headerDone = false;
boolean isHTTP = false;

String current_line = "";
int line_no = -1; // initialize to -1

// Initialize the Ethernet client library
// with the IP address and port of the server 
// that you want to connect to (port 80 is default for HTTP):
EthernetClient client;


// Functional prototypes
boolean isLineEnd(char c);
boolean isHeaderDone(String * line);
boolean isHeaderHTTP(String * line, int line_no);

void setup() 
{
    // start the serial library:
    Serial.begin(9600);
    // start the Ethernet connection:
    if (Ethernet.begin(mac) == 0) 
    {
        Serial.println("Failed to configure Ethernet using DHCP");
        // no point in carrying on, so do nothing forevermore:
        for(;;)
            ;
    }
    // give the Ethernet shield a second to initialize:
    delay(1000);
    Serial.println("connecting...");

    // if you get a connection, report back via serial:
    if (client.connect(server, SERVER_PORT)) 
    {
        Serial.println("connected");
        // Make a HTTP request:
        client.println("GET /foo?clientName=arduino_is_cool HTTP/1.0");
        //client.println("GET /search?q=arduino HTTP/1.0");
        client.println();
    } 
    else 
    {
        // kf you didn't get a connection to the server:
        Serial.println("connection failed, ah nuts");
    }
}

void loop()
{
    // if there are incoming bytes available 
    // from the server, read them and print them:
    boolean is_line_end;
    if (client.available()) 
    {
        // an http header ends with a blank line
        //boolean currentLineIsBlank = true;
        char c = client.read();
        current_line += c;
        
        if (is_line_end = isLineEnd(c)) 
        { 
            line_no += 1;
            if (!isHTTP)
            {
                if (isHeaderHTTP(&current_line, line_no))
                {
                    isHTTP = true;
                }
                else
                {
                    Serial.println("EPic FAIL");
                }
            }
        }
        
        if (headerDone)                     // print if body of response
        {
            Serial.print(c);
        }
        else if (is_line_end && isHeaderDone(&current_line)) // otherwise see if the header is done
        {
            headerDone = true;
        }
        
        // Now clear the line post everything else
        if (is_line_end) { current_line = ""; }
    }

    // if the server's disconnected, stop the client:
    if (!client.connected()) 
    {
        Serial.println();
        Serial.println("disconnecting.");
        headerDone = false;
        client.stop();
        // do nothing forevermore:
        for(;;)
            ;
    }
}

boolean isLineEnd(char c){
    return true ? c == '\n' : false;
}

boolean isHeaderDone(String * line){
    return true ? line->startsWith("\r\n") : false;
}

boolean isHeaderHTTP(String * line, int line_no)
{
    if (line_no  == 0)
    {
        return true ? line->startsWith("HTTP") : false; 
    }
    else
    {
        return false;
    } 
}
