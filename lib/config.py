"""
this module manages the configuration
"""
import ConfigParser


class Config(ConfigParser.SafeConfigParser):
    """ this class manages the configuration """
    def read(self, configuration_file):
        """reads a configuration file"""
        self.read(configuration_file)
