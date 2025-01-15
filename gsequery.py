import numpy as np
from pybfsw.gse.parameter import parameter_from_string, ParameterBank, Parameter
from os.path import expandvars, expanduser
from msgspec.msgpack import encode, decode
from sqlite3 import connect
import rpyc
import time
import math

# TODO: implement some limiting behavior, to prevent issuing some massive query that hangs the system
# TODO: make sure current where clause handling can handle more than one predicate


def get_db_path():
    env = "$GSE_DB_PATH"
    ret = expanduser(expandvars(env))
    if ret != env:
        return ret
    else:
        return None

def get_project_name():
    env = "$GSE_PROJECT"
    ret = expandvars(env)
    if ret != env:
        return ret.lower()
    else:
        return None

def scale_str(scale):
    if scale == None: return ""
    else: return f", {scale}"

class DBInterface:

    def __init__(self, path=None):
        if path is None:
            path = get_db_path()
        servers = {"local": "127.0.0.1:44555"}
        if path in servers:
            path = servers[path]
        self.path = path
        self.connect()

    def connect(self):
        if len(self.path.split(":")) == 2:
            self.remote = True
            host, port = self.path.split(":")
            self.connection = rpyc.connect(host, int(port))
        else:
            self.remote = False
            full_path = f"file:{self.path}?mode=ro"
            self.connection = connect(full_path, uri=True, timeout=2)
            self.cursor = None

    def ping(self):
        ping = ""
        if self.remote:
            try:
                ping = self.connection.root.ping()
            except Exception as e:
                print('exception in ping: ',e)
                pass
        return ping


    def maintain_connection(self):
        if self.remote:
            if self.ping() == "ping":
                return True
            else:
                self.connect()
                if self.ping() == "ping":
                    return True
                else:
                    return False
        else:
            #check that local sqlite connection is valid somehow
            return True

    def query(self, sql):
        if self.remote:
            data = self.connection.root.query(sql)
            return decode(data)
        else:
            return self.connection.execute(sql).fetchall()

    def query_start(self, sql):
        if self.remote:
            self.connection.root.query_start(sql)
        else:
            self.cursor = self.connection.execute(sql)

    def query_fetch(self,n):
        if self.remote:
            data = self.connection.root.query_fetch(n)
            return decode(data)
        else:
            return self.cursor.fetchmany(n)

class DBInterfaceRemote(rpyc.Service):
    def __init__(self, *args, **kwargs):
        self.db_file_path = kwargs["db_file_path"]
        self.cursor = None

    def on_connect(self, conn):
        path = self.db_file_path
        if path is None:
            path = get_db_path()
        full_path = f"file:{path}?mode=ro"
        from sqlite3 import connect

        self.connection = connect(full_path, uri=True, timeout=2)

    def exposed_query(self, sql):
        results = self.connection.execute(sql).fetchall()
        data = encode(results)
        print("query: ", sql)
        print("transmitting ", len(data), " bytes")
        return data

    def exposed_query_start(self, sql):
        self.cursor = self.connection.execute(sql)

    def exposed_query_fetch(self,n):
        if n > 1000000:
            raise ValueError("fetch size is too large, use n < 1,000,000")
        if self.cursor is None:
            raise RuntimeError("you must call query_start before calling query_fetch")
        return encode(self.cursor.fetchmany(n))

    def exposed_ping(self):
        return "ping"




def rpc_server(host, port, db_file_path=None):

    service = rpyc.utils.helpers.classpartial(
        DBInterfaceRemote, db_file_path=db_file_path
    )
    t = rpyc.utils.server.ThreadedServer(
        service, port=port, hostname=host, protocol_config={"allow_public_attrs": True}
    )
    t.start()


class ParameterGroups:
    def __init__(self, parameters, parameter_bank=None):
        self.groups = {}
        for parameter in parameters:
            if isinstance(parameter, Parameter):
                pass
            else:
                assert isinstance(parameter, str)
                if parameter.startswith("@"):
                    parameter = parameter_bank.get(parameter)
                else:
                    parameter = parameter_from_string(parameter)
            tup = (
                parameter.table,
                parameter.where,
                parameter.scale,
            )  # consider problems with where clauses that are semantically the same but don't compare equal as str
            if tup in self.groups:
                self.groups[tup].append(parameter)
            else:
                self.groups[tup] = [parameter]

class GSEQuery:
    def __init__(self, path=None, project=None):
        if project is None:
            project = get_project_name()
        if project is None:
            project = "none"
            self.parameter_bank = ParameterBank([])
        else:
            if project == "grips2":
                from pybfsw.payloads.grips2.parameters import make_parameter_bank
                self.parameter_bank = make_parameter_bank()
            else:
                raise ValueError(
                    f"unknown project {project}, cannot load parameter bank"
                )

        self.dbi = DBInterface(path=path)
        self.project = project

    def get_project_and_path(self):
        return (self.project, self.dbi.path)


    def get_column_names(self, table):
        sql = f"pragma table_info({table})"
        res = self.dbi.query(sql)
        return [t[1] for t in res]

    def get_latest_rows(self, table, limit=1, lastptr=None):

        """
        get the latest rows from a table

        example usage:
        _,last = gsequery.get_latest_rows('mytable') #first call to get pointer to latest row
        data,last = gsequery.get_latest_rows('mytable',n=4,lastptr=last) #returns latest 4 rows
        time.sleep(10)
        data,last = gsequery.get_latest_rows('mytable',n=4,lastptr=last) #returns latest 4 rows
        """

        if not 'gcutime' in self.get_column_names(table):
            return None, None # no column called gcutime

        if lastptr is not None:
            sql = f"select *,rowid,gcutime from {table} where rowid > {lastptr[0]} and gcutime >= {lastptr[1]} order by rowid desc limit {limit}"
            res = self.dbi.query(sql)
            if res:
                return res, (
                    res[0][-2],
                    res[0][-1],
                )  # typical case, first row is latest row, since sql query is descending order
            else:
                return None, lastptr  # no new data
        else:
            sql = f"select rowid,gcutime from {table} order by rowid desc limit 1"
            res = self.dbi.query(sql)
            if res:
                return None, res  # typical case
            else:
                return None, None  # db is empty

    def get_latest_n_rows(self, table, n):

        sql = f"select *,rowid,gcutime from {table} where rowid > (select max(rowid)-{n} from {table})"
        res = self.dbi.query(sql)
        if res:
            return res
        else:
            return None

    def get_rows1(self, table, t1, t2):

        """
        get rows from table between times t1 and t2
        """

        t1 = float(t1)
        t2 = float(t2)
        sql = f"select * from {table} where gcutime >= {t1} and gcutime <= {t2}"
        res = self.dbi.query(sql)
        if res:
            return res
        else:
            return None

    def get_rows1_exclusive(self, table, t1, t2):

        """
        get rows from table between times t1 and t2
        """

        t1 = float(t1)
        t2 = float(t2)
        sql = f"select * from {table} where gcutime > {t1} and gcutime <= {t2}"
        res = self.dbi.query(sql)
        if res:
            return res
        else:
            return None

    def get_n_rows(self, table, t1, t2):

        """
        get number of rows from table between times t1 and t2
        """

        t1 = float(t1)
        t2 = float(t2)
        try:
            sql = f"select * from {table} where gcutime >= {t1} and gcutime <= {t2}"
            res = self.dbi.query(sql)
            if res:
                return len(res)
            else:
                return 0
        except:
            return -1

    def get_table_names(self):
        sql = "select name from sqlite_master where type='table' and name not like 'sqlite_%';"
        names = self.dbi.query(sql)
        return [n[0] for n in names]

    def get_parameter_bank(self):
        return self.parameter_bank

    def get_latest_time(self, table):
        sql = f"select gcutime from {table} order by gcutime desc limit 1"
        res = self.dbi.query(sql)
        return res[0][0]

    def get_latest_blob(self, table, col):

        sql = f"select {col},rowid,gcutime from {table} order by rowid desc limit 1;"
        res = self.dbi.query(sql)
        if res:
            return res[0]
        else:
            return None


    def get_latest_value(self, name):
        if name[0] == "@":
            par = self.parameter_bank.get(name)
        else:
            par = parameter_from_string(name)
        sql = f"select gcutime,{par.column}{scale_str(par.scale)} from {par.table} where gcutime >= (select max(gcutime) from {par.table}) limit 1"
        data = self.dbi.query(sql)
        if data and par.scale and par.scale_div:
            return data[0][0], par.convert(data[0][1]/data[0][2]), par
        if data and par.scale :
            return data[0][0], par.convert(data[0][1]*data[0][2]), par
        elif data:
            return data[0][0], par.convert(data[0][1]), par
        else:
            return None

    def get_latest_values_for_plot(
        self, parameter_name, time_range_sec=86400, target_entries=1000, downsampling_factor=None
    ):
        """
        Retrieve values for plotting within a specified time range from the latest data.

        To minimize data impact, either `target_entries` or `downsampling_factor` must be provided.
        If both are specified, `downsampling_factor` will be used.

        Args:
            parameter_name (str): Parameter name or identifier.
            time_range_sec (int): Time range (in seconds) before the latest data to retrieve.
            target_entries (int): Approximate number of entries to retrieve.
            downsampling_factor (int, optional): Factor for reducing data rows.

        Returns:
            tuple: (list of timestamps, list of values, parameter) or None if no data.
        """
        # Determine the parameter object based on the name
        parameter = self.parameter_bank.get(parameter_name) if parameter_name.startswith("@") else parameter_from_string(parameter_name)

        # Calculate the starting time for the query based on the specified time range
        query_start_time = self.get_latest_time(parameter.table) - time_range_sec

        # Calculate the downsampling factor if not provided
        if downsampling_factor is None:
            # Query to count the total number of entries in the specified time range
            count_query = f"""
                SELECT COUNT({parameter.column}{scale_str(parameter.scale)})
                FROM {parameter.table}
                WHERE {parameter.where + ' AND ' if parameter.where else ''} gcutime > {query_start_time};
            """
            total_entries = self.dbi.query(count_query)[0][0]
            downsampling_factor = max(1, math.ceil(total_entries / target_entries))

        # SQL query to retrieve the data based on the downsampling factor
        data_query = f"""
            SELECT gcutime, {parameter.column}{scale_str(parameter.scale)}
            FROM {parameter.table}
            WHERE {parameter.where + ' AND ' if parameter.where else ''} gcutime > {query_start_time}
                  AND rowid % {downsampling_factor} = 0
            ORDER BY gcutime DESC;
        """
        data = self.dbi.query(data_query)

        if not data: return None # Return None if no data is retrieved

        # Extract timestamps and values from the data
        timestamps = [row[0] for row in data]

        if parameter.scale and parameter.scale_div:
            values = [parameter.convert(row[1] / row[2]) for row in data]
        elif parameter.scale:
            values = [parameter.convert(row[1] * row[2]) for row in data]
        else:
            values = [parameter.convert(row[1]) for row in data]

        return timestamps, values, parameter



    def make_parameter_groups(self, parameters):
        return ParameterGroups(parameters, parameter_bank=self.parameter_bank)

    def get_latest_value_groups(self, parameter_group: ParameterGroups):
        results = {}
        for query_info, parameters in parameter_group.groups.items():
            table, where, scale = query_info
            columns = [parameter.column for parameter in parameters]
            if where is None:
                sql = f"select gcutime,{','.join(columns)}{scale_str(scale)} from {table} where gcutime >= (select max(gcutime) from {table}) limit 1"
            else:
                sql = f"select gcutime,{','.join(columns)}{scale_str(scale)} from {table} where gcutime >= (select max(gcutime) from {table} where {where}) and {where} limit 1"
            res = self.dbi.query(sql)
            if res:
                res = res[0]
                gcutime = res[0]
                for i, parameter in enumerate(parameters):
                    if scale is None:
                        results[parameter.name] = (
                            gcutime,
                            parameter.convert(res[i + 1]),
                            parameter,
                        )
                    elif parameter.scale_div:
                        results[parameter.name] = (
                            gcutime,
                            parameter.convert(res[i + 1]/res[-1]),
                            parameter,
                        )
                    else:
                        results[parameter.name] = (
                            gcutime,
                            parameter.convert(res[i + 1]*res[-1]),
                            parameter,
                        )
            else:
                for parameter in parameters:
                    results[parameter.name] = None

        return results

    def get_median_value_groups(self, parameter_group: ParameterGroups,n=3):
        results = {}
        for query_info, parameters in parameter_group.groups.items():
            table, where, scale = query_info
            columns = [parameter.column for parameter in parameters]
            if where is None:
                sql = f"select rowid, gcutime,{','.join(columns)}{scale_str(scale)} from {table} order by gcutime desc limit {n}"
            else:
                sql = f"select rowid, gcutime,{','.join(columns)}{scale_str(scale)} from {table} where {where} order by gcutime desc limit {n}"
            data = self.dbi.query(sql)
            col_list = [('rowid',int),("times",float)] + [(parameter.column,type(data[0][i + 2])) for i, parameter in enumerate(parameters)]
            if scale: col_list.append(('scale',type(data[0][-1])))
            if data:
                data = np.array(data,dtype = col_list)
                time = min(data['times'])
                for i, parameter in enumerate(parameters):
                    y = data[parameter.column]
                    if parameter.scale:
                        if parameter.scale_div: y = y/data['scale']
                        else: y = y*data['scale']
                    results[parameter.name] = (time,parameter.convert(type(y[0])(np.median(y))),parameter)
            else:
                for parameter in parameters:
                    results[parameter.name] = None

        return results
