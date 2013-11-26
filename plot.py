import shapefile
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection
from numpy import array, max
import csv
import operator
import os


def add_commas(float_in):

    tmp = str(int(float_in))
    str_out = ""
    while len(tmp) > 3:
        if str_out:
            str_out = tmp[-3::] + "," + str_out
        else:
            str_out = tmp[-3::]
        tmp = tmp[0:-3]
    str_out = tmp + "," + str_out
    #print str(total) + " vs " + str_out
    return str_out


def map_colors(sf_records, sf_index, values, colormap="Blues", bias=0.0, debug=False):

    colormap = plt.get_cmap(colormap)
    color_list = []
    entry_count = 0

    for record in sf_records:
        rec_index = str(record.record[sf_index])
        try:
            amount = values[rec_index]
            if debug:
                print rec_index + "\t" + add_commas(amount)
            color_list.append(amount)
            entry_count += 1
        except KeyError:
            if debug:
                print rec_index + "\t0"
            color_list.append(0.0)
            pass

    if entry_count == 0:
        raise ValueError, "Warning: Nothing to plot. \n\
        No entry in the input data matched a shape file record. Skipping this data set."

    color_arr = array(color_list)
    total_mapped = sum(color_arr)

    # normalize, but bias the starting point
    max_val = max(color_arr)
    tmp = color_arr/(max_val * (1.0 + bias)) + (1 - 1.0/(1.0 + bias))
    color_arr = tmp

    if debug:
        print "\nMAX: " + str(max_val)
        print "Total (check): " + str(total_mapped) + "\n"

    colors = colormap(color_arr)
    return colors, total_mapped


def plot_map(sf_records, values, colors, headings, prefix, name, plot_options):

    sorted_values = sorted(values.iteritems(), key=operator.itemgetter(1))
    sorted_values.reverse()

    total = 0.0
    for index, amount in sorted_values:
        total += amount
    title_str = add_commas(total)

    for extension in plot_options['formats']:
        fig = plt.figure(figsize=(plot_options['width_inches'], plot_options['height_inches']), dpi=plot_options['dpi'])
        ax = fig.add_subplot(1, 1, 1)
        for i in range(len(sf_records)):
            patches = []
            points = array(sf_records[i].shape.points)
            parts = sf_records[i].shape.parts
            par = list(parts) + [points.shape[0]]
            for pij in range(len(parts)):
                patches.append(Polygon(points[par[pij]:par[pij+1]]))
            ax.add_collection(PatchCollection(patches, facecolor=colors[i, :], edgecolor='k', linewidths=plot_options['line_width']))

        ax.set_xlim(18.1, 19.15)
        ax.set_ylim(-34.45, -33.40)
        ax.set_aspect(1.0)

        ax.get_xaxis().set_visible(False)
        ax.get_yaxis().set_visible(False)

        plt.title(name + " (R" + title_str + ")")

        # TODO: add color bar
        if not os.path.exists("plots/" + extension):
            os.makedirs("plots/" + extension)
        filename = prefix + "-" + name.replace(" ", "_")
        fig.savefig("plots/" + extension + "/" + filename + "." + extension)
        plt.close()

    if not os.path.exists("plots/legend"):
        os.makedirs("plots/legend")
    f = open("plots/legend/" + filename + ".txt", "w")
    heading_str = ""
    for heading in headings:
        heading_str += "\t" + heading
    heading_str = heading_str[1::] + "\r\n"
    f.write(heading_str)
    for index, amount in sorted_values:
        f.write(index + "\t" + add_commas(amount) + "\r\n")
    f.close()


def read_input(filename, data_columns, delimeter='\t'):
    """
    Read an input textfile and categorize the content. The first line is assumed to be column headings.
    """

    index_column, category_columns, target_column = \
        data_columns['index'], data_columns['categories'], data_columns['target']

    data_in = list(csv.reader(open(filename, 'rU'), delimiter=delimeter))
    headings_in = data_in[0]
    data_in = data_in[1::]
    headings_out = [headings_in[index_column], ]
    for col in category_columns:
        headings_out.append(headings_in[col])
    headings_out.append(headings_in[target_column])
    print "\nReading input data file:"
    print "Columns: " + str(headings_out)

    data_out = []
    for row in data_in:
        tmp = [row[index_column], ]
        for col in category_columns:
            tmp.append(row[col])
        tmp.append(float(row[target_column]))
        data_out.append(tmp)
    data_out = sorted(data_out, key=operator.itemgetter(1))
    print str(len(data_out)) + " records read"
    #data_out = [head] + data_out
    return headings_out, data_out


def categorize(data_list, category_col=None):

    if not category_col:
        # calculate overall totals for each item in index column
        total = 0.0
        plot_dict = {}
        for row in data_list:
            if not plot_dict.get(row[0]):
                plot_dict[row[0]] = 0.0
            plot_dict[row[0]] += row[-1]
            total += row[-1]
        return total, plot_dict
    else:
        # calculate totals for each item in index column, broken down by category
        breakdown_dict = {}
        for row in data_list:
            if not breakdown_dict.get(row[category_col]):
                breakdown_dict[row[category_col]] = [0.0, {}]
            if not breakdown_dict[row[category_col]][1].get(row[0]):
                breakdown_dict[row[category_col]][1][row[0]] = 0.0
            breakdown_dict[row[category_col]][0] += row[-1]
            breakdown_dict[row[category_col]][1][row[0]] += row[-1]
        # convert dict to list
        breakdown_list = []
        for category, (total, plot_dict) in breakdown_dict.iteritems():
            breakdown_list.append((category, total, plot_dict))
        return breakdown_list


def assemble_plot_data(data_list):
    """

    """

    print "\nExtracting relevant data for plotting."
    # extract the data relevant to each plot
    total_overall, values_overall = categorize(data_list)  # amounts, grouped by index item
    num_data_sets = 1
    breakdown = []  # list of dicts

    num_categories = len(data_list[0]) - 2
    for i in range(num_categories):
        data_set_list = categorize(data_list, i+1)
        breakdown.append(data_set_list)
        num_data_sets += len(data_set_list)

    print str(num_data_sets) + " data sets ready for plotting."
    return total_overall, values_overall, breakdown


def read_shape_file(path):

    print "\nReading shapefile records."
    sf = shapefile.Reader(path)

    # extract list of record objects
    records = sf.shapeRecords()
    print str(len(records)) + " records in shapefile."
    print "The following fields are available from the shapefile:"
    print sf.fields
    for i in range(len(sf.fields)):
        if not i == 0:
            print str(i-1) + "\t" + sf.fields[i][0] + ", e.g. " + str(records[0].record[i - 1])
    return records


def generate_plot(sf_records, sf_index, values, headings, plot_options, prefix, filename):

    try:
        # map data to colors
        colors, total_mapped = map_colors(sf_records, sf_index, values, plot_options['colormap'], plot_options['bias'])

        # plot colors and shape records
        plot_map(sf_records, values, colors, headings, prefix, filename, plot_options)
    except ValueError as e:
        print e
        pass
    return


def generate_plot_set(data_file, data_columns, shape_file, shape_file_index, plot_options):

    if not os.path.exists("plots"):
        os.makedirs("plots")

    # Read input data, specifying the index column, which is used for matching to the shapefile,
    # as well as the target column with the values to be plotted. Further columns can optionally
    # be specified for breaking down the data set into categories.

    headings, data = read_input(data_file, data_columns)

    # Process input data, grouping it by some target column, and optionally categorizing it by another.
    total_overall, values_overall, breakdown = assemble_plot_data(data)
    print "Overall total: " + add_commas(total_overall)

    # Read shapefile
    sf_records = read_shape_file(shape_file)
    sf_index = shape_file_index  # the column that is used for joining to the input data set

    # Project values onto a color map.

    for extension in plot_options['formats']:
        # Plot summary map.
        tmp_head = [headings[0], headings[-1]]
        generate_plot(sf_records, sf_index, values_overall, tmp_head, plot_options, '0', 'Total')

        # Plot breakdown maps.
        for i in range(len(breakdown)):
            data_set_list = breakdown[i]
            num_digits = len(str(len(data_set_list)))  # used in prefixes for file names
            for j in range(len(data_set_list)):
                category_name, tmp_subtotal, tmp_values = data_set_list[j]
                print tmp_values
                tmp = "{0:0" + str(num_digits) + "d}"
                prefix = tmp.format(j+1)
                prefix = str(i+1) + prefix
                generate_plot(sf_records, sf_index, tmp_values, tmp_head, plot_options, prefix, category_name)
    return


if __name__ == "__main__":

    data_file = 'city_budget.txt'

    data_columns = {}
    data_columns['index'] = -2
    data_columns['categories'] = [1, 3]
    data_columns['target'] = -4

    shape_file = "shapefiles_cape_town/wards.shp"
    shape_file_index = 3
    extensions = ['png', 'svg']

    # For all available colormaps, see http://matplotlib.org/examples/color/colormaps_reference.html
    colormaps = [
        'binary',
        'Blues',
        'Greens',
        'Oranges',
        'OrRd',
        'Reds',
    ]

    plot_options = {
        'colormap': colormaps[1],
        'formats': ['png', 'svg'],
        'bias': 0.2,
        'line_width': 0.2,
        'width_inches': 8,
        'height_inches': 8.5,
        'dpi': 100,
    }

    generate_plot_set(data_file, data_columns, shape_file, shape_file_index, plot_options)