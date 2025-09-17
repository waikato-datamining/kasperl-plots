import argparse
import csv
from typing import List, Iterable

from wai.logging import LOGGING_WARNING

from kasperl.api import make_list, BatchWriter, Plot, XYPlot, SequencePlot
from seppl.placeholders import placeholder_list, InputBasedPlaceholderSupporter


class CsvPlotWriter(BatchWriter, InputBasedPlaceholderSupporter):

    def __init__(self, output: str = None, separator: str = None,
                 logger_name: str = None, logging_level: str = LOGGING_WARNING):
        """
        Initializes the writer.

        :param output: the file to write the plot data to
        :type output: str
        :param separator: the separator to use for the CSV file
        :type separator: str
        :param logger_name: the name to use for the logger
        :type logger_name: str
        :param logging_level: the logging level to use
        :type logging_level: str
        """
        super().__init__(logger_name=logger_name, logging_level=logging_level)
        self.output_file = output
        self.separator = separator

    def name(self) -> str:
        """
        Returns the name of the handler, used as sub-command.

        :return: the name
        :rtype: str
        """
        return "to-csv-plot"

    def description(self) -> str:
        """
        Returns a description of the writer.

        :return: the description
        :rtype: str
        """
        return "Saves just the plot data as CSV file."

    def _create_argparser(self) -> argparse.ArgumentParser:
        """
        Creates an argument parser. Derived classes need to fill in the options.

        :return: the parser
        :rtype: argparse.ArgumentParser
        """
        parser = super()._create_argparser()
        parser.add_argument("-o", "--output", type=str, help="The file to save the plot data in. " + placeholder_list(obj=self), required=True)
        parser.add_argument("-s", "--separator", type=str, help="The separator to use for writing the CSV file.", required=False, default=",")
        return parser

    def _apply_args(self, ns: argparse.Namespace):
        """
        Initializes the object with the arguments of the parsed namespace.

        :param ns: the parsed arguments
        :type ns: argparse.Namespace
        """
        super()._apply_args(ns)
        self.output_file = ns.output
        self.separator = ns.separator

    def accepts(self) -> List:
        """
        Returns the list of classes that are accepted.

        :return: the list of classes
        :rtype: list
        """
        return [Plot]

    def write_batch(self, data: Iterable):
        """
        Saves the data in one go.

        :param data: the data to write
        :type data: Iterable
        """
        data = make_list(data)
        if len(data) == 0:
            self.logger().warning("No data to save!")
            return
        if len(data) > 1:
            self.logger().warning("Can only save the first of %d data items!" % len(data))
        data = data[0]
        path = self.session.expand_placeholders(self.output_file)
        with open(path, "w", newline='') as fp:
            writer = csv.writer(fp, delimiter=self.separator)
            if isinstance(data, XYPlot):
                x_label = "x" if (data.x_label is None) else data.x_label
                y_label = "y" if (data.y_label is None) else data.y_label
                writer.writerow([x_label, y_label])
                for x, y in zip(data.x_data, data.y_data):
                    writer.writerow([x, y])
            elif isinstance(data, SequencePlot):
                label = "value" if (data.label is None) else data.label
                writer.writerow([label])
                for value in data.data:
                    writer.writerow([value])
            else:
                raise Exception("Unhandled plot class: %s" % str(type(data)))
