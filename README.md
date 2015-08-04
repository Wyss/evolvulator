## Evolvulator readme

Server dependencies include: Python 2.7, Twisted, autobahn.websocket, and Flask


### Bioreactor setup

1. Connect small quick release tube to the stop cock of the media reservoirs and attach with a zip tie.
2. Connect bioreactor feeder tube to fresh media reservoir.
3. Connect bioreactor waste tube to waste reservoir.
4. Connect equalizer tubing between waste and fresh media reservoirs.
5. Tape equalizer tubing to the side of media reservoir.
6. Tighten all ports on the top of bioreactor.
7. Fill bioreactor by opening media reservoir stop cock.
8. Once full place feeder tube into the pinch valve.
9. Check that feeder tubing is completely in the valve and make sure all connector tops on the top of the bioreactor are tight!


### Setting up the server:

Create a new database file:

1. navigate to `<repository_path>/code/service/experimentcore`
2. run python
3. type “from exp_dbifc import createDB” without quotes
4. type “createDB(“/location/of/created/database/file_name.DB”)” don't type outside-most quotes
a) replace /location/of/created/database/ with the path to the directory where the database will be created
b) replace file_name with the name of the database.
c) e.g. /home/wade/Documents/Evolvulator/database/Wade.DB

start the server with the following command:

    twistd -noy app.tac

To output information displayed in the terminal to a log file initiate the server with the following command:

    twistd -noy app.tac | tee logfile.txt or twistd -noy app.tac > logfile.txt


### Creating an experiment

Create a `*_evo.json` file for each Evolvulator hardware you would like to run in
`<repository_path>/code/service/evolvulator`

Use the evo_example_evo.json as a template

### Starting the server:

1. cd to `<repository_path>/code/service`

2. start server with `twistd -noy app.tac > date_log.txt`

3. open localhost:8080 in your preferred browser

4. open new tabs for Evo evo


### Running an experiment

1. After filling each bioreactor with clean media, turn on the stir bar, and change the max sensor reading (blank) on the control web page with the strip chart.  You can determine the max sensor reading by opening a web page of each Evolvulator IP and looking at Analog 2.  Refresh a couple times to get accurate reading.

2. On the control web page hit the “Start” button to begin recording data to database.  Hit “Loop” to start control loop.

3. After experiment is complete, copy and rename the Wade.DB files to save all data.

