import requests
import json
import configparser

config = configparser.ConfigParser()
config.read('config.ini')

def main ():
    accessToken =  getWebAccessToken(config["creds"]["spDcCookie"])
    getFriendList(accessToken)


def getWebAccessToken (spDcCookie):
  url = "https://open.spotify.com/get_access_token?reason=transport&productType=web_player"
  headers = {"Cookie": f"sp_dc={spDcCookie}"}
  response = requests.get(url, headers=headers)
  return json.loads(response.text)["accessToken"]


def getFriendList(webAccessToken):
    url = "https://spclient.wg.spotify.com/user-profile-view/v3/profile/sws2obne5rwglf9x7podxy3nb/following"
    headers = {"Authorization": f"Bearer {webAccessToken}"}
    response = requests.get(url, headers=headers)
    print(response.text)


main()
