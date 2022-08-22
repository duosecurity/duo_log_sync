"""
Definition of the Program class
"""

import logging
from logging.handlers import RotatingFileHandler


class ProgramShutdownError(Exception):
    """
    Raise when the program is no longer running and a task needs to begin
    shutdown procedures. Definition is inherited from the Exception class
    """

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
    def is_logging_set(cls):
        """
        @return _logging_set
        """

        return cls._logging_set

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

        try:
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
            
            #  Log rotation, allows for 3 rotations, each at 25MB.
            logger = logging.getLogger()
            handler = RotatingFileHandler(log_filepath, maxBytes=26214400, backupCount=3)
            logger.addHandler(handler)

        except FileNotFoundError as file_not_found_error:
            cls.log(f"DuoLogSync: Could not follow the path {log_filepath}. "
                    "Make sure the directories in the filepath exist.")
            cls.initiate_shutdown(f"{file_not_found_error}")
            return

        cls._logging_set = True
        cls.log('Starting DuoLogSync', logging.INFO)

    @classmethod
    def log(cls, message, level=logging.ERROR):
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
