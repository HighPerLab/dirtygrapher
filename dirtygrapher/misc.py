import pint

def create_csv_table(in_dict, names, X):
    if in_dict is not None:
        rows = {}
        csvwriter = csv.DictWriter(sys.stdout, fieldnames=names)
        csvwriter.writeheader()
        for x in X:
            tmp_dict = {'x': x}
            for name in names[1:]:
                if 'bandh2d' in in_dict[name][str(x)].keys():
                    tmp_dict[name] = in_dict[name][str(x)]['bandh2d']['mean'][0]
                elif 'mbandh2d' in in_dict[name][str(x)].keys():
                    tmp_dict[name] = in_dict[name][str(x)]['mbandh2d']['mean'][0]
            csvwriter.writerow(tmp_dict)

