class LoggingHook(object):
    '''
    Simple logging hook for the processors to log what's happening
    '''
    def __init__(self, logger, level):
        self.logger = logger
        self.level = level

    def notify_me(self, processor_name, event_type, message):
        self.logger.log(self.level, '%s - %s : %s' % (processor_name, event_type, message))
