import matplotlib.pyplot as plt
import numpy as np
import logging
from config import _LOG_LEVEL

# Visuals


def _format_plot(
    x_title=None,
    y_title=None,
    x_label_rot=None,
    y_label_rot=None,
    x_labels=None,
    y_labels=None,
    title=None,
):
    if title:
        plt.title(title)
    if x_title:
        plt.xlabel = x_title
    if y_title:
        plt.ylabel = y_title
    if x_label_rot:
        plt.xticks(rotation=x_label_rot)
    if y_label_rot:
        plt.yticks(rotation=y_label_rot)


def make_bar_plot(
    x_axis,
    y_axis,
    x_title=None,
    y_title=None,
    x_label_rot=None,
    y_label_rot=None,
    x_labels=None,
    y_labels=None,
    title=None,
):
    plt.bar(x_axis, y_axis)

    _format_plot(x_title, y_title, x_label_rot, y_label_rot, x_labels, y_labels, title)

    for bar in ax.patches:
        # The text annotation for each bar should be its height.
        bar_value = bar.get_height()
        # Format the text with commas to separate thousands. You can do
        # any type of formatting here though.
        text = f'{bar_value:,}'
        # This will give the middle of each bar on the x-axis.
        text_x = bar.get_x() + bar.get_width() / 2
        # get_y() is where the bar starts so we add the height to it.
        text_y = bar.get_y() + bar_value
        # If we want the text to be the same color as the bar, we can
        # get the color like so:
        bar_color = bar.get_facecolor()
        # If you want a consistent color, you can just set it as a constant, e.g. #222222
        ax.text(text_x, text_y, text, ha='center', va='bottom', color=bar_color,
                size=12)

    plt.show()


def make_group_bar_plot(
    x_axis,
    y_axis,
    x_title=None,
    y_title=None,
    x_label_rot=None,
    y_label_rot=None,
    x_labels=None,
    y_labels=None,
    title=None,
    path=None
):
    fig, ax = plt.subplots(figsize=(12, 8))

    bar_width = float(0.2)
    x = np.arange(len(x_axis))

    acc = 0
    for data in y_axis:
        a_bar = ax.bar([val + acc for val in x], data, width=bar_width)
        acc = acc + bar_width

    # Fix the x-axes.
    ax.set_xticks([val + bar_width * 2 / 3 for val in x])
    ax.set_xticklabels(x_axis)

    _format_plot(x_title, y_title, x_label_rot, y_label_rot, x_labels, y_labels, title)

    # Axis styling.
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_color("#DDDDDD")
    ax.tick_params(bottom=False, left=False)
    ax.set_axisbelow(True)
    ax.yaxis.grid(True, color="#EEEEEE")
    ax.xaxis.grid(False)
    # Add axis and chart labels.
    ax.set_xlabel(x_title, labelpad=15)
    ax.set_ylabel(y_title, labelpad=15)
    fig.tight_layout()

    # For each bar in the chart, add a text label.
    for bar in ax.patches:
        # The text annotation for each bar should be its height.
        bar_value = bar.get_height()
        # Format the text with commas to separate thousands. You can do
        # any type of formatting here though.
        text = f'{bar_value:,}'
        # This will give the middle of each bar on the x-axis.
        text_x = bar.get_x() + bar.get_width() / 2
        # get_y() is where the bar starts so we add the height to it.
        text_y = bar.get_y() + bar_value
        # If we want the text to be the same color as the bar, we can
        # get the color like so:
        bar_color = bar.get_facecolor()
        # If you want a consistent color, you can just set it as a constant, e.g. #222222
        ax.text(text_x, text_y, text, ha='center', va='bottom', color=bar_color,
                size=12)

    if not (path is None):
        fig.savefig(path + ".png", bbox_inches='tight', dpi=150)
    else:
        plt.show()


_logger = logging.getLogger(__name__)
_logger.setLevel(_LOG_LEVEL)
