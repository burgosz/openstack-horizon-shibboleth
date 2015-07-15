from datetime import datetime, date
__author__ = 'burgosz'

def log(message):
    logfile = open('log', 'a+')
    logfile.write("{:%H:%M:%d}: ".format(datetime.now()))
    logfile.write("Message: %s.\n" % message)
