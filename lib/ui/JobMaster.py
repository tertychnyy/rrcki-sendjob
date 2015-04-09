import commands
import os
import time
import sys
from taskbuffer.JobSpec import JobSpec
from taskbuffer.FileSpec import FileSpec
from common.KILogger import KILogger
from ui.Actions import moveData
import userinterface.Client as Client
_logger = KILogger().getLogger("JobMaster")

class JobMaster:
    def __init__(self):
        self.jobList = []
        self.fileList = []
        self.dbname = ''
        self.dbport = 0
        self.dbtimeout = 0
        self.dbuser = ''
        self.dbpasswd = ''

    def putData(self, params=None, fileList=[], fromSEparams=None, toSEparams=None):
        return moveData(params=params, fileList=fileList, params1=fromSEparams, params2=toSEparams)

    def getTestJob(self, site):
        datasetName = 'panda.destDB.%s' % commands.getoutput('uuidgen')
        destName    = 'ANALY_RRC-KI-HPC'

        job = JobSpec()
        job.jobDefinitionID   = int(time.time()) % 10000
        job.jobName           = "%s" % commands.getoutput('uuidgen')
        job.transformation    = '/s/ls2/users/poyda/bio/runbio_wr.py'
        job.destinationDBlock = datasetName
        job.destinationSE     = destName
        job.currentPriority   = 1000
        job.prodSourceLabel   = 'user'
        job.computingSite     = site
        job.cloud             = 'RU'

        job.jobParameters=""

        fileOL = FileSpec()
        fileOL.lfn = "%s.job.log.tgz" % job.jobName
        fileOL.destinationDBlock = job.destinationDBlock
        fileOL.destinationSE     = job.destinationSE
        fileOL.dataset           = job.destinationDBlock
        fileOL.type = 'log'
        fileOL.scope = 'panda'
        job.addFile(fileOL)
        return job

    def submitJobs(self, jobList):
        print 'Submit jobs'
        _logger.debug('Submit jobs')

        s,o = Client.submitJobs(jobList)
        _logger.debug("---------------------")
        _logger.debug(s)
        for x in o:
            _logger.debug("PandaID=%s" % x[0])
        if isinstance( x[0], int ):
            return x[0]
        raise Exception("JobMaster.submitJobs() failed")

    def sendjob(self, data):


        datasetName = 'panda:panda.destDB.%s' % commands.getoutput('uuidgen')
        destName    = 'ANALY_RRC-KI-HPC'
        site = 'ANALY_RRC-KI-HPC'
        scope = 'user.ruslan'

        distributive = data['distributive']
        release = data['release']
        parameters = data['parameters']
        input_type = data['input_type']
        input_params = data['input_params']
        input_files = data['input_files']
        output_type = data['output_type']
        output_params = data['output_params']
        output_files = data['output_files']

        jobid = data['jobid']
        _logger.debug('Jobid: ' + str(jobid))

        job = JobSpec()
        job.jobDefinitionID = int(time.time()) % 10000
        job.jobName = commands.getoutput('uuidgen')
        job.transformation = '/s/ls2/users/poyda/sw/run_wr.py'
        job.destinationDBlock = datasetName
        job.destinationSE = destName
        job.currentPriority = 1000
        job.prodSourceLabel = 'user'
        job.computingSite = site
        job.cloud = 'RU'
        job.prodDBlock = "%s:%s.%s" % (scope, scope, job.jobName)

        job.jobParameters = '%s %s %s' %(release, distributive, parameters)

        params = {}
        _logger.debug('MoveData')
        ec = 0
        ec, uploaded_input_files = self.putData(params=params, fileList=input_files, fromType=input_type, fromParams=input_params, toType='grid', toParams={'dest': job.prodDBlock})
        if ec != 0:
            _logger.error('Move data error: ' + ec[1])
            return

        for file in uploaded_input_files:
            fileIT = FileSpec()
            fileIT.lfn = file
            fileIT.dataset = job.prodDBlock
            fileIT.prodDBlock = job.prodDBlock
            fileIT.type = 'input'
            fileIT.scope = scope
            job.addFile(fileIT)

        for file in output_files:
            fileOT = FileSpec()
            fileOT.lfn = file
            fileOT.destinationDBlock = job.prodDBlock
            fileOT.destinationSE = job.destinationSE
            fileOT.dataset = job.prodDBlock
            fileOT.type = 'output'
            fileOT.scope = scope
            fileOT.GUID = commands.getoutput('uuidgen')
            job.addFile(fileOT)


        fileOL = FileSpec()
        fileOL.lfn = "%s.log.tgz" % job.jobName
        fileOL.destinationDBlock = job.destinationDBlock
        fileOL.destinationSE = job.destinationSE
        fileOL.dataset = job.destinationDBlock
        fileOL.type = 'log'
        fileOL.scope = 'panda'
        job.addFile(fileOL)


        self.jobList.append(job)
        pandaid = self.run()
        if isinstance( pandaid, int ):
            print "Try to update pandaid"
            import MySQLdb
            conn = MySQLdb.connect(host=self.dbhost, db=self.dbname,
                                            port=self.dbport, connect_timeout=self.dbtimeout,
                                            user=self.dbuser, passwd=self.dbpasswd)

            cur = conn.cursor()

            varDict = {}
            varDict['jobid'] = jobid
            varDict['pandaid'] = pandaid
            sql = "UPDATE jobstable SET pandaid=:pandaid WHERE jobid=:jobid"

            cur.execute(sql, varDict)



    def run(self):
        for job in self.jobList:
            jobs = []
            #jobs.append(self.getBuildJob(job))
            #jobs.append(self.getStageInJob(job))
            #jobs.append(self.getExecuteJob(job))
            #jobs.append(self.getStageOutJob(job))

        return self.submitJobs(self.jobList)


