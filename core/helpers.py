"""
Created on Apr 2, 2016

@author: user
"""

import logging
import requests
import simplejson as json
import config

from datetime import timedelta
from decimal import Decimal
from sqlalchemy.orm import class_mapper
from tornado import httpclient, httputil


class FilterHelper(object):
    def __init__(self):
        self.__sqlfilter = ""
        self.__params = {}

    def get_params(self):
        return self.__params

    def get_sql_filter(self):
        return self.__sqlfilter

    @staticmethod
    def alter_filter_property(filter: str, property, value):
        argfilter = json.loads(filter)
        items = [x for x in argfilter if x.get("property") == property]
        if len(items) > 0:
            items[0]["value"] = value
        else:
            item = {}
            item['property'] = property
            item['value'] = value
            argfilter.append(item)
        return json.dumps(argfilter)

    @staticmethod
    def get_filter_value_from_property(filter: str, property):
        argfilter = json.loads(filter)
        retval = ""
        items = [x for x in argfilter if x.get("property") == property]
        if len(items) > 0:
            retval = items[0].get("value")
        return retval

    @staticmethod
    def pop_filter_property(filter: str, property):
        argfilter = json.loads(filter)
        items = [x for x in argfilter if x.get("property") == property]
        if len(items) > 0:
            argfilter.remove(items[0])
        return json.dumps(argfilter)

    def parse(self, filter):
        try:
            if type(filter) == bytes:
                filter = filter.decode("utf-8")
            argfilter = json.loads(filter)
            fl = []
            i = 0
            for fil in argfilter:
                prop = fil.get("property")
                value = fil.get("value")
                operator = fil.get("operator").lower() if fil.get("operator") else "="
                field = fil.get("property")
                if type(value) != list:
                    if prop.find(".") > -1:
                        param = prop.split(".")[1] + str(i)
                    else:
                        param = prop + str(i)
                    s = "( {0} {1} :{2} )"
                    s = s.format(field, operator, param)
                    fl.append(s)
                    if operator in ["like", "ilike"]:
                        value = "%" + value + "%"
                    self.__params[param] = value
                else:
                    if operator == 'between':
                        fl2 = []
                        j = 0
                        for v in value:
                            if prop.find(".") > -1:
                                param = prop.split(".")[1] + str(j)
                            else:
                                param = prop + str(j)
                            s = ":" + param
                            fl2.append(s)
                            self.__params[param] = v
                            j += 1
                        temp_str = field + " between " + fl2[0] + " and " + fl2[1]
                        fl.append("(" + temp_str + ")")
                        fl = fl
                    else:
                        fl2 = []
                        j = 0
                        for v in value:
                            if prop.find(".") > -1:
                                param = prop.split(".")[1] + str(j)
                            else:
                                param = prop + str(j)
                            s = field + " {0} :" + param
                            s = s.format("=") if not operator else s.format(operator)
                            fl2.append(s)
                            if operator in ["like", "ilike"]:
                                value = "%" + v + "%"
                            else:
                                value = v
                            self.__params[param] = value
                            j += 1
                        temp_str = " or ".join(fl2)
                        fl.append("(" + temp_str + ")")
                        fl = fl
                i += 1
            self.__sqlfilter = " and ".join(fl)
        except Exception as e:
            logging.exception(e)

    def parse2(self, filter: str):
        argfilter = json.loads(filter)
        idx = 0
        for i in argfilter:
            if type(i) == dict:
                self.__translate_dict(i, idx)
            else:
                self.__sqlfilter += " " + i + " "
            idx += 1

    def __translate_dict(self, obj, param_idx):

        for k, v in enumerate(obj):
            fl = []
            if v != 'operator':
                fl.append(v)
                fl.append(obj['operator'])
                if obj['operator'] == 'like':
                    fl.append(":" + v + str(param_idx))
                else:
                    fl.append(":" + v + str(param_idx))
                self.__sqlfilter += " ".join(fl)
                self.__params[v + str(param_idx)] = obj[v]


class SortParser(object):
    def __init__(self, sort: str):
        self.sortString = sort

    def get_sort_direction_from_property(self, property_):
        try:
            argsort = json.loads(self.sortString)
            retval = ""
            Items = [x for x in argsort if x.get("property") == property_]
            if len(Items) > 0:
                retval = Items[0].get("direction")
            return retval
        except Exception as e1:
            try:
                arrsplitrow = self.sortString.split(',')
                arrRow = []
                for row in arrsplitrow:
                    arrsplitatt = row.strip().split(' ')
                    if len(arrsplitatt) > 2:
                        rowSort = {"property": arrsplitatt[0], "direction": arrsplitatt[1]}
                        arrRow.append(rowSort)
                self.sortString = json.dumps(arrRow)
                argsort = json.loads(self.sortString)
                retval = ""
                Items = [x for x in argsort if x.get("property") == property_]
                if len(Items) > 0:
                    retval = Items[0].get("direction")
                return retval
            except Exception as e2:
                logging.exception(e2)
            logging.exception(e1)

    def pop_sort_property(self, property_):
        argsort = json.loads(self.sortString)
        Items = [x for x in argsort if x.get("property") == property_]
        if len(Items) > 0:
            argsort.remove(Items[0])
        self.sortString = json.dumps(argsort)

    def add_sort_property(self, property_, direction):
        argsort = json.loads(self.sortString)
        appendee = {"property": property_, "direction": direction}
        argsort.append(appendee)
        self.sortString = json.dumps(argsort)

    def parse(self):
        retString = self.sortString
        d = []
        try:
            sortObj = json.loads(self.sortString)
            for obj in sortObj:
                d.append(obj.get("property") + " " + obj.get("direction"))
            retString = ",".join(d)
        except Exception as e:
            # logging.exception(e)
            pass
        return retString


class OneSignal(object):
    def __init__(self):
        self.app_id_worker = "1160d890-287a-43a4-9236-36e624aabc74"
        self.app_id_customer = "c98a589d-9909-4a0f-9537-4c0405d19042"
        self.auth_customer = "Basic YTk4NjhhMjktMDgxZC00NDYwLWFlZjktZjhiZTAzZTQ2YmRi"
        self.auth_worker = "Basic NjAxOWZkMTgtZmFjNS00YmQ1LTlkZjAtZjZkZmZjNWNlZGNk"
        self.url_customer = "https://mytra.id"
        self.url_worker = "https://guard.mytra.id/guard"

    def notif_for_worker(self, filters, title, content):
        payload = {"app_id": self.app_id_worker,
                   "headings": {"en": title},
                   "url": self.url_worker,
                   "filters": filters,
                   "contents": {"en": content}}
        header = {"Content-Type": "application/json; charset=utf-8", "Authorization": self.auth_worker}
        requests.post("https://onesignal.com/api/v1/notifications", headers=header, data=json.dumps(payload))

    def notif_for_customer(self, filters, title, content, url='/'):
        payload = {"app_id": self.app_id_customer,
                   "headings": {"en": title},
                   "url": self.url_customer + url,
                   "filters": filters,
                   "contents": {"en": content}}
        header = {"Content-Type": "application/json; charset=utf-8", "Authorization": self.auth_customer}
        requests.post("https://onesignal.com/api/v1/notifications", headers=header, data=json.dumps(payload))


def toRoman(n):
    """convert integer to Roman numeral"""
    romanNumeralMap = (
        ('M', 1000), ('CM', 900), ('D', 500), ('CD', 400), ('C', 100), ('XC', 90), ('L', 50), ('XL', 40), ('X', 10),
        ('IX', 9), ('V', 5), ('IV', 4), ('I', 1))
    result = ""
    for numeral, integer in romanNumeralMap:
        while n >= integer:
            result += numeral
            n -= integer
    return result


def model_to_dict(obj, visited_children=None, back_relationships=None):
    if visited_children is None:
        visited_children = set()
    if back_relationships is None:
        back_relationships = set()
    serialized_data = {c.key: getattr(obj, c.key) for c in obj.__tablename__.columns}
    relationships = class_mapper(obj.__class__).relationships
    visitable_relationships = [(name, rel) for name, rel in relationships.items() if name not in back_relationships]
    for name, relation in visitable_relationships:
        if relation.backref:
            back_relationships.add(relation.backref)
        relationship_children = getattr(obj, name)
        if relationship_children is not None:
            if relation.uselist:
                children = []
                for child in [c for c in relationship_children if c not in visited_children]:
                    visited_children.add(child)
                    children.append(model_to_dict(child, visited_children, back_relationships))
                serialized_data[name] = children
            else:
                serialized_data[name] = model_to_dict(relationship_children, visited_children, back_relationships)
    return serialized_data


def to_dict(model_instance, query_instance=None):
    if hasattr(model_instance, '__table__'):
        return {c.name: getattr(model_instance, c.name) for c in model_instance.__table__.columns}
    else:
        cols = query_instance.column_descriptions
        return {cols[i]['name']: model_instance[i] for i in range(len(cols))}


def from_dict(dict, model_instance):
    for c in model_instance.__table__.columns:
        setattr(model_instance, c.name, dict[c.name])


def rows_to_dict(rows_model_instance):
    data = []
    for row in rows_model_instance:
        data.append(to_dict(row))
    return data


def create_number_base36_from_datetime(datetime):
    arrdatetime1 = datetime.replace("-", "").replace(":", "") \
        .split("T")
    arrdatetime2 = arrdatetime1[1].split(".")
    converter = Base36Converter()
    return converter.encode(int(arrdatetime1[0])) + converter.encode(int(arrdatetime2[0])) + \
           converter.encode(int(arrdatetime2[1]))


def moneyfmt(value, places=2, curr='', sep=',', dp='.',
             pos='', neg='-', trailneg=''):
    """Convert Decimal to a money formatted string.

    places:  required number of places after the decimal point
    curr:    optional currency symbol before the sign (may be blank)
    sep:     optional grouping separator (comma, period, space, or blank)
    dp:      decimal point indicator (comma or period)
             only specify as blank when places is zero
    pos:     optional sign for positive numbers: '+', space or blank
    neg:     optional sign for negative numbers: '-', '(', space or blank
    trailneg:optional trailing minus indicator:  '-', ')', space or blank

    >>> d = Decimal('-1234567.8901')
    >>> moneyfmt(d, curr='$')
    '-$1,234,567.89'
    >>> moneyfmt(d, places=0, sep='.', dp='', neg='', trailneg='-')
    '1.234.568-'
    >>> moneyfmt(d, curr='$', neg='(', trailneg=')')
    '($1,234,567.89)'
    >>> moneyfmt(Decimal(123456789), sep=' ')
    '123 456 789.00'
    >>> moneyfmt(Decimal('-0.02'), neg='<', trailneg='>')
    '<0.02>'

    """
    q = Decimal(10) ** -places  # 2 places --> '0.01'
    sign, digits, exp = value.quantize(q).as_tuple()
    result = []
    digits = list(map(str, digits))
    build, next = result.append, digits.pop
    if sign:
        build(trailneg)
    for i in range(places):
        build(next() if digits else '0')
    if places:
        build(dp)
    if not digits:
        build('0')
    i = 0
    while digits:
        build(next())
        i += 1
        if i == 3 and digits:
            i = 0
            build(sep)
    build(curr)
    build(neg if sign else pos)
    return ''.join(reversed(result))


def create_number_from_datetime(datetime):
    arrdatetime1 = datetime.replace("-", "").replace(":", "") \
        .split("T")
    arrdatetime2 = arrdatetime1[1].split(".")
    converter = BaseNumberConverter()
    return converter.encode(int(arrdatetime1[0])) + converter.encode(int(arrdatetime2[0])) + \
           converter.encode(int(arrdatetime2[1]))


class BaseNumberConverter(object):
    def __init__(self):
        self.BASENUMBER = "0123456789"

    def encode(self, num):
        """Encode a positive number in Base X

        Arguments:
        - `num`: The number to encode
        - `alphabet`: The alphabet to use for encoding
        """
        if num == 0:
            return self.BASENUMBER[0]
        arr = []
        base = len(self.BASENUMBER)
        while num:
            num, rem = divmod(num, base)
            arr.append(self.BASENUMBER[rem])
        arr.reverse()
        return ''.join(arr)

    def decode(self, string):
        """Decode a Base X encoded string into the number

        Arguments:
        - `string`: The encoded string
        - `alphabet`: The alphabet to use for encoding
        """
        base = len(self.BASENUMBER)
        strlen = len(string)
        num = 0

        idx = 0
        for char in string:
            power = (strlen - (idx + 1))
            num += self.BASENUMBER.index(char) * (base ** power)
            idx += 1

        return num


class Base62Converter(object):
    def __init__(self):
        self.BASE62 = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

    def encode(self, num):
        """Encode a positive number in Base X

        Arguments:
        - `num`: The number to encode
        - `alphabet`: The alphabet to use for encoding
        """
        if num == 0:
            return self.BASE62[0]
        arr = []
        base = len(self.BASE62)
        while num:
            num, rem = divmod(num, base)
            arr.append(self.BASE62[rem])
        arr.reverse()
        return ''.join(arr)

    def decode(self, string):
        """Decode a Base X encoded string into the number

        Arguments:
        - `string`: The encoded string
        - `alphabet`: The alphabet to use for encoding
        """
        base = len(self.BASE62)
        strlen = len(string)
        num = 0

        idx = 0
        for char in string:
            power = (strlen - (idx + 1))
            num += self.BASE62.index(char) * (base ** power)
            idx += 1

        return num


class Base36Converter(object):
    def __init__(self):
        self.BASE36 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    def encode(self, num):
        """Encode a positive number in Base X

        Arguments:
        - `num`: The number to encode
        - `alphabet`: The alphabet to use for encoding
        """
        if num == 0:
            return self.BASE36[0]
        arr = []
        base = len(self.BASE36)
        while num:
            num, rem = divmod(num, base)
            arr.append(self.BASE36[rem])
        arr.reverse()
        return ''.join(arr)

    def decode(self, string):
        """Decode a Base X encoded string into the number

        Arguments:
        - `string`: The encoded string
        - `alphabet`: The alphabet to use for encoding
        """
        base = len(self.BASE36)
        strlen = len(string)
        num = 0

        idx = 0
        for char in string:
            power = (strlen - (idx + 1))
            num += self.BASE36.index(char) * (base ** power)
            idx += 1

        return num


def select_cols(*args):
    retval = []
    for obj in args:
        if hasattr(obj, '__table__'):
            for col in obj.__table__.columns:
                retval.append(getattr(obj, col.name))
        else:
            retval.append(obj)
    return retval


def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)


def _get_user_data(token, username):
    http_client = httpclient.HTTPClient()
    # http_client = AsyncHTTPClient()
    try:
        authHeader = token
        headers = {"Accept": "*/*", "Content-Type": "application/json; charset=UTF-8", "Authorization": authHeader}
        params = {'page': 1, 'limit': 100}
        filters = [
            {
                'property': "sys_users.username",
                'value': username,
                'operator': "="
            }
        ]
        params['filter'] = json.dumps(filters)
        params['sort'] = "[]"
        strParams = ""
        if params:
            strParams = "?" + httputil.urlencode(params).encode().decode("utf-8")
        url = config.ADMIN_API_URL + config.BASE_API + "{0}".format("datauser") + strParams
        print(url)
        response = http_client.fetch(url, method="GET", headers=headers)
        data = json.loads(response.body.decode("UTF-8"))
        return data.get("rows")
    except httpclient.HTTPError as e:
        logging.exception(e)
    except Exception as e:
        logging.exception(e)
    http_client.close()


def _get_user_worker(token):
    http_client = httpclient.HTTPClient()
    try:
        authHeader = token
        headers = {"Accept": "*/*", "Content-Type": "application/json; charset=UTF-8", "Authorization": authHeader}
        params = {'page': 1, 'limit': 10}

        filters = [
            {
                'property': "user_workers.status",
                'value': 'ACT',
                'operator': "="
            }
        ]
        params['filter'] = json.dumps(filters)
        params['sort'] = "[]"

        strParams = ""
        if params:
            strParams = "?" + httputil.urlencode(params).encode().decode("utf-8")
        url = config.ADMIN_API_URL + config.BASE_API + "/{0}".format("worker") + strParams
        response = http_client.fetch(url, method="GET", headers=headers)
        data = json.loads(response.body.decode("UTF-8"))
        return data.get("rows")
    except httpclient.HTTPError as e:
        logging.exception(e)
    except Exception as e:
        logging.exception(e)
    http_client.close()


if __name__ == '__main__':
    # f = FilterHelper()
    # f.parse_ext_filter(' [ { "property" : "name", "value" : "arief" } ] ')
    # print(f.get_params(), f.get_sql_filter())
    # '''
    # session.query(User).filter(
    #                      text(f.get_sql_filter())).\
    #                      params(f.get_params()).all()'''
    # import datetime
    # import random
    # min = 10
    # max = 90
    #
    # a = str(random.randint(min, max))
    # b = '%02d' % datetime.datetime.now().day
    # c = str(int(create_number_from_datetime(datetime.datetime.now().isoformat())) % 100000)
    # bok_num = a + b + c
    # print('INV/' + datetime.datetime.now().strftime("%Y%m%d") + '/'
    #       + toRoman(int(datetime.datetime.now().strftime("%y")))
    #       + '/' + toRoman(int(datetime.datetime.now().strftime("%m"))) + '/' + bok_num)

    a = "-6.183810199999999,106.84530189999998"
    b = "-6.3008047,106.7866051"
    pool = "-6.3008094,106.8544573"

    a_lat, a_long = a.split(',')
    b_lat, b_long = b.split(',')
    pool_lat, pool_long = pool.split(',')

    distance = (abs(float(a_lat) - float(pool_lat)) ** 2 + abs(float(a_long) - float(pool_long)) ** 2) ** 0.5
    b_distance = (abs(float(b_lat) - float(pool_lat)) ** 2 + abs(float(b_long) - float(pool_long)) ** 2) ** 0.5
    print(distance)
    print(b_distance)

    # from core.scaffolding.mst.services.MstPgscheduleService import MstPgscheduleService
    # # from common.helpers import FilterHelper, to_dict, rows_to_dict, SortParser
    # from sqlalchemy.sql.expression import text
    # import simplejson as json
    # import logging
    # import uuid
    # import datetime
    # from tornado.concurrent import run_on_executor