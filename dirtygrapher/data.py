import sys
import logging
import numpy as np
from pint import UnitRegistry

def _rec_get_data(data, *keys):
    if keys:
        value = data[keys[0]]
        left_keys = keys[1:]
        return _rec_get_data(value, *left_keys)
    else:
        return data

# depth = len( namespace == (a, b, ...) )
def collect_data(data, **keys):
    """
    Return a dictionary of key-values pairs based upon the lookup
    path given as input to the data input. If no lookup path is
    given, return a empty dictionary. Error out in the case where
    the path cannot be resolved.

    Note: this function is strict on lookup paths, that they be
          specified as a tuple of arguments, e.g. `foo=('bar',)`
          or `baz=('hello','kitty',0)`
    """
    return collect_data_from_set(data, None, **keys)

def collect_data_from_set(data, fset, **keys):
    in_dict = dict()
    collect_data_from_set_update(data, in_dict, fset, **keys)
    return in_dict

def collect_data_from_set_update(data, in_dict, fset, **keys):
    if keys is not None:
        ureg = UnitRegistry()
        ureg.define('Kilo- = 1e3 = K-') # override SI standard kilo (k)
        for i in data:
            for k in i:
                if fset is None or fset == k['test']['name']:
                    test_type = k['test']['name']
                else:
                    break
                size = str(k['test']['size'][0])
                # we need to make sure that keys exist...
                if test_type not in in_dict:
                    in_dict[test_type] = dict()
                if size not in in_dict[test_type]:
                    in_dict[test_type][size] = dict()
                for key, value in keys.items():
                    try:
                        if 'unit' in value and 'baseunit' in value:
                            tmp = normalise_value(ureg, _rec_get_data(k, *value['path']), _rec_get_data(k, *value['unit']), value['baseunit'])
                        else:
                            tmp = _rec_get_data(k, *value['path'])
                        if key not in in_dict[test_type][size]:
                            in_dict[test_type][size][key] = dict([('all',list())])
                        in_dict[test_type][size][key]['all'].append(tmp)
                    except KeyError:
                        logging.warn('Path `{}\' not in `{}\''.format(value['path'], key))
                        continue

def drop_x_data(test, xlist):
    if test is not None:
        for jdk in test.keys():
            if int(jdk) not in xlist:
                del test[jdk]

def drop_not_listed(test, xdict):
    if test is not None:
        for jdk, value in test.iteritems():
            pass

def compute_fold(in_dict, func, *params):
    if func is not None:
        for idk in in_dict.keys(): # data/test set
            func(in_dict[idk], *params)

def compute_median(in_dict, *keys):
    compute_mean_median(in_dict, -1, *keys)

def compute_mean(in_dict, *keys):
    compute_mean_median(in_dict, 1, *keys)

def compute_mean_median(in_dict, what, *keys):
    if keys is not None:
        for idk in in_dict.keys(): # data/test set
            for jdk in in_dict[idk].keys(): # X value
                for key in keys:
                    try:
                        tmp = np.array(in_dict[idk][jdk][key]['all'], dtype=float)
                        amin = np.amin(tmp)
                        amax = np.amax(tmp)
                        if what > 0 or what == 0:
                            mean = np.mean(tmp)
                            mmin = mean - amin
                            mmax = amax - mean
                            in_dict[idk][jdk][key]['mean'] = [mean.tolist(), mmin.tolist(), mmax.tolist()]
                        if what < 0 or what == 0:
                            median = np.median(tmp)
                            mmin = median - amin
                            mmax = amax - median
                            in_dict[idk][jdk][key]['median'] = [median.tolist(), mmin.tolist(), mmax.tolist()]
                    except KeyError:
                        logging.warn('Key `{}\' not found, did you miss type something?'.format(key))
                        continue

def normalise_value(ureg, value, v_unit, norm):
    if v_unit.lower() != norm.lower():
        tmp = value * ureg(v_unit)
        return tmp.to(ureg(norm)).magnitude
    else:
        return value

