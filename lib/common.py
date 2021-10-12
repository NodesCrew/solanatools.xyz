# coding: utf-8

def fatal_error(message):
    """ Print error and exit
    """
    print("Fatal error: %s" % message)
    exit(1)


def flatten_json(y):
    """ JSON flattener from https://stackoverflow.com/a/51379007
    """
    out = {}

    def flatten(x, name=''):
        if type(x) is dict:
            for a in x:
                flatten(x[a], name + a + '_')
        elif type(x) is list:
            i = 0
            for a in x:
                flatten(a, name + str(i) + '_')
                i += 1
        else:
            out[name[:-1]] = x
    flatten(y)
    return out


def iter_file(path):
    """ Iterate over file lines
    """
    with open(path) as f:
        for line in f:
            yield line.strip()
