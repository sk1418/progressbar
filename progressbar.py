# -*- coding:utf-8 -*-
import sys
import util, log
import datetime
import time
from threadpool import ThreadPool
from Queue import Queue
from threading import Thread
from threadpool import Terminate_Watcher


logger_name = 'progressBarLogger'
log.setup_log(logger_name,'INFO', 'INFO', '/tmp/foo.log')
LOG = log.get_logger(logger_name)

fmt_dl_header                    = u' Progress Monitor :[%s] | Threads Pool:[%d]\n'
fmt_dl_progress                  = u' Progress [%d/%d]:'
fmt_dl_last_finished             = u'  Latest %d finished tasks:\n'
fmt_dl_failed_jobs               = u'  Failed tasks:\n'

fmt_progress = '%s [%s] %.1f%%\n'
SHOW_DONE_NUMBER = 5


class JobStatus:
    """
    An Enum class to indicate the status of a Job
    """
    Waiting = 0
    Running = 1
    Success = 2
    Failed  = 3
    


class JobProgress(object):
    """
    progress object for single job 
    """
    def __init__(self, name, total_value=100):
        self.name = name
        self.total_value = total_value
        self.finished_value = 0
        self.start = datetime.datetime.now()

    def add_finished_value(self, increment):
        self.finished_value += increment

    def set_finished_value(self, finished_value):
        self.finished_value = finished_value

    def set_finished_percentage(self, finished_perc):
        self.finished_value = float(finished_perc)/100 * self.total_value

    def add_finished_percentage(self, finished_perc):
        self.finished_value += float(finished_perc)/100.0*self.total_value

    def percent(self):
        """calculate finished percentage"""
        return float(self.finished_value) / float(self.total_value) if self.total_value else 0.0

    def rate(self):
        """ calculate finishing speed """
        elapsed = datetime.datetime.now() - self.start
        return float(self.total_value - self.finished_value)/float(elapsed.total_seconds())


class Progressbar(object):
    #the factor of width used for progress bar
    percent_bar_factor = 0.4
    def __init__(self, jobs, title='', pool_size=1):
        #total number of jobs
        self.title = title
        self.total = len(jobs)
        self.jobs = jobs
        self.pool_size = pool_size

        #the number of finished jobs
        self.done=0
        self.done2show=[]
        self.success_list=[]
        self.failed_list=[]

    def has_work_to_do(self):
        return self.done < self.total

    def __update_status(self):
        self.success_list = [job for job in self.jobs if job.status == JobStatus.Success]
        self.failed_list = [job for job in self.jobs if job.status == JobStatus.Failed]
        self.done = len(self.success_list) + len(self.failed_list)
        self.done2show = self.success_list[-1:-1-SHOW_DONE_NUMBER:-1]
        self.failed_list = self.failed_list[::-1]
        

    def print_progress(self):
        self.__update_status()
        def output(txt):
            sys.stdout.write(txt)

        width = util.get_terminal_size()[1] -5
        bar_count = (int(width*self.__class__.percent_bar_factor)-2/10) # number of percent bar
        line = log.hl(u' %s\n'% ('+'*width), 'cyan')
        sep = log.hl(u' %s\n'% ('='*width), 'cyan')
        output(u'\x1b[2J\x1b[H') #clear screen
        sys.stdout.write(line)
        header = fmt_dl_header % (self.title, self.pool_size)
        sys.stdout.write(log.hl(u' %s' % header,'warning'))
        sys.stdout.write(line)



        all_p = [] #all progress bars, filled by following for loop
        sum_percent = 0 # total percent for running job
        sum_rate = 0 # total rate for running job
        total_percent = 0
    
        for job in [j for j in self.jobs if j.status == JobStatus.Running]:
            prog_obj = job.progress
            percent = prog_obj.percent()
            #sum for the total progress
            sum_percent += percent

            bar = util.ljust('=' * int(percent * bar_count), bar_count)
            per100 = percent * 100 
            single_p =  fmt_progress % \
                    (util.rjust(prog_obj.name,(width - bar_count)-32), bar, per100) # the -20 is for the xx.x% and [ and ] xx.xkb/s (spaces)
            all_p.append(log.hl(single_p,'green'))
        
        #calculate total progress percent
        total_percent = float(sum_percent+self.done)/self.total
        
        #global progress
        g_text = fmt_dl_progress % (self.done, self.total)
        g_bar = util.ljust('#' * int(total_percent* bar_count), bar_count)
        g_progress =  fmt_progress % \
                    (util.rjust(g_text,(width - bar_count - 32)), g_bar, 100*total_percent) # the -20 is for the xx.x% and [ and ] xx.xkb/s (spaces)

        #output all total progress bars
        sys.stdout.write(log.hl(u'%s'%g_progress, 'red'))
        sys.stdout.write(sep)

        #output all downloads' progress bars
        sys.stdout.write(''.join(all_p))

        # finished jobs
        if len(self.done2show):
            sys.stdout.write(line)
            sys.stdout.write(log.hl(fmt_dl_last_finished % SHOW_DONE_NUMBER,'warning'))
            sys.stdout.write(line)
            #display finished jobs
            for job in self.done2show:
                sys.stdout.write(log.hl(u' √ %s\n'% job.name,'cyan'))

        #failed downloads
        if len(self.failed_list):
            sys.stdout.write(line)
            sys.stdout.write(log.hl(fmt_dl_failed_jobs,'error'))
            sys.stdout.write(line)
            #display failed jobs
            for failed_job in self.failed_list:
                sys.stdout.write(log.hl(u' ✘ %s\n' % failed_job.name,'red'))


        sys.stdout.write(line)
        sys.stdout.flush()


def start_jobs(jobs, title='', threadpool_size=1):
    Terminate_Watcher()
    pool = ThreadPool(threadpool_size)
    executer = Executer(jobs, pool)
    executer.start()
    progress_bar = Progressbar(jobs, title, threadpool_size)
    while progress_bar.has_work_to_do():
        time.sleep(1)
        progress_bar.print_progress()

class Job(object):
    def __init__(self, name, totol_effort=100):
        self.name = name
        self.progress = JobProgress(name, totol_effort )
        self.execute_result = 0
        self.status = JobStatus.Waiting

    def start_work(self):
        self.status = JobStatus.Running
        self.execute_result = self.execute()
        self.__post_execution()
        
    
    def execute(self):
        x = 0
        while x < 5:
            time.sleep(1)
            x+=1
            self.progress.add_finished_percentage(20)
        return 0

    def __post_execution(self):
        self.status = JobStatus.Failed if self.execute_result else JobStatus.Success

class Executer(Thread):
    def __init__(self, jobs, threadpool):
        Thread.__init__(self)
        self.jobs = jobs
        self.pool = threadpool

    def run(self):
        for job in self.jobs:
            self.pool.add_task(job.start_work)
        self.pool.wait_completion()



if __name__ == '__main__':
    jobs =[]
    for x in xrange(1):
        jobs.append(Job("job_"+str(x)))
        
    start_jobs(jobs,'foo',3)
