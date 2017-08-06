class Point(object):
    def __init__(self, x = None, y = None, tupl_str = None):
        if tupl_str is not None:
            self.x = eval(tupl_str)[0]
            self.y = eval(tupl_str)[1]
        if x is not None:
            self.x = x  
        if y is not None:
            self.y = y

    def __repr__(self):
        return "({0}, {1})".format(self.x, self.y)

    def __str__(self):
        return "({0}, {1})".format(self.x, self.y)

    def __hash__(self):
        return hash((self.x, self.y))

    def __eq__(self, other):
        return (self.x, self.y) == (other.x, other.y)
