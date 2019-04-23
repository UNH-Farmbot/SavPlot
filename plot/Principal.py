import numpy
from Farmware import *

class Netatmo(Farmware):
    def __init__(self):
        Farmware.__init__(self,((__file__.split(os.sep))[len(__file__.split(os.sep)) - 3]).replace('-master', ''))

    # ------------------------------------------------------------------------------------------------------------------
    def load_config(self):

        super(Netatmo, self).load_config()

        self.private_mode = False

        self.get_arg('ne', "eugene.tcipnjatov@gmail.com" , tuple) #(37.80,-122.38)
        self.get_arg('sw', "Safety_123", tuple) #""(37.70,-122.52)"

        if not isinstance(self.args['ne'][0], float) or not isinstance(self.args['ne'][1], float):
            self.args['ne'] = ''.join(self.args['ne'])
            self.private_mode = True
        if not isinstance(self.args['sw'][0], float) or not isinstance(self.args['sw'][1], float):
            self.args['sw'] = ''.join(self.args['sw'])
            self.private_mode = True

    # ------------------------------------------------------------------------------------------------------------------
    def get_access_token(self, login='', password=''):

        client_id = '5afc26dd13475dee138c5873'
        client_secret = 'J6mWnRcq4BRh3CnFOvAI900EEjRJD6LdDpOzMnLWicVqS'

        if login != '':
            payload = {'grant_type': 'password',
                       'username': login,
                       'password': password,
                       'client_id': client_id,
                       'client_secret': client_secret}
        else:
            payload = {'grant_type': 'refresh_token',
                       'refresh_token': 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJ1bmtub3duIiwic3ViIjoyMDUyLCJpYXQiOjE1NTYwMjU2NjgsImp0aSI6ImE3NTA5MDQ5LTJkNDktNGM4OS1hOGUzLWVlZmQ5NThhYTA5YyIsImlzcyI6Ii8vbXkuZmFybWJvdC5pbzo0NDMiLCJleHAiOjE1NTk0ODEzMzcsIm1xdHQiOiJjbGV2ZXItb2N0b3B1cy5ybXEuY2xvdWRhbXFwLmNvbSIsImJvdCI6ImRldmljZV8yMDQ5Iiwidmhvc3QiOiJ4aWNvbmZ1bSIsIm1xdHRfd3MiOiJ3c3M6Ly9jbGV2ZXItb2N0b3B1cy5ybXEuY2xvdWRhbXFwLmNvbTo0NDMvd3MvbXF0dCIsIm9zX3VwZGF0ZV9zZXJ2ZXIiOiJodHRwczovL2FwaS5naXRodWIuY29tL3JlcG9zL2Zhcm1ib3QvZmFybWJvdF9vcy9yZWxlYXNlcy9sYXRlc3QiLCJiZXRhX29zX3VwZGF0ZV9zZXJ2ZXIiOiJodHRwczovL2FwaS5naXRodWIuY29tL3JlcG9zL0Zhcm1Cb3QvZmFybWJvdF9vcy9yZWxlYXNlcy8xNDU4MTg3MSJ9.IrTzqJS57q17_rOGJBlrvjf6s9ULOWhsnOKkxGK1Uy5NV96r-DW1tyko1HJwKInIm_bLsFSAd7q4ujprIdlyvogS-jBGa9lgrZLAp669z0al5AYIZF13kZg3yFHth_-1xECxSyLQQDyH19C8_wC97Af0OZYzKKoDjLZGauaX7ztDDUbaiT4it29OhPO8smHJ17tq-n7akjlNJ_GgRmucoajP6Rv7KBhEPM1PpOAH5BCmF1SRa9NEskqvy_AU8WCrJ3pf3GqPiwv95Mneq-pzx52foNO0Urm5sAqN6glHgvkEFI0pWYyBN79MAAJdn2B-zrqf6oIkF0R18eX_hFgrzQ',
                       'client_id': client_id,
                       'client_secret': client_secret}

        response = requests.post("https://api.netatmo.com/oauth2/token", data=payload)
        response.raise_for_status()
        #print("Your access token is: {}".format(response.json()["access_token"]))
        #print("Your refresh token is: {}".format(response.json()["refresh_token"]))
        #print("Expires in: {}m".format(response.json()["expires_in"] / 60))

        return response.json()["access_token"]


    # ----------------------------------------------------------------------------------------------------------------------
    def run(self):

        self.weather.load()
        td = d2s(today_local())
        #using private weather station
        if self.private_mode:
            self.log('Private mode, contacting your weather station...')
            params={'access_token': self.get_access_token(self.args["ne"], self.args["sw"])}

            response = requests.post("https://api.netatmo.com/api/getstationsdata", params=params)
            response.raise_for_status()
            data = response.json()["body"]

            if len(data['devices']) == 0:
                raise ValueError("You don't seem to have a weather station?")

            outside = data['devices'][0]['modules'][0]['dashboard_data']['Temperature']
            rain = data['devices'][0]['modules'][1]['dashboard_data']['Rain']

            if td not in self.weather():
                self.weather()[td]={}
                self.weather()[td]['min_temperature'] = outside
                self.weather()[td]['max_temperature']= outside
            else:
                self.weather()[td]['max_temperature'] = max(outside,self.weather()[td]['max_temperature'])
                self.weather()[td]['min_temperature'] = min(outside,self.weather()[td]['min_temperature'])

            self.weather()[td]['rain24']=rain

        # using public data
        else:
            self.log('Community mode: {} - {}'.format(self.args["ne"], self.args["sw"]))
            params = {
                'access_token': self.get_access_token(),
                'lat_ne': self.args["ne"][0],
                'lat_sw': self.args["sw"][0],
                'lon_ne': self.args["ne"][1],
                'lon_sw': self.args["sw"][1],
                'filter': 'true',
            }

            response = requests.post("https://api.netatmo.com/api/getpublicdata", params=params)
            response.raise_for_status()
            data = response.json()["body"]

            if len(data)==0:
                raise ValueError('No weataher stations found around you, try to enlarge the box')

            self.log("Averaging on {} stations...".format(len(data)))
            temperature=[]
            rain24=[]

            for x in data:
                m=x['measures']
                for n in m:
                    if 'res' in m[n]:
                        for t in m[n]['res']:
                            for i in range(0,len(m[n]['type'])):
                                if m[n]['type'][i]=='temperature':
                                    temperature.append(float(m[n]['res'][t][i]))
                    if 'rain_24h' in m[n]:
                        rain24.append(float(m[n]['rain_24h']))

            if len(temperature)==0 or len(rain24)==0:
                raise ValueError('Did not get data about rain or temperature from stations in this area, try to enlarge the box')
            mean_t=float('{:.2f}'.format(numpy.mean(temperature)))
            mean_r=float('{:.2f}'.format(numpy.mean(rain24)))

            if td not in self.weather():
                self.weather()[td]['min_temperature'] = mean_t
                self.weather()[td]['max_temperature']=mean_t
            else:
                self.weather()[td]['max_temperature'] = max(mean_t,self.weather()[td]['max_temperature'])
                self.weather()[td]['min_temperature'] = min(mean_t,self.weather()[td]['min_temperature'])
            self.weather()[td]['rain24'] = mean_r

        self.log('Weather:\n{}'.format(self.weather))
        self.weather.save()

# ----------------------------------------------------------------------------------------------------------------------
if __name__ == "__main__":

    app = Netatmo()
    try:
        app.load_config()
        app.run()
        sys.exit(0)

    except requests.exceptions.HTTPError as error:
        if error.response.text[0:100]==u'{"error":"invalid_grant"}':
            app.log('Invalid credentials {} {}'.format(app.nes,app.sws), 'error')
        else:
            app.log('HTTP error {} {} '.format(error.response.status_code,error.response.text[0:100]), 'error')
    except Exception as e:
        app.log('Something went wrong: {}'.format(str(e)), 'error')
    sys.exit(1)
