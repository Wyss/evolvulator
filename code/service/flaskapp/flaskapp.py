"""
Copyright (c) 2012 Wyss Institute at Harvard University

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
"""

"""
flaskapp.py
"""

from flask import Flask, g, request, render_template, jsonify, make_response, send_from_directory
from werkzeug.exceptions import HTTPException, NotFound
from os.path import dirname, basename, split, abspath
from os.path import join as op_join
import random
import sys

from experimentcore.exp_dbifc import setupExperiment
exp_dict = setupExperiment('evolvulator')

app = Flask(__name__)
app.config.from_object(__name__)
app.wsport = 9000 # default
                 
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(op_join(app.root_path, 'static'),
                               'faviconSQ.ico', mimetype='image/png')
#end def

@app.route('/')
def index():
    # simply render all of the available jobs
    job_list = [{'jobname':key} for key in exp_dict.keys()]  # create 
    return render_template('index.html', joblist=job_list)
# end def
    
@app.route('/experiment/_update_parameters/<job_name>')
def update_parameters(job_name=""):
    print "Received parameters"
    if job_name in exp_dict:
        dbifc = exp_dict[job_name]  # get the correct database interface
        new_params = request.args
        updatedindex = dbifc.updateParamDict(new_params)
        print "we've updated", updatedindex
        return jsonify(result="updated"+str(updatedindex))
    else:
        return request.args
# end def


@app.route("/experiment/<job_name>")
def show_experiment(job_name=""):
    # print "begin show experiment"
    if job_name in exp_dict:
        dbifc = exp_dict[job_name]  # get the correct database interface
        # print "begin listify params"
        params = dbifc.jsonListifyParameters()
        core_params = {'jobname':job_name, 'url':dbifc.getURL()}
        print "Show experiment"
        try:
            return render_template('experiment.html', core=core_params, parameters=params, wsport=app.wsport)
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print "In: ", inspect.stack()[1][3]
            print "Bad rendering of Template"
            return
    else:    
        return page_not_found(NotFound(), errormessage="This ain't no job")
# end def

@app.errorhandler(404)
def page_not_found(error, errormessage=""):
    return render_template('error404.html', message=errormessage), 404
    
@app.errorhandler(500)
def server_problem(error):
    return render_template('error500.html', message=error), 500

@app.route('/experiment/_get_data/<job_name>')
def get_data(job_name=""):
    print "Get data"
    if job_name in exp_dict:
        dbifc = exp_dict[job_name]  # get the correct database interface
        print "getting data"
        data = edb.getDataDict(g.db)
        return jsonify(data)
# end def

# @app.before_request
# def before_request():
#     """Make sure we are connected to the database each request."""
#     g.db = edb.connectToDB(thedatabase)
# 
# 
# @app.teardown_request
# def teardown_request(exception):
#     """Closes the database again at the end of the request."""
#     if hasattr(g, 'db'):
#         g.db.close()
# # end def