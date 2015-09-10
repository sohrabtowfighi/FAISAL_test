"""
    We want to setup a processing pipeline that would accept a list of jobs
    (computing tasks) from multiple users and run these jobs on the compute
    server and email the results back to the users. The two main desired
    features of the processing pipeline are:
    
    1.  Webpage for getting the job lists from the users along with their 
        personal information.
    2.  A scheduler script written in BASH, that submits the jobs to p 
        processing threads, where only k serial jobs per thread are allowed. 
        The scheduler script should be run periodically using the cron daemon 
        and check if there is vacancy on the processing threads and submit jobs 
        to accordingly. The scheduler should behave “optimally” in the sense 
        that all the p processing threads must be utilized always, unless of 
        course the total number of jobs is less than p.
        
    You are required to implement the above processing pipeline and 
    successfully demonstrate its working under the following conditions:
    
        1.  Multiple users simultaneously submitting job lists via the web 
            interface.
        2.  Job lists of different lengths.
        3.  Jobs with varying run-times.
        4.  A reasonable choice for p and k.
        
    NOTE: You are free to choose the “test” jobs on the job lists as you like. 
    The only restriction is that the “test” jobs cannot expect any further user 
    input and they should be able to run readily on the compute server without 
    any dependencies.
"""
from wsgiref.simple_server import make_server
from Queue import queue
import threading
from random import random

jobs = queue()

def sum_random_numbers(n_random_numbers):
    sum_numbers = 0
    for i in range(0, n):
        sum_numbers += random()
    return sum_numbers

def application(environ, start_response):    
    
    start_response([('content-type', 'text/html;charset=utf-8')])
    try:
        jobs.put(job_data)
        response_body = "job submitted - expect an email at " + email
    except:
        response_body = "job submission failed"        
    # change format so thta response body is an iterable with bytes    
    response_body = [str.encode(response_body)]
    return response_body


server = wsgiref.simple_server.make_server('', 8000, application)
server.serve_forever()


