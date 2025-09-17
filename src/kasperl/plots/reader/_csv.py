import argparse
import csv
import os.path
from typing import List, Iterable, Union

from seppl.io import locate_files
from wai.logging import LOGGING_WARNING

from seppl.placeholders import PlaceholderSupporter, placeholder_list
from kasperl.api import Reader, Plot, XYPlot, SequencePlot


class CsvPlotReader(Reader, PlaceholderSupporter):

    def __init__(self, source: Union[str, List[str]] = None, source_list: Union[str, List[str]] = None,
                 resume_from: str = None, title: str = None, x_data: str = None, x_label: str = None,
                 y_data: str = None, y_label: str = None, separator: str = None,
                 logger_name: str = None, logging_level: str = LOGGING_WARNING):
        """
        Initializes the reader.

        :param source: the filename(s)
        :param source_list: the file(s) with filename(s)
        :param resume_from: the file to resume from (glob)
        :type resume_from: str
        :param title: the title for the plot
        :type title: str
        :param x_data: the 1-based column index for the x values
        :type x_data: str
        :param x_label: the title for the x axis
        :type x_label: str
        :param y_data: the 1-based column index for the y values
        :type y_data: str
        :param y_label: the title for the y axis
        :type y_label: str
        :param separator: the separator to use for the CSV file
        :type separator: str
        :param logger_name: the name to use for the logger
        :type logger_name: str
        :param logging_level: the logging level to use
        :type logging_level: str
        """
        super().__init__(logger_name=logger_name, logging_level=logging_level)
        self.source = source
        self.source_list = source_list
        self.resume_from = resume_from
        self.title = title
        self.x_data = x_data
        self.x_label = x_label
        self.y_data = y_data
        self.y_label = y_label
        self.separator = separator
        self._inputs = None
        self._current_input = None
        self._x_col = None
        self._y_col = None

    def name(self) -> str:
        """
        Returns the name of the handler, used as sub-command.

        :return: the name
        :rtype: str
        """
        return "from-csv-plot"

    def description(self) -> str:
        """
        Returns a description of the reader.

        :return: the description
        :rtype: str
        """
        return "Reads the CSV file and turns the data into data for a plot: an XYPlot when x and y columns specified, " \
               "a SequencePlot when only specifying the y column."

    def _create_argparser(self) -> argparse.ArgumentParser:
        """
        Creates an argument parser. Derived classes need to fill in the options.

        :return: the parser
        :rtype: argparse.ArgumentParser
        """
        parser = super()._create_argparser()
        parser.add_argument("-i", "--input", type=str, help="Path to the CSV file(s) to read; glob syntax is supported; " + placeholder_list(obj=self), required=False, nargs="*")
        parser.add_argument("-I", "--input_list", type=str, help="Path to the text file(s) listing the CSV files to use; " + placeholder_list(obj=self), required=False, nargs="*")
        parser.add_argument("--resume_from", type=str, help="Glob expression matching the file to resume from, e.g., '*/012345.csv'", required=False)
        parser.add_argument("-t", "--title", type=str, help="The title for the plot, default is the file name.", required=False, default=None)
        parser.add_argument("-x", "--x_data", type=str, help="The 1-based index of the column in the CSV file to use for the x values.", required=False, default=None)
        parser.add_argument("-X", "--x_label", type=str, help="The label to use for the x-axis, default is the column name.", required=False, default=None)
        parser.add_argument("-y", "--y_data", type=str, help="The 1-based index of the column in the CSV file to use for the y values.", required=True, default=None)
        parser.add_argument("-Y", "--y_label", type=str, help="The label to use for the y-axis, default is the column name.", required=False, default=None)
        parser.add_argument("-s", "--separator", type=str, help="The separator to use for reading the CSV file.", required=False, default=",")
        return parser

    def _apply_args(self, ns: argparse.Namespace):
        """
        Initializes the object with the arguments of the parsed namespace.

        :param ns: the parsed arguments
        :type ns: argparse.Namespace
        """
        super()._apply_args(ns)
        self.source = ns.input
        self.source_list = ns.input_list
        self.resume_from = ns.resume_from
        self.title = ns.title
        self.x_data = ns.x_data
        self.x_label = ns.x_label
        self.y_data = ns.y_data
        self.y_label = ns.y_label
        self.separator = ns.separator

    def generates(self) -> List:
        """
        Returns the list of classes that get produced.

        :return: the list of classes
        :rtype: list
        """
        return [Plot]

    def initialize(self):
        """
        Initializes the processing, e.g., for opening files or databases.
        """
        super().initialize()
        self._inputs = None
        if self.y_data is None:
            raise Exception("At least the column for the Y values must be specified!")
        self._y_col = int(self.y_data) - 1
        self._x_col = None
        if self.x_data is not None:
            self._x_col = int(self.x_data) - 1
        if self.separator is None:
            self.separator = ","

    def read(self) -> Iterable:
        """
        Loads the data and returns the items one by one.

        :return: the data
        :rtype: Iterable
        """
        if self._inputs is None:
            self._inputs = locate_files(self.source, input_lists=self.source_list, fail_if_empty=True, resume_from=self.resume_from, default_glob="*.csv")
        self._current_input = self._inputs.pop(0)
        self.session.current_input = self._current_input
        self.logger().info("Reading from: " + str(self.session.current_input))

        x = None if (self._x_col is None) else []
        y = []
        x_label = None
        y_label = None
        first = True
        with open(self.session.current_input, "r", newline='') as fp:
            reader = csv.reader(fp, delimiter=self.separator)
            for row in reader:
                # header
                if first:
                    first = False
                    if self._x_col is not None:
                        x_label = row[self._x_col]
                    y_label = row[self._y_col]
                # data
                if self._x_col is not None:
                    x.append(row[self._x_col])
                y.append(row[self._y_col])

        title = self.title if (self.title is not None) else os.path.basename(self.session.current_input)
        meta = {"source": self.session.current_input}
        if self._x_col is not None:
            yield XYPlot(title=title, x_data=x, x_label=x_label, y_data=y, y_label=y_label, metadata=meta)
        else:
            yield SequencePlot(title=title, data=y, label=y_label, metadata=meta)

    def has_finished(self) -> bool:
        """
        Returns whether reading has finished.

        :return: True if finished
        :rtype: bool
        """
        return len(self._inputs) == 0
