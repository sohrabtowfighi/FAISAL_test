"""
    FAISAL Exercise
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
        to accordingly. The scheduler should behave 'optimally' in the sense 
        that all the p processing threads must be utilized always, unless of 
        course the total number of jobs is less than p.
        
    You are required to implement the above processing pipeline and 
    successfully demonstrate its working under the following conditions:
    
        1.  Multiple users simultaneously submitting job lists via the web 
            interface.
        2.  Job lists of different lengths.
        3.  Jobs with varying run-times.
        4.  A reasonable choice for p and k.
        
    NOTE: You are free to choose the 'test' jobs on the job lists as you like. 
    The only restriction is that the 'test' jobs cannot expect any further user 
    input and they should be able to run readily on the compute server without 
    any dependencies.
"""


from pdb import set_trace
from numpy import argmin, argmax
from wsgiref.simple_server import make_server
from email.mime.text import MIMEText
from urllib.parse import parse_qs
from queue import Queue
from time import sleep
from threading import Timer, Thread
import smtplib
import unittest

html = """
<html>
    <head>
        <title>User Input</title>
    </head>
<body>
<h1>Arithmetic series from 1 to n</h1>
<form action="/put_job" method="POST">
    n = <input type="number" name="n" id="n">
    <br/>
    Your email: <input type="email" name="email" id="n">
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
    raw_n = GET_request.get(b'n', [''])[0]
    raw_email = GET_request.get(b'email', [''])[0]
    response_body = [str.encode(html)]
    empties = [None, [''], '']
    if raw_n not in empties and raw_email not in empties:
        email = raw_email.decode('UTF-8')
        n = int(raw_n.decode('UTF-8'))
        my_process_input = process_input(n, email)
        try:
            jobs.put(my_process_input)
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

class Worker(Thread):
    def __init__(self, input_queue):
        self._input_queue = input_queue
        Thread.__init__(self)
    @staticmethod
    def compose(x, y):
        body = "Input: " + str(x) + "\nOutput: " + str(y)
        return body
    def sendEmail(self, recipient_email_address, msg_string):
        sender_email_address = 'test.faisal.noreply@gmail.com'
        sender_email_password = 'medicalimaging'    
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.ehlo()
        server.starttls()
        server.login(sender_email_address, sender_email_password) 
        subject = 'FAISAL Query'        
        msgbody = '\r\n'.join(['To: %s' % recipient_email_address,
                            'From: %s' % sender_email_address,
                            'Subject: %s' % subject,
                            '', msg_string])    
        server.sendmail(sender_email_password, [recipient_email_address], 
                        msgbody) 
        server.quit()
    def run(self):
        while True:
            myinput = self._input_queue.get()
            n = myinput._n
            email = myinput._email
            if myinput is not None:
                answer = arithmetic_series(n)
                msg_body = Worker.compose(n, answer)
                self.sendEmail(email, msg_body)

class Supervisor(object):
    def __init__(self, num_workers, limit_jobs_per_worker):
        # initialize the number of Workers
        self._num_workers = num_workers
        self._limit_jobs_per_worker = limit_jobs_per_worker
        self._workers = list()
        self._input_queues = list()        
        for i in range(0, num_workers):
            self._input_queues.append(Queue(maxsize=limit_jobs_per_worker))
            myinputqueue = self._input_queues[-1]
            self._workers.append(Worker(myinputqueue))
            self._workers[-1].start()
    def check(self):
        jobs_in_workers = [0]*self._num_workers
        for i in range(0, self._num_workers):
            jobs_in_workers[i] = self._input_queues[i].qsize()
        least_full_worker_index = argmin(jobs_in_workers)
        least_full_worker_count = jobs_in_workers[least_full_worker_index]
        most_full_worker_index = argmax(jobs_in_workers)
        most_full_worker_count = jobs_in_workers[most_full_worker_index]
        self._jobs_in_workers = jobs_in_workers
        self._least_full_index = least_full_worker_index
        self._least_full_count = least_full_worker_count
        self._most_full_index = most_full_worker_index
        self._most_full_count = most_full_worker_count
    def isFull(self):
        for i in range(0, self._num_workers):
            if self._jobs_in_workers[i] < self._limit_jobs_per_worker:
                return False
        return True
    def transfer(self):
        if self._least_full_count == 0 and self._most_full_count > 0:
            job_to_transfer = self._input_queues[self._most_full_count].get()
            self._input_queues[self._least_full_count].put(job_to_transfer)
            return True
        return False
    def add(self):
        myjob = jobs.get()
        self._input_queues[self._least_full_index].put(myjob)
    def manage(self):
            self.check()
            isTransfer = self.transfer()
            if isTransfer == True:
                self.check() 
            while not self.isFull() and jobs.qsize() > 0:
                self.add()

def schedule(time_interval, supervisor):
    supervisor.manage()   
    Timer(time_interval, schedule, args=(time_interval, supervisor)).start()

class WebServer(object):
    def __init__(self, ip, port, app):
        self._server = make_server(IP, PORT, application)
        self._server_thread = Thread(target=self._server.serve_forever)
        self._server_thread.start()



class Tests(unittest.TestCase):
  def test_simultaneous(self):
      self.assertEqual('foo'.upper(), 'FOO')

  def test_isupper(self):
      self.assertTrue('FOO'.isupper())
      self.assertFalse('Foo'.isupper())

  def test_split(self):
      s = 'hello world'
      self.assertEqual(s.split(), ['hello', 'world'])
      # check that s.split fails when the separator is not a string
      with self.assertRaises(TypeError):
          s.split(2)

if __name__ == '__main__':
    jobs = Queue()
    IP = '127.0.0.1'
    PORT = 8000
    interval = 1  # second
    NUMBER_OF_THREADS = p = 3  # p
    MAX_JOBS_PER_THREAD = k = 3  # k
    mySupervisor = Supervisor(p, k)  
    mySchedule = schedule(interval, mySupervisor)
    myServer = WebServer(IP, PORT, application)
    