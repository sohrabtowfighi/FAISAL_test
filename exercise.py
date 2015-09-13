"""
    FAISAL Submission - Sohrab Towfighi
    Licence: GNU GPL v3.0
    September 12, 2015
    
    Contents:
    1. Imports
    2. HTML
    3. Data Pipeline
        3a. Functions
        3b. Classes
    4. Automated Testing
        4a. Functions
        4b. Class
    5. Main
    6. Notes
"""

# 1. Imports
from multiprocessing import Process, Queue
from threading import Timer
from time import sleep
from pdb import set_trace
from numpy import argmin, argmax
from wsgiref.simple_server import make_server
from email.mime.text import MIMEText
from urllib.parse import parse_qs, urlencode
from time import sleep
import smtplib
# for testing
import unittest
import imaplib
from urllib.request import urlopen

# 2. HTML
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

# 3a Data Pipeline Functions
def application(environ, start_response):
    # https://www.python.org/dev/peps/pep-0333/
    # PEP 0333 -- Python Web Server Gateway Interface v1.0
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
    try:
        for i in range(1, n+1):
            result += i
    except:
        result = -1
    return result

def schedule(time_interval, supervisor):
    # recursive calls to threading.Timer produce an indefinitely operating
    # timer
    supervisor.manage()   
    Timer(time_interval, schedule, args=(time_interval, supervisor)).start()

# 3b Data Pipeline Classes
class WebServer(object):
    def __init__(self, ip, port, app):
        self._server = make_server(IP, PORT, application)
        self._server_process = Process(target=self._server.serve_forever)
        self._server_process.start()

class Emailer(object):
    def __init__(self, input_queue):
        self._emailer = EmailWorker(input_queue)
        self._emailer.start()

class process_input(object):
    def __init__(self, n, email):
        self._n = n
        self._email = email
        self._arith_series = 0

class EmailWorker(Process):
    def __init__(self, input_queue):
        Process.__init__(self)
        self._input_queue = input_queue   
    @staticmethod
    def compose(x, y):
        body = "Input: " + str(x) + "\nOutput: " + str(y)
        return body
    def connectEmail(self):
        self._sender_email_address = 'test.faisal.noreply1@gmail.com'
        self._sender_email_password = 'medicalimaging'    
        self._server = smtplib.SMTP('smtp.gmail.com', 587)
        self._server.ehlo()
        self._server.starttls()
        self._server.login(self._sender_email_address, 
                           self._sender_email_password)                 
    def sendEmail(self, recipient_email_address, msg_string):
        subject = 'FAISAL Query'        
        msgbody = '\r\n'.join(['To: %s' % recipient_email_address,
                               'From: %s' % self._sender_email_address,
                               'Subject: %s' % subject,
                               '', msg_string])    
        self._server.sendmail(self._sender_email_password, 
                        [recipient_email_address], 
                        msgbody) 
    def run(self):
        self.connectEmail()        
        while True:
            myinput = self._input_queue.get()
            if myinput is not None:
                n = myinput._n
                arith_series = myinput._arith_series
                email = myinput._email
                message = EmailWorker.compose(n, arith_series)
                self.sendEmail(email, message)
        return        
                
class Worker(Process):
    def __init__(self, input_queue, output_queue):
        Process.__init__(self)
        self._input_queue = input_queue        
        self._output_queue = output_queue
    def run(self):
        while True:
            myinput = self._input_queue.get()
            if myinput is not None:
                n = myinput._n
                myinput._arith_series = arithmetic_series(n)
                self._output_queue.put(myinput)
        return

class Supervisor(object):
    def __init__(self, num_workers, limit_jobs_per_worker, input_queue,
                 output_queue):
        self._num_workers = num_workers
        self._limit_jobs_per_worker = limit_jobs_per_worker
        self._workers = list()
        self._workers_queues = list()      
        self._input_queue = input_queue
        self._output_queue = output_queue
        for i in range(0, num_workers):
            self._workers_queues.append(Queue(maxsize=limit_jobs_per_worker))
            myinputqueue = self._workers_queues[-1]
            outputqueue = self._output_queue
            self._workers.append(Worker(myinputqueue, outputqueue))
            self._workers[-1].start()
    def check(self):
        jobs_in_workers = [0]*self._num_workers
        for i in range(0, self._num_workers):
            jobs_in_workers[i] = self._workers_queues[i].qsize()
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
            job_to_transfer = self._workers_queues[self._most_full_index].get()
            self._workers_queues[self._least_full_index].put(job_to_transfer)
            return True
        return False
    def add(self):
        myjob = self._input_queue.get()
        self._workers_queues[self._least_full_index].put(myjob)
    def manage(self):
            self.check()
            isTransfer = self.transfer()
            if isTransfer == True:
                self.check() 
            while not self.isFull() and self._input_queue.qsize() > 0:
                self.add()

# for testing
def submitManyJobsToPortal(url, n, email, count=2):
    results = []
    for i in range(0, count):
        results.append(submitJobToPortal(url, n, email))
    return results

def submitJobToPortal(url, n, email):
    form_data = {'n': n, 'email': email}
    data = urlencode(form_data)
    data = data.encode('UTF-8')
    response = urlopen(url, data)
    data = response.read()
    return data

def countInbox(gmail, password, port):    
    imap = imaplib.IMAP4_SSL('imap.gmail.com', port)
    imap.login(gmail, password)
    imap.select()
    res = imap.search(None,'UnSeen')
    indices =  str(res[1][0], 'utf-8').split()
    imap.close()
    imap.logout()
    number_unread_messages = len(indices)
    return number_unread_messages

def emptyInbox(gmail, password, port):
    imap = imaplib.IMAP4_SSL('imap.gmail.com', port)
    imap.login(gmail, password)
    imap.select()    
    typ, data = imap.search(None, 'ALL')
    for num in data[0].split():
        imap.store(num, '+FLAGS', '\\Deleted')
    imap.expunge()
    imap.close()
    imap.logout()

def miniTestSuite(url, port):           
    receive_gmail = 'test.faisal.receive@gmail.com'
    password = 'medicalimaging'   
    gmail_port = 993
    num_emails = 10
    time_limit = 100
    n = 2
    emptyInbox(receive_gmail, password, gmail_port)
    init = countInbox(receive_gmail, password, gmail_port)
    submitManyJobsToPortal(url + ":" + str(port), n, receive_gmail, num_emails)
    time = 0
    while time < time_limit:
        sleep(2)
        time += 2
        if countInbox(receive_gmail, password, gmail_port) == num_emails:
            break
    emptyInbox(receive_gmail, password, gmail_port)
    sleep(1)
    post_empty = countInbox(receive_gmail, password, gmail_port)
    assert post_empty == 0
    print("Passed miniTestSuite")    
    
class Tests(unittest.TestCase):
    _port = 8000 
    _gmailport = 993
    _url = 'http://127.0.0.1:' + str(_port)        
    _gmail = 'test.faisal.receive@gmail.com'
    _pass = 'medicalimaging'
    _timeout = 30                 
    def setUp(self):
        emptyInbox(self._gmail, self._pass, self._gmailport)   
        sleep(1)
    @classmethod
    def tearDownClass(self):
        emptyInbox(self._gmail, self._pass, self._gmailport)   
    def test_users(self):
        num_users = 3
        jobs_per_user = 2
        arith_input = 15
        users = []
        for i in range(0, num_users):
            users.append(Process(target=submitManyJobsToPortal, 
                                     args=(self._url, arith_input, 
                                           self._gmail, jobs_per_user)))
            users[i].start()
        time = 0
        num_emails = countInbox(self._gmail, self._pass, self._gmailport)
        while num_emails != num_users*jobs_per_user:
            sleep(1)
            time += 1
            if time > self._timeout:                
                raise TimeoutError("Timeout during test_users")
            num_emails = countInbox(self._gmail, self._pass, self._gmailport)
    def test_job_list_length(self):
        job_list_lengths = [1, 2, 3, 12]
        for i in job_list_lengths:
            submitManyJobsToPortal(self._url, 10, self._gmail, i)
            time = 0
            while countInbox(self._gmail, self._pass, self._gmailport) != i:
                sleep(1)
                time += 1
                if time > self._timeout:                    
                    raise TimeoutError("Timeout during test_job_list_length")
            emptyInbox(self._gmail, self._pass, self._gmailport)
    def test_job_time_duration(self):
        for arith_input in [3, 200000, int(2E7)]:
            time = 0
            submitJobToPortal(self._url, arith_input, self._gmail)
            while countInbox(self._gmail, self._pass, self._gmailport) == 0:
                sleep(1)
                time += 1
                if time > self._timeout:
                    raise TimeoutError("Timeout during test_job_time_duration")


if __name__ == '__main__':
    jobs = Queue()
    emails = Queue()
    IP = '127.0.0.1'
    PORT = 8000
    interval = 0.1  # seconds until Supervisor.manage is scheduled to run
    NUMBER_OF_PROCESSES = p = 3  # p
    MAX_JOBS_PER_PROCESS = k = 3  # k
    myEmailer = Emailer(emails)
    mySupervisor = Supervisor(p, k, jobs, emails)  
    mySchedule = schedule(interval, mySupervisor)
    myServer = WebServer(IP, PORT, application)
    miniTestSuite('http://'+IP, PORT)        
    unittest.main()
    
# 6. Notes
    """            
        The script runs a localhost webserver. Run the script using 
        'python3 exercise.py' in terminal. Access the site at 
        'http://127.0.0.1:8000'. The job distribution is controlled by the 
        Supervisor class' manage method. The supervisor manages every 
        interval==0.1 seconds. I am using multiprocessing.Process instead of 
        threading.Thread because the global interpreter lock in Python prevents
        the simultaneous execution of multiple threads. 
        I am using test.faisal.noreply1@gmail.com to send results to users.
        I am using test.faisal.receive@gmail.com to receive emails in the 
        course of automated testing. The password for both is 'medicalimaging'.
        The automated testing takes about 1 minute. The tests check the 
        recipient's email address to make sure the correct number of messages 
        are delivered. Gmail blocks attempts to submit very large number of 
        emails at once but the code is scalable.
    """