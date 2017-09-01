import logging
import numpy as np
from cycler import cycler
from itertools import cycle
import matplotlib.pyplot as plt
import palettable

def create_graph(title, x_label, y_label, X, data_list, plots, options):
    if plots is not None:
        count = 0
        graph_type = 'normal'
        if options is not None and 'graph_type' in options:
            graph_type = options['graph_type']
        # switch
        if graph_type == 'subplot':
            # FIXME unsafe assumption...
            (count, fig) = create_subplot(x_label, y_label, X, data_list, plots[0], options)
            if count > 0:
                #fig.legend(fancybox=True, loc='best').draggable()
                fig.suptitle(title)
                fig.tight_layout()
                #plt.xlabel(x_label)
                #plt.ylabel(y_label)
                plt.show()
            else:
                logging.info('Nothing to graph, moving on...')
        elif graph_type == 'normal':
            for plot in plots:
                count += create_basicplot(X, data_list, options, **plot)
            if count > 0:
                plt.legend(fancybox=True, loc='best').draggable()
                plt.title(title)
                plt.xlabel(x_label)
                plt.ylabel(y_label)
                plt.show()
            else:
                logging.info('Nothing to graph, moving on...')
        else: #
            logging.error('Value for `graph_type\' -> "{:s}" is not supported!'.format(options['graph_type']))
            sys.exit()

def create_subplot(x_label, y_label, X, data_list, plot, options):
    num_data = len(data_list)
    cols = 2
    rows = _round_nearest_divide(num_data, cols)
    total_plots = cols * rows
    count = 0
    fig = plt.figure()
    # FIXME what to do when we have different plots? disallow?
    if 'config' in plot and 'ylimit' in plot['config']:
        ylimits = plot['config']['ylimit']
    else:
        ylimits = compute_max_ylimit(data_list, X, *plot['data'].keys())
    for num, data_name in enumerate(data_list.keys()):
        plt.subplot(rows, cols, num+1, autoscaley_on=False)
        count += create_plot(X, data_name, data_list[data_name], options, **plot)
        plt.ylim(ylimits)
        plt.legend(fancybox=True, loc='best').draggable()
        plt.title(data_name)
        plt.xlabel(x_label)
        plt.ylabel(y_label)
    return (count, fig)

def create_basicplot(X, data_list, options, **plot):
    if plot is not None and 'data' in plot:
        count = 0
        # get the plot type, default: errorbar
        plot_type = 'errorbar'
        if 'config' in plot and 'type' in plot['config']:
            plot_type = plot['config']['type']
        # get xskip value
        if len(X) < 10:
            xlabel_skip_value = 1
        else:
            xlabel_skip_value = 5
        xskip_value = 1
        if options is not None and 'xskip' in options:
            xskip_value = options['xskip']
            xlabel_skip_value = int(xskip_value/xlabel_skip_value) if int(xskip_value/xlabel_skip_value) != 0 else 1
            # edit inplace (XXX is this safe)?
            X = X[::xskip_value]
        # get num of data
        num_data = len(data_list)
        # get axes instance
        axes = plt.gca()
        # set color cycles
        plt.rc('axes', prop_cycle=(
            cycler('color', palettable.colorbrewer.diverging.Spectral_11.mpl_colors)
        ))
        markerfacecycle = cycle(palettable.colorbrewer.diverging.Spectral_11_r.mpl_colors)
        # set marker cycles
        markercycle = cycle(['8', 'X', 'P', '*', 's', 'd', 'p'])
        for lcount, data in enumerate(data_list.keys()):
            bottom = np.zeros(len(X)) # used for overlaping bars (stackbar)
            ddcount = 1
            for dcount, (key, value) in enumerate(plot['data'].items()):
                if key not in data_list[data][str(X[0])]:
                    logging.info('Looks like we aren\'t meant to graph `{:s}\', key {:s} not found, skipping...'.format(data, key))
                    ddcount += 1
                    continue
                else:
                    # get plus-minus values, if they exist
                    tmp_y = dict([('Y', []), ('+-', [[],[]])])
                    for x in X:
                        try:
                            tmp_y['Y'].append(data_list[data][str(x)][key][value][0])
                            tmp_y['+-'][0].append(data_list[data][str(x)][key][value][1])
                            tmp_y['+-'][1].append(data_list[data][str(x)][key][value][2])
                        except KeyError as e:
                            logging.warn('Unable to access {:s} -> {:s} in {:s}'.format(key, e, data))
                            pass
                    # get base x-indices
                    X2 = np.arange(len(X))
                    # set width of x-indices (mainly useful for bar graphs)
                    width = np.min(0.8/num_data)
                    # set axes x-tick limits
                    # switch
                    if plot_type == 'errorbar':
                        if tmp_y['+-']:
                            plt.errorbar(X2+(width*lcount), tmp_y['Y'], yerr=tmp_y['+-'], lolims=True, uplims=True, label='{:s} - {:s}'.format(data, key), marker=next(markercycle), markerfacecolor=next(markerfacecycle))
                        else:
                            plt.errorbar(X2+(width*lcount), tmp_y['Y'], label='{:s} - {:s}'.format(data, key), dashes=(1,1), marker=markercycle.next(), markerfacecolor=markerfacecycle.next())
                    elif plot_type == 'bar':
                        if tmp_y['+-']:
                            plt.bar(X2+(width*lcount), tmp_y['Y'], width=width, yerr=tmp_y['+-'], label='{:s} - {:s}'.format(data, key))
                        else:
                            plt.bar(X2+(width*lcount), tmp_y['Y'], width=width, label='{:s} - {:s}'.format(data, key))
                    elif plot_type == 'stackbar':
                        if tmp_y['+-']:
                            rects = plt.bar(X2+(width*lcount), tmp_y['Y'], width=width, yerr=tmp_y['+-'], edgecolor='white', bottom=bottom, label='{:s} - {:s}'.format(data, key))
                        else:
                            rects = plt.bar(X2+(width*lcount), tmp_y['Y'], width=width, edgecolor='white', bottom=bottom, label='{:s} - {:s}'.format(data, key))
                        if dcount == len(plot['data']) - ddcount: # we have reach the end
                            add_bar_label(rects, plt.gca(), data, bottom)
                        else:
                            bottom += np.array(tmp_y['Y'])
                    else:
                        logging.error('Plot type `{:s}\' is not supported!'.format(plot_type))
                        sys.exit()
                    # set ticks based on X setting
                    plt.xticks((X2+(width*lcount/2.0))[::xlabel_skip_value], X[::xlabel_skip_value])
                    count += 1 # used to enumerate the plot stack - for which there is no len() method
        return count

def create_plot(X, data_name, data_dict, options, **plot):
    count = 0
    if plot is not None and 'data' in plot:
        # get the plot type, default: errorbar
        plot_type = 'errorbar'
        if 'config' in plot and 'type' in plot['config']:
            plot_type = plot['config']['type']
        # get xskip value
        if len(X) < 10:
            xlabel_skip_value = 1
        else:
            xlabel_skip_value = 5
        xskip_value = 1
        if options is not None and 'xskip' in options:
            xskip_value = options['xskip']
            xlabel_skip_value = int(xskip_value/xlabel_skip_value) if int(xskip_value/xlabel_skip_value) != 0 else 1
            # edit inplace (XXX is this safe)?
            X = X[::xskip_value]
        # get axes instance
        axes = plt.gca()
        # set color cycles
        plt.rc('axes', prop_cycle=(
            cycler('color', palettable.colorbrewer.diverging.Spectral_11.mpl_colors)
        ))
        markerfacecycle = cycle(palettable.colorbrewer.diverging.Spectral_11_r.mpl_colors)
        # set marker cycles
        markercycle = cycle(['8', 'X', 'P', '*', 's', 'd', 'p'])
        bottom = np.zeros(len(X)) # used for overlaping bars (stackbar)
        ddcount = 1
        num_data = len(plot['data'])
        for dcount, (key, value) in enumerate(plot['data'].items()):
            if key not in data_dict[str(X[0])]:
                logging.info('Looks like we aren\'t meant to graph `{:s}\', key {:s} not found, skipping...'.format(data_name, key))
                ddcount += 1
                continue
            else:
                # get plus-minus values, if they exist
                tmp_y = dict([('Y', []), ('+-', [[],[]])])
                for x in X:
                    try:
                        tmp_y['Y'].append(data_dict[str(x)][key][value][0])
                        tmp_y['+-'][0].append(data_dict[str(x)][key][value][1])
                        tmp_y['+-'][1].append(data_dict[str(x)][key][value][2])
                    except KeyError as e:
                        logging.warn('Unable to access {} -> {} in {}'.format(key, e, data_name))
                        pass
                # get base x-indices
                X2 = np.arange(len(X))
                # set width of x-indices (mainly useful for bar graphs)
                width = np.min(0.8/num_data)
                # set axes x-tick limits
                # switch
                if plot_type == 'errorbar':
                    if tmp_y['+-']:
                        plt.errorbar(X2+(width*dcount), tmp_y['Y'], yerr=tmp_y['+-'], lolims=True, uplims=True, label='{:s} - {:s}'.format(data_name, key), marker=next(markercycle), markerfacecolor=next(markerfacecycle))
                    else:
                        plt.errorbar(X2+(width*dcount), tmp_y['Y'], label='{:s} - {:s}'.format(data_name, key), dashes=(1,1), marker=markercycle.next(), markerfacecolor=markerfacecycle.next())
                elif plot_type == 'bar':
                    if tmp_y['+-']:
                        plt.bar(X2+(width*dcount), tmp_y['Y'], width=width, yerr=tmp_y['+-'], label='{:s} - {:s}'.format(data_name, key))
                    else:
                        plt.bar(X2+(width*dcount), tmp_y['Y'], width=width, label='{:s} - {:s}'.format(data_name, key))
                elif plot_type == 'stackbar':
                    if tmp_y['+-']:
                        rects = plt.bar(X2+(width*dcount), tmp_y['Y'], width=width, yerr=tmp_y['+-'], edgecolor='white', bottom=bottom, label='{:s} - {:s}'.format(data_name, key))
                    else:
                        rects = plt.bar(X2+(width*dcount), tmp_y['Y'], width=width, edgecolor='white', bottom=bottom, label='{:s} - {:s}'.format(data_name, key))
                    if dcount == len(plot['data']) - ddcount: # we have reach the end
                        add_bar_label(rects, plt.gca(), data_name, bottom)
                    else:
                        bottom += np.array(tmp_y['Y'])
                else:
                    logging.error('Plot type `{:s}\' is not supported!'.format(plot_type))
                    sys.exit()
                # set ticks based on X setting
                plt.xticks((X2+(width*dcount/2.0))[::xlabel_skip_value], X[::xlabel_skip_value])
                count += 1 # used to enumerate the plot stack - for which there is no len() method
    return count

def add_bar_label(rects, axes, label, hadjust=None):
    '''
    Based off of http://composition.al/blog/2015/11/29/a-better-way-to-add-labels-to-bar-charts-with-matplotlib/
    '''
    (y_bottom, y_top) = axes.get_ylim()
    y_height = y_top - y_bottom
    if hadjust is not None and len(hadjust) == len(rects):
        h_adjust = hadjust
    else:
        h_adjust = [0.0] * len(rects)
    for j, rect in enumerate(rects):
        height = rect.get_height() + h_adjust[j]
        p_height = (height / y_height)
        if p_height > 0.95:
            label_position = height - (y_height * 0.05)
        else:
            label_position = height + (y_height * 0.01)
        axes.text(rect.get_x() + rect.get_width()/2., label_position,
                '{:s}'.format(label),ha='center', va='bottom', rotation=90)

def _round_nearest_divide(a, b):
    q, r = divmod(a, b)
    return q + int(2 * r >= b)

def compute_ylimit_pplot(in_dict, X, *keys):
    if keys is not None:
        out_dict = dict()
        for idk in in_dict.keys():
            out_dict[idk] = list((0.0,0.0))
            for x in X:
                for key in keys:
                    try:
                        tmp = np.array(in_dict[idk][str(x)][key]['all'], dtype=float)
                        amin = np.amin(tmp)
                        amax = np.amax(tmp)
                        out_dict[idk][0] = np.minimum(out_dict[idk][0], amin).tolist()
                        out_dict[idk][1] = np.maximum(out_dict[idk][1], amax).tolist()
                    except KeyError:
                        logging.warn('Key `{}\' not found, did you miss type something?'.format(key))
                        continue
        return out_dict

def compute_max_ylimit(in_dict, X, *keys):
    if keys is not None:
        tmp_dict = compute_ylimit_pplot(in_dict, X, *keys)
        max_ylimit = list((0.0,0.0))
        for key in tmp_dict.keys():
            max_ylimit[0] = np.minimum(max_ylimit[0], tmp_dict[key][0])
            max_ylimit[1] = np.maximum(max_ylimit[1], tmp_dict[key][1])
        return max_ylimit
    else:
        return list()

