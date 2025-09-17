import argparse
from typing import List, Iterable

import plotext_plus as plt
from wai.logging import LOGGING_WARNING

from kasperl.api import make_list, BatchWriter, Plot, XYPlot, SequencePlot
from kasperl.plots.core import PLOT_TYPES, PLOT_LINE, PLOT_SCATTER
from seppl.placeholders import placeholder_list, InputBasedPlaceholderSupporter


class TerminalPlot(BatchWriter, InputBasedPlaceholderSupporter):

    def __init__(self, output: str = None, plot_type: str = None,
                 logger_name: str = None, logging_level: str = LOGGING_WARNING):
        """
        Initializes the writer.

        :param output: the file to write the plot to
        :type output: str
        :param plot_type: the type of plot to generate
        :type plot_type: str
        :param logger_name: the name to use for the logger
        :type logger_name: str
        :param logging_level: the logging level to use
        :type logging_level: str
        """
        super().__init__(logger_name=logger_name, logging_level=logging_level)
        self.output_file = output
        self.plot_type = plot_type

    def name(self) -> str:
        """
        Returns the name of the handler, used as sub-command.

        :return: the name
        :rtype: str
        """
        return "to-terminal-plot"

    def description(self) -> str:
        """
        Returns a description of the writer.

        :return: the description
        :rtype: str
        """
        return "Plots the data directly in the terminal."

    def _create_argparser(self) -> argparse.ArgumentParser:
        """
        Creates an argument parser. Derived classes need to fill in the options.

        :return: the parser
        :rtype: argparse.ArgumentParser
        """
        parser = super()._create_argparser()
        parser.add_argument("-o", "--output", type=str, help="The file to save the plot in. " + placeholder_list(obj=self), required=False, default=None)
        parser.add_argument("-t", "--plot_type", choices=PLOT_TYPES, help="The type of plot to generate.", required=False, default=PLOT_LINE)
        return parser

    def _apply_args(self, ns: argparse.Namespace):
        """
        Initializes the object with the arguments of the parsed namespace.

        :param ns: the parsed arguments
        :type ns: argparse.Namespace
        """
        super()._apply_args(ns)
        self.output_file = ns.output
        self.plot_type = ns.plot_type

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
            self.logger().warning("No data to plot!")
            return
        if len(data) > 1:
            self.logger().warning("Can only plot the first of %d data items!" % len(data))
        data = data[0]

        path = None
        if self.output_file is not None:
            path = self.session.expand_placeholders(self.output_file)

        if isinstance(data, XYPlot):
            if self.plot_type == PLOT_LINE:
                plt.plot(data.x_data, data.y_data)
            elif self.plot_type == PLOT_SCATTER:
                plt.scatter(data.x_data, data.y_data)
            else:
                raise Exception("Unhandled plot type: %s" % self.plot_type)
            x_label = "x" if (data.x_label is None) else data.x_label
            y_label = "y" if (data.y_label is None) else data.y_label
            plt.xlabel(label=x_label)
            plt.ylabel(label=y_label)
        elif isinstance(data, SequencePlot):
            if self.plot_type == PLOT_LINE:
                plt.plot(data.data)
            elif self.plot_type == PLOT_SCATTER:
                plt.scatter(data.data)
            else:
                raise Exception("Unhandled plot type: %s" % self.plot_type)
            label = "value" if (data.label is None) else data.label
            plt.ylabel(label=label)
        else:
            raise Exception("Unhandled plot class: %s" % str(type(data)))

        plt.title("Plot" if (data.title is None) else data.title)
        plt.show()
        if path is not None:
            plt.save_fig(path=path)
