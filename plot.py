import shapefile
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection
from numpy import array, max
import csv
import operator


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


def get_colors(records, values):

    colormap = plt.get_cmap('Blues')
    color_list = []

    for record in records:
        ward = str(record.record[3])
        try:
            amount = values[ward]
            print ward + "\t" + add_commas(amount)
            color_list.append(amount)
        except KeyError:
            print "empty ward: " + ward
            color_list.append(0.0)

    color_arr = array(color_list)
    total = sum(color_arr)
    # normalize, but bias the starting point
    max_val = max(color_arr)
    tmp = color_arr/(max_val * 1.25) + (1 - 1.0/1.25)

    # keep zero-valued entries white
    for i in range(len(color_arr)):
        if not color_arr[i]:
            tmp[i] = 0.0
    color_arr = tmp

    print "MAX: " + str(max_val)
    print "Total (check): " + str(total)

    # print a sorted list of totals for each ward
    sorted_breakdown = sorted(values.iteritems(), key=operator.itemgetter(1))
    sorted_breakdown.reverse()

    colors = colormap(color_arr)
    return colors, total, sorted_breakdown


def plot_map(records, colors, directory, name, extension, counter, sorted_breakdown):

    fig = plt.figure(figsize=(8, 8.5), dpi=100)
    ax = fig.add_subplot(1, 1, 1)
    for i in range(num_recs):
        patches = []
        points = array(records[i].shape.points)
        parts = records[i].shape.parts
        par = list(parts) + [points.shape[0]]
        for pij in range(len(parts)):
            patches.append(Polygon(points[par[pij]:par[pij+1]]))
        ax.add_collection(PatchCollection(patches, facecolor=colors[i, :], edgecolor='k', linewidths=.2))

    ax.set_xlim(18.1, 19.15)
    ax.set_ylim(-34.45, -33.40)
    ax.set_aspect(1.0)

    ax.get_xaxis().set_visible(False)
    ax.get_yaxis().set_visible(False)

    total = 0.0
    for ward, amount in sorted_breakdown:
        total += amount
    title_str = add_commas(total)

    plt.title(name + " (R" + title_str + ")")

    # TODO: add colorbar
    filename = str(counter) + "-" + name.replace(" ", "_")
    if name == "Total Capital Spend":
        fig.savefig(directory + filename + extension)
    else:
        if extension == ".png":
            fig.savefig(directory + "png/" + filename + extension)
        else:
            fig.savefig(directory + "svg/" + filename + extension)
    plt.close()

    if name == "Total Capital Spend":
        f = open(directory + filename + ".txt", "w")
    else:
        f = open(directory + "legend/" + filename + ".txt", "w")
    f.write("WARD NO. \tAMOUNT (Rands)\r\n")
    for ward, total in sorted_breakdown:
        f.write(str(ward) + "\t" + add_commas(total) + "\r\n")
    f.close()


def read_input(filename, index_column, category_columns, target_column, delimeter='\t'):
    """
    Read an input textfile and categorize the content. The first line is assumed to be column headings.
    """

    data = list(csv.reader(open(filename, 'rU'), delimiter=delimeter))
    headings = data[0]
    data = data[1::]
    head = [headings[index_column], ]
    for col in category_columns:
        head.append(headings[col])
    head.append(headings[target_column])
    print "Reading input data file, columns: " + str(head)

    data_out = []
    for row in data:
        tmp = [row[index_column], ]
        for col in category_columns:
            tmp.append(row[col])
        tmp.append(float(row[target_column]))
        data_out.append(tmp)
    data_out = sorted(data_out, key=operator.itemgetter(1))
    print str(len(data_out)) + " records read"
    #data_out = [head] + data_out
    return data_out


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

    # extract the data relevant to each plot
    total_overall, values_overall = categorize(data_list)  # amounts, grouped by index item
    breakdown = []  # list of dicts

    num_categories = len(data_list[0]) - 2
    for i in range(num_categories):
        breakdown.append(categorize(data_list, i+1))
    return total_overall, values_overall, breakdown


if __name__ == "__main__":

    categories = [1, 3]  # directorate and department

    # read input csv
    data = read_input('city_budget.txt', -2, categories, -4)

    # categorize the data
    total_overall, values_overall, breakdown = assemble_plot_data(data)
    print total_overall
    print values_overall
    print len(breakdown)
    print len(breakdown[0])
    print len(breakdown[1])


    ## read input shapefile
    #print "\n------------ READING SHAPEFILE --------------"
    #sf = shapefile.Reader("./shapefiles_cape_town/wards.shp")
    #
    ## extract list of record objects
    #records = sf.shapeRecords()
    #num_recs = len(records)
    #print "Number of records: ", str(num_recs)
    #print sf.fields
    #print records[55].record
    #print records[0].record[3]
    #
    #
    #print "\n------------ CALCULATING COLORS --------------"
    #colors_tot, total, sorted_breakdown = get_colors(records, values_tot)
    #colors_cat = {}
    #for category, values in values_cat.iteritems():
    #    tmp_colors, tmp_total, tmp_sorted_breakdown = get_colors(records, values)
    #    colors_cat[category] = (tmp_colors, tmp_total, tmp_sorted_breakdown)
    #
    #
    #print "\n------------ PLOTTING MAP --------------"
    #plot_map(records, colors_tot, "plots/", 'Total Capital Spend', '.png', 0, sorted_breakdown)
    #plot_map(records, colors_tot, "plots/", 'Total Capital Spend', '.svg', 0, sorted_breakdown)
    #
    #i = 1
    #for category, vals in colors_cat.iteritems():
    #    tmp_colors, tmp_total, tmp_sorted_breakdown = vals
    #    if tmp_total > 0.0:
    #        plot_map(records, tmp_colors, config[0], category, '.png', i, tmp_sorted_breakdown)
    #        plot_map(records, tmp_colors, config[0], category, '.svg', i, tmp_sorted_breakdown)
    #    i += 1
