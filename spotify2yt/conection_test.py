from ytmusicapi import YTMusic

ytmusic = YTMusic("browser.json")
info = ytmusic.get_account_info()
print(info)