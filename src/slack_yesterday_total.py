#!/bin/python3
from cloudhealth import CloudHealth
from datetime import datetime, timedelta
import numpy as np
import yaml
import os
import requests
import json


config_path = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "config.yaml")))

if __name__ == "__main__":
    
    with open(config_path) as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
        
    now_date = datetime.now() 

    yesterday = now_date - timedelta(days=3)

    c = CloudHealth(ApiKey=config["cloudhealth_api"])
    data = c.new() \
        .with_report('olap_reports/cost/history') \
        .with_time('daily') \
        .get_report()
    c.build_data(data)
    # c.write_excel('report.xlsx')
    # print(c.data_frames)


    bill = "$" + str(np.around(c.data_frames[0][1][yesterday.strftime("%Y-%m-%d")][0] ,decimals=1)) + str(" ") + yesterday.strftime("%Y-%m-%d")
    
    # Set the webhook_url to the one provided by Slack when you create the webhook at https://my.slack.com/services/new/incoming-webhook/
    # webhook_url = 'https://hooks.slack.com/services/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'
    webhook_url = config["slack_hook"]
    slack_data = {'text': bill}

    response = requests.post(
        webhook_url, data=json.dumps(slack_data),
        headers={'Content-Type': 'application/json'}
    )
    if response.status_code != 200:
        raise ValueError(
            'Request to slack returned an error %s, the response is:\n%s'
            % (response.status_code, response.text)
        )
