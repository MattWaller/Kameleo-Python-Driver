import subprocess
import requests
import json
import random
from random import randint
from bs4 import BeautifulSoup
import psutil    


class Kameleo_cli(object):
    def __init__(self, email, password):
        self.host = 'http://localhost:5050'
        self.email = email
        self.password = password
        self.exe_name = "Kameleo.CLI.exe"
        # starts up the CLI interface for Kameleo.
        # logic test to check if Kameleo.CLI.exe is already running
        open_test = True
        for proc in psutil.process_iter():
            # check whether the process to kill name matches
            if proc.name() == self.exe_name:
                open_test = False
                print("Kameleo.exe already running.")
        if open_test == True:
            # initiate the subprocess to start Kameleo CLI   
            print("Kameleo.exe starting up.")     
            subprocess.Popen(['assets/Kameleo/Kameleo.CLI.exe', f'email={email}', f'password={password}'])
    def closeCLI(self):
        for proc in psutil.process_iter():
            # check whether the process to kill name matches
            if proc.name() == self.exe_name:
                proc.kill()
                print("Kameleo shutdown.")
    # grabs the base profiles from API --> json dict does not work.
    def base_profiles(self):
        r = requests.get(f"{self.host}/base-profiles")#,json={'deviceType': 'desktop','browserProduct': 'chrome'})
        base_profiles = json.loads(r.text)
        return base_profiles
    def init_profile(self,proxyIP='192.168.0.0.0',proxyPort=4000,proxyType='none',deviceType="desktop",language="en-us"):
        base_profiles = self.base_profiles()
        proxyPort = str(proxyPort)
        assert type(proxyIP) == type(str()), f"Error you have entered a non valid IP address {proxyIP} - the IP address should be passed as a string."
        # get profile_ip dictionary for setting up spoofing.
        if proxyIP != '192.168.0.0.0':
            proxies = {
            "https":f"https://{proxyIP}:{proxyPort}",
            "http":f"http://{proxyIP}:{proxyPort}",
            "ftp":f"ftp://{proxyIP}:{proxyPort}"
            }
            ip_dict = self.get_ip_info(proxy=True,proxyDict=proxies)
        else:
            ip_dict = self.get_ip_info()
        # define simple screen size spoofing --> module is very lightweight & will need to be revised.
        screen_size = self.screenSize()  
        # inits new profile based on the proxy or not.
        new_profile_create = self.new_profile(ip_dict,screen_size,base_profiles,proxyIP=proxyIP,proxyPort=proxyPort,proxyType=proxyType,deviceType=deviceType,language=language)
        # make request to server to initiate the new profile
        r = requests.post(f"{self.host}/profiles/new",json=new_profile_create)
        # get guid from request
        guid = json.loads(r.text)['id']
        # start up new profile
        r = requests.get(f"{self.host}/profiles/{guid}/start")
        if r.status_code == 200:
            print('successfully started driver..')
            driver = self.driverConnection(guid)
            print('successfully connected to driver..')
            return driver
        print('failed to compile script')
        raise 'error'
    # get ip information for setting up the json file for spoofing profile.
    def get_ip_info(self,proxy=False,proxyDict={}):
        if proxy == False:
            r = requests.get('https://www.iplocate.com/en/')
            if r.status_code == 200:
                soup = BeautifulSoup(r.text)
                my_table = soup.select('table')
                soup = BeautifulSoup(str(my_table))
                tds = soup.select('td')
                i = 0 
                ip_dict = {}
                while i < len(tds):
                    ip_dict[tds[i].text.strip()] = tds[i+1].text.strip()
                    i += 2
        else:
            r = requests.get('https://www.iplocate.com/en/',proxies=proxiesDict)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text)
                my_table = soup.select('table')
                soup = BeautifulSoup(str(my_table))
                tds = soup.select('td')
                i = 0 
                ip_dict = {}
                while i < len(tds):
                    ip_dict[tds[i].text.strip()] = tds[i+1].text.strip()
                    i += 2
        return ip_dict    
    # define simple logic of 4 random screen sizes.
    def screenSize(self):
        screensizes= ["1920x1080","1366x768","1440x900","1536x864"]
        return screensizes[random.randint(0,len(screensizes)-1)]
    # dictionary & logic for creating a new profile.
    def new_profile(self,ip_dict,screen_size,base_profiles,proxyIP='192.168.0.0.0',proxyPort=4000,proxyType='none',deviceType='desktop',language='en-us'):
        # creates a desktop instance of kameleo browser from base profiles
        if deviceType == 'desktop' or deviceType=='mobile':
            profile_array = []
            for base_profile in base_profiles:
                if base_profile['device']['type'] == 'desktop' and base_profile['language'] == language:
                    profile_array.append(base_profile['id'])
        else:
            profile_array = []
            for base_profile in base_profiles:
                profile_array.append(base_profile['id'])
        guid = profile_array[randint(0,len(profile_array)-1)]
        print(guid)
        profile_dict = {
          "baseProfileId": guid,
          "canvas": "off",
          "webgl": {
            "value": "noise",
            "extra": {
              "vendor": "Google Inc.",
              "renderer": "ANGLE (Intel(R) HD Graphics 630 Direct3D11 vs_5_0 ps_5_0)"
            }
          },
          "timezone": {
            "value": "automatic",
            "extra": ip_dict['Timezone']
          },
          "geolocation": {
            "value": "automatic",
            "extra": {
              "latitude": float(ip_dict['Latitude']),
              "longitude": float(ip_dict['Longitude'])
            }
          },
          "proxy": {
            "value": proxyType,
            "extra": {
              "host": proxyIP,
              "port": int(proxyPort),
              "id": "username",
              "secret": "password"
            }
          },
          "webRtc": {
            "value": "automatic",
            "extra": {
              "privateIp": "2d2f78e7-1b1e-4345-a21b-07c904c98394.local",
              "publicIp": ip_dict['Your IP address']
            }
          },
          "fonts": {
            "value": "enabled",
            "extra": [
              
            ]
          },
          "plugins": {
            "value": "enabled",
            "extra": [          
            ]
          },
          "screen": {
            "value": "automatic",
            "extra":screen_size
          },
          "startPage": "https://whoer.net",
          "extensions": [
            
          ],
          "notes": "",
          "launcher": "automatic"
        }
        return profile_dict 
    # logic for connecting to webdriver.
    def driverConnection(self,guid):
        import selenium
        from selenium import webdriver
        from selenium.webdriver.remote.webdriver import WebDriver
        from selenium.webdriver.common.keys import Keys
        driver =  webdriver.Remote(command_executor=f'{self.host}/webdriver', desired_capabilities={'kameleo:profileId':guid})
        Keys = Keys
        return driver

if __name__ == "__main__":
    email = 'email'
    password = 'password'
    x = Kameleo_cli(email,password)
    driver = x.init_profile()
    #x.closeCLI()

