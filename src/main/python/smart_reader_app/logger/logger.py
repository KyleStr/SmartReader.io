import logging
import logging.config


class Logger:
    """
    **Logger**
    """

    def __init__(self, log_conf):
        """

        **__init__**
        This function create an object with predefined configuration

        Args:
            log_conf (str): Logger configuration path

        Returns:
            None: None

        - Example::

            logger_conf = Logger("config/log.conf")

        .. note:: Example of how to use loggers

        """
        self.log_conf = log_conf

    def set_logger_by_name(self, name):
        """

        **Logger**
        This function create an object with predefined configuration

        Args:
            name (str): Logger name (normaly use the python name file)

        Returns:
            None: None

        - Example::

            logger = logger_conf.set_logger_by_name(__name__)

        """
        logging.config.fileConfig(fname=self.log_conf, disable_existing_loggers=False)

        # Get the logger specified in the file
        self.logger = logging.getLogger(name)

        return self
