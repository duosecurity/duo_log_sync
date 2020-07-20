"""
Definition of the Program class
"""

import logging

class Program:
    """
    The Program class is used not to create objects, but to keep track of this
    program's state and to provide functionality for changing state and
    creating logs or messages.
    """

    # Used to determine whether tasks should continue to run or should begin
    # the shutdown protocol
    _running = True

    # Used to track if logging has been set up. If logging is not set up,
    # print statements will be used in lieu of logs
    _logging_set = False

    @classmethod
    def is_running(cls):
        """
        @return _running
        """

        return cls._running

    @classmethod
    def initiate_shutdown(cls, reason):
        """
        Simply set _running to False which will propogate to all consumers and
        producers causing them to begin the shutdown procedure.

        @param reason   Explanation of why a shutdown was requested
        """

        cls.log(f"DuoLogSync: Shutting down due to [{reason}]", logging.WARNING)
        cls._running = False

    @classmethod
    def setup_logging(cls, log_filepath):
        """
        Function to set up logging, such as saving logs to log_filepath.

        @param log_filepath Filepath where logging messages should be saved
        """

        logging.basicConfig(
            #Where to save logs
            filename=log_filepath,

            #How logs should be formatted
            format='%(asctime)s %(levelname)-8s %(message)s',

            #Minimum level required of a log in order to be seen / written
            level=logging.INFO,

            # Date format to use with logs
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        cls._logging_set = True
        cls.log('Starting DuoLogSync')

    @classmethod
    def log(cls, message, level=logging.INFO):
        """
        Wrapper around the logging.log method with additional functionality to
        use a print statement in the case that logging has yet to be set up

        @param message  A statement to be logged or printed
        @param level    Urgency / value of message
        """

        if cls._logging_set:
            logging.log(level, message)
        else:
            print(message)
