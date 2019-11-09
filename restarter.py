'''
Date: August 2018
Short script with CLI to be used for restarting others scripts.
Parameters which can be defined script, duration of loop, number of threads 
'''
import argparse
import logging
from subprocess import Popen
import time

logging.basicConfig(level=logging.DEBUG, format = '%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser()
parser.add_argument('-s', '--script', action="store", dest="script", help = 'name of script, e.q. : helloworld.py')
parser.add_argument('-i', '--interval', action="store", dest="interval", type=int, help = 'duration of loop in seconds, e.g. 10')
parser.add_argument('-t', '--threads', action="store", dest="threads", type=int, default = 1, help = 'number of threads, default is 1')
parser.add_argument('-d', '--delay', action="store", dest="delay", type=int, default = 0, help = 'delay between running next process, default is 0')
settings = parser.parse_args()

def restarter(interval = settings.interval, script = settings.script, threads = settings.threads, delay = settings.delay):
    '''
    starts script after defined interval of seconds will restart script and so on and so on
    infinite loop
    ============
    parameters:
        interval: time in seconds between start of script and killing of script, e.g. : 10
        script: name of script, e.q. : 'helloworld.py'
        threads: number of scripts, default is 1 
    '''
    logger.debug('Restarter starts')
    while True:
        data = []
        for i in range(threads):
            try:
                data.append(Popen(['python3', script]))
                if delay:
                    time.sleep(delay)
            except:
                data.append(Popen(['python', script]))
                if delay:
                    time.sleep(delay)
        time.sleep(interval)
        for item in data:
            item.kill()
    
if __name__ == "__main__":
    restarter()
