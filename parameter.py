chars = "01234567890~%^&|*()<>-+/.eybx "


def nothing(y):
    return y


class Parameter:
    def __init__(
        self, name, table, column, where=None, converter=None, low_range=None, high_range=None,low_alarm=None,high_alarm=None,units="raw", comment="",scale=None,scale_div = False
    ):
        """
        The parameter class wraps all necessary information for retrieving and displaying
        information about an instrument parameter. An example of a parameter would be the
        flight computer CPU temperature.

        name (string): the parameter name
        table (string): the name of the database table containing the column for this parameter
        column (string): the name of the column in the database
        where (string, optional): a where clause allowing for filtered queries
        converter (func or string): a function or eval string that converts the raw value from the DB into something with units
        units (string): the units of the converted values
        comment (str): a comment string for including information about this parameter
        scale (p) : a scale factor included in the same gsedb table

        eval strings use the \"y\" variable as a placeholder
        example eval strings: y*1e3 + 5 (mult by 1e3 and add 5), y & 0b0101 (bitwise AND between y and 5)
        """
        if converter is None:
            self.converter = nothing
        else:
            self.converter = converter
        self.name = name
        self.table = table
        self.column = column
        self.where = where
        self.units = units
        self.comment = comment
        self.low_range = low_range
        self.high_range = high_range
        self.low_alarm = low_alarm
        self.high_alarm = high_alarm
        self.scale = scale
        self.scale_div = scale_div

    def convert(self, y):
        if isinstance(self.converter, str):
            for c in self.converter:
                if c not in chars:
                    raise ValueError(f"bad eval string, valid chars are {chars}")
            return eval(self.converter)

        else:
            return self.converter(y)


def parameter_from_string(s, name=None):

    """
    factory function for creating Parameter instances from colon separated strings
    examples:
    p = parameter_from_string("pdu:volt0:pduid=1",name="@pdu1_volt0")
    p = parameter_from_string("pdu:amp1:pduid=0:10*x:amps",name="@pdu0_current1_10x")
    """

    sp = s.split(":")
    if name is None:
        name = s
    if len(sp) == 2:
        return Parameter(name, sp[0], sp[1])
    elif len(sp) == 3:
        return Parameter(name, sp[0], sp[1], where=sp[2])
    elif len(sp) == 4:
        return Parameter(name, sp[0], sp[1], where=sp[2], converter=sp[3])
    elif len(sp) == 5:
        return Parameter(name, sp[0], sp[1], where=sp[2], converter=sp[3], units=sp[4])
    else:
        raise ValueError("bad format for parameter string")


class ParameterBank:

    """
    A ParameterBank instance is a container for Parameter instances
    Right now it is just a fancy wrapper around a dict, but there might be
    some additional bookeeping added later

    A Parameter that is added to the ParameterBank must have a name that starts with @
    """

    def __init__(self, par: list = []):
        self.map = {}
        for p in par:
            self.add(p)

    def add(self, p, force = False):
        assert isinstance(p, Parameter)
        if p.name[0] != "@":
            raise ValueError(
                "first character of parameter needs to be @ for insertion into ParameterBank"
            )
        if p.name in self.map and force == False:
            raise KeyError(
                f"parameter with name {p.name} is already in the parameter bank!"
            )
        self.map[p.name] = p

    def get(self, name):
        if name in self.map:
            return self.map[name]
        else:
            raise KeyError(f"parameter with name={name} not found in parameter bank")


    def parameters_by_table(self):

        by_table = {}

        for name in self.map:
            p = self.map[name]
            tab_id = p.table
            if not tab_id in by_table:
                by_table[tab_id] = {}
            col_id = p.column
            if not col_id in by_table[tab_id]:
                by_table[tab_id][col_id] = [p]
            else: 
                by_table[tab_id][col_id].append(p)
        return by_table

    def print_tables_columns(self,f=None):

        by_table = self.parameters_by_table()

        ltab = 0
        lcol = 0

        for tab_id in by_table: 
            ltab = max(ltab,len(tab_id))
            for col_id in by_table[tab_id]: lcol = max(lcol,len(col_id))

        if f: f = open(f, "w")

        for tab_id in by_table: 
            for col_id in by_table[tab_id]:
                print (f"{tab_id}".ljust(ltab + 1) + f": {col_id}".ljust(lcol + 3) + " ".join([p.name for p in by_table[tab_id][col_id]]) , file=f)
        print ("",file=f)
        if f: f.close()

    def print_parameters(self,f=None):

        if f: f = open(f, "w")

        by_table = self.parameters_by_table()
        for tab_id in by_table: 
            for col_id in by_table[tab_id]:
                for p in by_table[tab_id][col_id]:
                    cstr = str(p.converter)
                    print(f"{p.name},{p.table},{p.column},{p.where},{p.units},{p.comment}",file=f)

        if f: f.close()
