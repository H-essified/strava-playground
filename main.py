from stravalib.client import Client
import urllib3
import requests
from datetime import datetime
from datetime import timezone
from datetime import timedelta
import json
import pandas as pd
import os
import pytz

client = Client()


# Generate authorisation URL if not already authorised
# authorize_url = client.authorization_url(
#     client_id=xxxx, redirect_uri="http://localhost:8282/authorize", scope=['read', 'read_all','profile:read_all','profile:write','activity:read','activity:read_all','activity:write']
# )
# print(authorize_url)
# exit()

# code = 'xxxx'

# # Setup tokens for client
# token_response = client.exchange_code_for_token(
#     client_id=128202, client_secret="xxxx", code=code
# )
# client.access_token = token_response["access_token"]
# client.refresh_token = token_response["refresh_token"]
# client.token_expires_at = token_response["expires_at"]

# print(client.refresh_token)
# exit() 

# # Pull out athlete information
# athlete = client.get_athlete()
# print(athlete)
# print('mark')

class User:
    def __init__(self, data_source='api', json_path=False):
        self.data_source = data_source.lower()
        self.json_path = json_path

        return


    def import_data(self, time_limit=False, page_limit=5):
        self.time_limit = time_limit
        self.page_limit = page_limit
        if self.time_limit:
            self.max_time = datetime.now(timezone.utc) - timedelta(days=self.time_limit)

        if self.data_source.lower() == 'api':
            self.datajson = self.get_api_data()
        elif self.data_source.lower() == 'json':
            if not os.path.exists(self.json_path):
                raise FileNotFoundError("Unable to find json file")
            with open(self.json_path, 'r') as f:
                self.datajson = json.loads(f.read())
        else:
            raise ValueError("Invlaid data source specified")
        self.normalise_data()

        return
        
          
    def get_api_data(self):
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        self.auth_url = "https://www.strava.com/oauth/token"
        self.activities_url = "https://www.strava.com/api/v3/athlete/activities"
        payload = {
            'client_id': "xxxx",
            'client_secret': 'xxxx',
            'refresh_token': 'xxxx',
            'grant_type': "refresh_token",
            'f': 'json',
            'scope': 'activity:read_all'
        }

        print("Requesting Token...\n")
        res = requests.post(self.auth_url, data=payload, verify=False)
        print(res.json())
        access_token = res.json()['access_token']
        print("Access Token = {}\n".format(access_token))

        self.api_header = {'Authorization': 'Bearer ' + access_token}
        my_dataset = self.loop_through_pages(1)
        return {"results": my_dataset}
    
    def loop_through_pages(self, page):
            
            # start at page ...
            page = page
            # set new_results to True initially
            new_results = True
            # create an empty array to store our combined pages of data in
            data = []
            while new_results:
                # Give some feedback
                print(f'You are requesting page {page} of your activities data ...')
                # request a page + 200 results
                get_strava = requests.get(self.activities_url, headers=self.api_header, params={'per_page': 200, 'page': f'{page}'})
                get_strava.raise_for_status()
                # save the response to new_results to check if its empty or not and close the loop
                new_results = json.loads(get_strava.text)
                # add our responses to the data array
                data.extend(new_results)

                if self.time_limit is not False:
                    timezone_offset = int(data[-1]["utc_offset"]) 
                    max_start_date = datetime.strptime(data[-1]["start_date"], "%Y-%m-%dT%H:%M:%SZ")
                    max_start_date = max_start_date + timedelta(seconds=timezone_offset)
                    max_start_date = pytz.utc.localize(max_start_date)
                    if max_start_date < self.max_time:
                        return data
                # increment the page
                page += 1
                if page > self.page_limit:
                    return data
            # return the combine results of our get requests
            return data

    def normalise_data(self):
        '''
        Converts data json to dataframe
        '''
        self.datapd = pd.json_normalize(self.datajson["results"])
        self.datapd["start_date"] = pd.to_datetime(self.datapd["start_date"])
        self.datapd["start_date_utc"] = self.datapd.apply(lambda row: self.apply_utc(row), axis=1)
        self.datapd = self.datapd[self.datapd["start_date"] > self.max_time]
        return
    
    def apply_utc(self, row):
        utc_normalised = row["start_date"] + timedelta(seconds=int(row["utc_offset"]))

        return utc_normalised


    def generate_statistics(self):
        self.statistics = pd.DataFrame.from_dict({
            "total_distance(metres)": int(self.datapd["distance"].sum()),
            "total_moving_time": timedelta(seconds=int(self.datapd["moving_time"].sum())),
            "total_elapsed_time": timedelta(seconds=int(self.datapd["elapsed_time"].sum())),
            "total_activities ": len(self.datapd),
            "total_elevation_gain(metres)": int(self.datapd["total_elevation_gain"].sum()),
            "unique_sports": self.datapd["sport_type"].unique().tolist(),
            "total_kudos": self.datapd["kudos_count"].sum()
        }, orient="index", columns=["value"])


user = User('json', 'json.json')
# user = User("api")
user.import_data(time_limit=14)
# with open('json.json', 'w') as f:
#     f.write(json.dumps(user.datajson, indent=2))
user.generate_statistics()
print(user.statistics)