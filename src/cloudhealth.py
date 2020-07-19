import requests
from urllib.parse import urlencode
import json
import pandas as pd
import pprint
import simplejson
from pandas import ExcelWriter
import yaml


class CloudHealth:
    def __init__(self, **kwargs):
        self.pp = pprint.PrettyPrinter(indent=4)
        self.api_key = kwargs.get('ApiKey')
        self.new()
        self.data_frames = []
        self.headers = {'Authorization': 'Bearer ' + self.api_key,
                        'Accept': 'application/json'}
        self.config_files = kwargs.get('ReportConfigFiles')
        if self.config_files:
            self.load_config()

    def load_config(self):
        self.report_config = {}
        for r in self.config_config.split(','):
            with open(r, 'r') as s:
                c = yaml.safe_load(s)
                #self.report_config = {**self.report_config, **c}

    def with_query(self, query):
        self.query = query
        return self

    def with_name(self, name):
        self.name = name
        return self

    def with_dimension(self, dimension):
        self.dimensions.append(dimension)
        return self

    def with_select_filter(self, filter):
        self.filters.append("{}:select:{}".format(filter[0],
                                                  ','.join(filter[1])))
        return self

    def with_reject_filter(self, filter):
        self.filters.append("{}:reject:{}".format(filter[0],
                                                  ','.join(filter[1])))
        return self

    def with_measures(self, measures):
        self.measures = measures
        return self

    def with_time(self, interval, select=None):
        self.interval = interval
        if select:
            self.filters.append("time:select:{}".format(select))
        return self

    def with_report(self, report):
        self.report = report
        return self

    def build_url(self):
        q = {}
        base_url = 'https://chapi.cloudhealthtech.com/{}/?'.format(self.report)
        q['dimensions[]'] = self.dimensions
        q['filters[]'] = self.filters
        q['measures[]'] = self.measures
        q['interval'] = self.interval
        q['name'] = self.name
        q['query'] = self.query
        url = base_url + urlencode(q, doseq=True)
        return url

    def get_report(self):
        # print('Getting report . . .')
        url = self.build_url()
        response = requests.get(url, headers=self.headers)
        j = json.loads(response.text)
        # self.pp.pprint(j)
        reportData = open("report.json", "w")
        reportData.write(simplejson.dumps(j, indent=4, sort_keys=True))
        reportData.close()
        # print('Done.')
        return j

    def build_data(self, j):
        # print('Generating data . . .')
        data_j = j['data']
        dims = j['dimensions']
        x_axis = list(dims[0].keys())[0]
        category = list(dims[1].keys())[0]
        cols = [d['name'] for d in dims[0][x_axis]]
        categories = [d['name'] for d in dims[1][category]]
        c = 0
        for m in j['measures']:
            measure_label = m['label']
            data = {}
            data['Categories'] = categories
            i = 0
            for col in cols:
                row = data_j[i]
                i = i + 1
                if all(d[c] is None for d in row):
                    continue
                data[col] = [d[c] for d in row]
            c = c + 1
            df = pd.DataFrame(data)
            df = df.dropna(thresh=len(data.keys())-1)
            frame_name = '{}-{}'.format(measure_label[:14], category[:14])
            self.data_frames.append((frame_name, df))
        # print('Done.')

    def write_excel(self, path):
        print('Writing data to {} . . .'.format(path))
        writer = ExcelWriter(path)
        for df in self.data_frames:
            df[1].to_excel(writer, df[0], index=False)
        writer.save()
        print('Done')

    def new(self):
        # print('Clearing out existing report parameters . . .')
        self.dimension = []
        self.filters = []
        self.dimensions = []
        self.interval = ""
        self.interval_count = ""
        self.measures = []
        self.name = ""
        self.query = ""
        return self

    def get_report_definition(self, report):
        url = 'https://chapi.cloudhealthtech.com/{}/new'.format(report)
        response = requests.get(url, headers=self.headers)
        j = json.loads(response.text)
        print('DIMENSIONS')
        for d in j['dimensions']:
            print('   {} ("{}")'.format(d['name'], d['label']))

        print('MEASURES')
        for d in j['measures']:
            print('   {} ("{}")'.format(d['name'], d['label']))

        print('INTERVALS')
        for d in j['intervals']:
            print('   {}'.format(d))

