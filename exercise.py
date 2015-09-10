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

from pdb import set_trace
from wsgiref.simple_server import make_server
from email.mime.text import MIMEText
from urllib.parse import parse_qs
from queue import Queue
import threading
import smtplib

html = """
<html>
    <head>
        <title>User Input</title>
    </head>
<body>
<h1>Arithmetic series from 1 to n</h1>
<form action="/put_job" method="POST">
    n = <input type="number" name="n">
    <br/>
    Your email: <input type="email" name="email">
    <br/>
    <input type="submit">
</form>
</body>
</html>
"""

def application(environ, start_response):
    status = '200 OK'
    headers = [('Content-type', 'text/html; charset=utf-8')]
    start_response(status, headers)
    try:
        request_body_size = int(environ.get('CONTENT_LENGTH', 0))
    except (ValueError):
        request_body_size = 0
    request_body = environ['wsgi.input'].read(request_body_size)
    GET_request = parse_qs(request_body)
    raw_n = GET_request.get(b'n', '')
    n = raw_n[1:-1].decode('UTF-8')
    raw_email = GET_request.get(b'email', '')
    email = int(raw_email.decode('UTF-8'))
    response_body = [str.encode(html)]
    if n not in [None, ''] and email not in [None, '']:
        my_process_input = process_input(n, email)
        try:
            jobs.put(my_process_input)
            print(my_process_input._n)
            response_body = [b"job submission succeeded"]
        except:
            response_body = [b"job submission failed"]    
    return response_body

def arithmetic_series(n):
    result = 0
    for i in range(1, n+1):
        result += i
    return result

class process_input(object):
    def __init__(self, n, email):
        self._n = n
        self._email = email

class Worker(threading.Thread):
    def __init__(self, input_queue, output_queue):
        self._email_server = smtplib.SMTP('localhost')
        self._input_queue = input_queue
        self._output_queue = output_queue
        threading.Thread.__init__(self)
    @staticmethod
    def compose(x, myresult):
        body = "Input: " + x + "\nOutput: " + myresult
        return body
    def sendEmail(self, email_address, msg_string):
        msg = MIMEtext(msg_string)
        msg['Subject'] = msg_string
        msg['From'] = 'FAISAL_noreply@sfu.ca'
        msg['To'] = email_address
        self._email_server.send_message(msg)
    def run(self):
        while True:
            myinput = self._input_queue.get()
            n = myinput._n
            email = myinput._email
            if myinput is not None:
                answer = arithmetic_series(n)
                msg_body = Worker.compose(n, answer)
                self.sendEmail(email, msg_body)

if __name__ == '__main__':
    results = Queue()
    jobs = Queue()
    IP = '127.0.0.1'  # localhost
    PORT = 8000  # arbitrary non-priveliged port
    NUMBER_OF_THREADS = 3  # p
    MAX_JOBS_PER_THREAD = 3  # k
    server = make_server(IP, PORT, application)
    server.serve_forever()


