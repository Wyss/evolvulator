// Copyright (c) 2011 Wyss Institute at Harvard University
// 
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
// 
// The above copyright notice and this permission notice shall be included in
// all copies or substantial portions of the Software.
// 
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
// THE SOFTWARE.
// 
// http://www.opensource.org/licenses/mit-license.php



// Evolvulator.ino -- derived from Web_Demo.ino sample code for Webduino server 
//                      library
// dependency Webduino webserver library
// https://github.com/sirleech/Webduino
 
// http://host/
// This URL brings up a display of the values READ on digital pins 0-9
// and analog pins 0-5.  This is done with a call to defaultCmd.
//
// http://host/form
// This URL also brings up a display of the values READ on digital pins 0-9
// and analog pins 0-5.  But it's done as a form,  by the "formCmd" function,
// and the digital pins are shown as radio buttons you can change.
// When you click the "Submit" button,  it does a POST that sets the
// digital pins,  re-reads them,  and re-displays the form.
//
// http://host/json
// return: response JSON formatted system state with respect to arduino pins
// 
// http://host/control
// input: GET request to turn on a LOAD
// return: response JSON formatted system state
//
// http://host/measurement
// input: none
// return: response JSON formatted system state


#define SERVER_IP 192,168,1,130
#define MAC_ADDRESS  0x40, 0xA2, 0xDA, 0x00, 0x75, 0xC3

#define PREFIX ""
#define NAMELEN 32
#define VALUELEN 32

//to prevent compiling errors in Ubuntu and Windows Arduino IDE, favicon should be defined in WebServer.h.

// Analog Pins
#define POTENTIOMETER_PIN 0
#define PHOTODIODE0_PIN 1
#define PHOTODIODE1_PIN 2
	 
// Digital Pins
#define FAN_PIN	9
#define LED0_PIN 0
#define LED1_PIN 1
#define LOAD0_PIN 5
#define LOAD1_PIN 6
#define LOAD2_PIN 7
#define LOAD3_PIN 8
#define _ON  1
#define _OFF 0

#include "SPI.h"
#include "avr/pgmspace.h" // new include
#include <string.h>
#include "Ethernet.h"
#include "WebServer.h"
#define VERSION_STRING "0.1"

// no-cost stream operator as described at 
// http://sundial.org/arduino/?page_id=119
template<class T>
inline Print &operator <<(Print &obj, T arg) { obj.print(arg); return obj; }

// CHANGE THIS TO YOUR OWN UNIQUE VALUE
static uint8_t mac[] = {  MAC_ADDRESS };

// CHANGE THIS TO MATCH YOUR HOST NETWORK
static uint8_t ip[] = {SERVER_IP}; 

WebServer webserver(PREFIX, 80);

//
uint16_t potentiometer_value = 0;
uint16_t photodiode0_value = 0;
uint16_t photodiode1_value = 0;
uint8_t fan_status = _ON;
void load_on(uint8_t load_pin);
void load_off(uint8_t load_pin);

// commands are functions that get called by the webserver framework
// they can read any posted data from client, and they output to server

void isLOADOn(WebServer &server, WebServer::ConnectionType type, uint8_t pin) 
{
    if (digitalRead(pin) == _ON) {
        server << "\"ON\"";
    }
    else {
        server << "\"OFF\"";
    }
}

void isLEDOn(WebServer &server, WebServer::ConnectionType type, uint8_t pin) 
{
    if (digitalRead(pin) == LOW) {
        server << "\"ON\"";
    }
    else {
        server << "\"OFF\"";
    }  
}

void returnState(WebServer &server, WebServer::ConnectionType type) 
{
    // return system state.  
    server << "{ ";
    server << "\"POTVALUE\": " << potentiometer_value;
    server << ", \"PHOTODIODE0\": " << photodiode0_value;
    server << ", \"PHOTODIODE1\": " << photodiode1_value;
    server << ", \"LOAD0\": "; isLOADOn(server, type, LOAD0_PIN);
    server << ", \"LOAD1\": "; isLOADOn(server, type, LOAD1_PIN);
    server << ", \"LOAD2\": "; isLOADOn(server, type, LOAD2_PIN);
    server << ", \"LOAD3\": "; isLOADOn(server, type, LOAD3_PIN);
    server << ", \"LED0\": "; isLEDOn(server, type, LED0_PIN);
    server << ", \"LED1\": "; isLEDOn(server, type, LED1_PIN);
    server << " }";
}

void measurementCmd(WebServer &server, WebServer::ConnectionType type, char *url_tail, bool tail_complete)
{
    if (type == WebServer::POST) {
        server.httpFail();
        return;
    }

    server.httpSuccess("application/json");
    
    if (type == WebServer::HEAD) {
        return;
    }
    returnState(server,type);
}

void controlCmd(WebServer &server, WebServer::ConnectionType type, char *url_tail, bool tail_complete)
{
    URLPARAM_RESULT rc;
    char name[NAMELEN];
    int  name_len;
    char value[VALUELEN];
    int value_len;
    int loadnum;

    /* this line sends the standard "we're all OK" headers back to the
       browser */
    server.httpSuccess("application/json");

    /* if we're handling a GET or POST, we can output our data here.
       For a HEAD request, we just stop after outputting headers. */
    if (type == WebServer::HEAD) {
        return;
    }

    if (strlen(url_tail)) {
        while (strlen(url_tail)) {
            rc = server.nextURLparam(&url_tail, name, NAMELEN, value, VALUELEN);
            if (rc == URLPARAM_EOS) {
            }
            else {
                if (strncmp(name, "LOAD", 4) == 0) {
                    loadnum = abs(name[4] - '0');
                    // for now, let's turn the fan on and off
                    if (loadnum < 4) {
                        if (strncmp(value, "ON", 2) == 0) {
                            load_on(loadnum);
                        }
                        else {
                            load_off(loadnum);
                        }
                    } // end if
                } // end if strncmp
            } // end  else
        } // end while
    } // end if
    returnState(server,type);
}

// from Web_Demo.ino 
void jsonCmd(WebServer &server, WebServer::ConnectionType type, char *url_tail, bool tail_complete) {
    if (type == WebServer::POST) {
        server.httpFail();
        return;
    }

    server.httpSuccess("application/json");

    if (type == WebServer::HEAD)
        return;

    int i;    
    server << "{ ";
    for (i = 0; i <= 9; ++i) {
        // ignore the pins we use to talk to the Ethernet chip
        int val = digitalRead(i);
        server << "\"d" << i << "\": " << val << ", ";
    }

    for (i = 0; i <= 5; ++i) {
        int val = analogRead(i);
        server << "\"a" << i << "\": " << val;
        if (i != 5) { 
            server << ", ";
        }
    }
  
    server << " }";
}

// from Web_Demo.ino for debugging use only 
void outputPins(WebServer &server, WebServer::ConnectionType type, bool addControls = false)
{
    P(html_head) =
    "<html>"
    "<head>"
    "<title>Evolvulator Web Server</title>"
    "<style type=\"text/css\">"
    "BODY { font-family: sans-serif }"
    "H1 { font-size: 14pt; text-decoration: underline }"
    "P  { font-size: 10pt; }"
    "</style>"
    "</head>"
    "<body>";
    P(digital_pin_header) = "<h1>Digital Pins</h1><p>";
    P(analog_pin_header) = "</p><h1>Analog Pins</h1><p>";
    
    int i;
    server.httpSuccess();
    server.printP(html_head);

    if (addControls) {
        server << "<form action='" PREFIX "/form' method='post'>";
    }

    server.printP(digital_pin_header);

    for (i = 0; i <= 9; ++i) {
        // ignore the pins we use to talk to the Ethernet chip
        int val = digitalRead(i);
        server << "Digital " << i << ": ";
        if (addControls) {
            char pin_name[4];
            pin_name[0] = 'd';
            itoa(i, pin_name + 1, 10);
            server.radioButton(pin_name, "1", "On", val);
            server << " ";
            server.radioButton(pin_name, "0", "Off", !val);
        }
        else {
            server << (val ? "HIGH" : "LOW");
        }
        server << "<br/>";
    }

    server.printP(analog_pin_header);
    
    for (i = 0; i <= 5; ++i) {
        int val = analogRead(i);
        server << "Analog " << i << ": " << val << "<br/>";
    }

    server << "</p>";

    if (addControls) {
        server << "<input type='submit' value='Submit'/></form>";
    }
    server << "</body></html>";
}

// from Web_Demo.ino for debugging use only 
void formCmd(WebServer &server, WebServer::ConnectionType type, char *url_tail, bool tail_complete) 
{
    if (type == WebServer::POST) {
        bool repeat;
        char name[16], value[16];
        do {
            repeat = server.readPOSTparam(name, 16, value, 16);
            if (name[0] == 'd') {
                int pin = strtoul(name + 1, NULL, 10);
                int val = strtoul(value, NULL, 10);
                digitalWrite(pin, val);
            }
        } while (repeat);
        server.httpSeeOther(PREFIX "/form");
    }
    else {
        outputPins(server, type, true);
    }
}

// from Web_Demo.ino for debugging use only 
void defaultCmd(WebServer &server, WebServer::ConnectionType type, char *url_tail, bool tail_complete)
{
    outputPins(server, type, false);  
}


int checkFan(uint16_t *val_last)
// check status of the fan and update the speed
{
    uint16_t val = analogRead(POTENTIOMETER_PIN);
    // gotta drop 2 bits because 10 bit ADC, 8 bit PWM
    *val_last = (val + 3*(*val_last)) >> 2;     // weighted average value
    if (fan_status == _ON) {
        analogWrite(FAN_PIN, (*val_last) >> 3); // divide by 8 for a gain on the input
    }
    else {
        analogWrite(FAN_PIN, 0);
    }
    return 0;
}

void led_on(uint8_t led_pin)
{
    // LEDs are pull down
    digitalWrite(led_pin, LOW);
}

void led_off(uint8_t led_pin)
{
    // LEDs are pull down
    digitalWrite(led_pin, HIGH);
}

void load_on(uint8_t load_number)
{
    // assumes LOADX_PIN are sequential output pins on the arduino
    digitalWrite(LOAD0_PIN + load_number, HIGH);
}

void load_off(uint8_t load_number)
{
    // assumes LOADX_PIN are sequential output pins on the arduino
    digitalWrite(LOAD0_PIN +  load_number, LOW);
}

void checkPhotoDiode(uint16_t *val_last, uint8_t photodiode_pin, uint8_t led_pin)
{
    // Take the difference of the signal with the LED on, then the LED off
    // this takes care of the ambiant light bias
    
    led_on(led_pin);
    uint16_t val = (uint16_t) analogRead(photodiode_pin);
//    led_off(led_pin);
//    val -= analogRead(photodiode_pin);
    *val_last = (val + 3*(*val_last)) >> 2;
}

void setup()
{
    // set pins for digital output
    pinMode(LED0_PIN, OUTPUT);
    pinMode(LED1_PIN, OUTPUT);
    pinMode(FAN_PIN, OUTPUT);
    pinMode(LOAD0_PIN, OUTPUT);
    pinMode(LOAD1_PIN, OUTPUT);
    pinMode(LOAD2_PIN, OUTPUT);
    pinMode(LOAD3_PIN, OUTPUT);

    Ethernet.begin(mac, ip);
    webserver.begin();

    webserver.setDefaultCommand(&defaultCmd);
    webserver.addCommand("json", &jsonCmd);
    webserver.addCommand("control", &controlCmd);
    webserver.addCommand("measurement", &measurementCmd);
    webserver.addCommand("form", &formCmd);
}

void loop()
{
    // process incoming connections one at a time forever
    webserver.processConnection();
    
    // if you wanted to do other work based on a connecton, it would go here
    checkFan(&potentiometer_value);
    checkPhotoDiode(&photodiode0_value, PHOTODIODE0_PIN, LED0_PIN);
    checkPhotoDiode(&photodiode1_value, PHOTODIODE1_PIN, LED1_PIN);
}



