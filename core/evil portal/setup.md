# installation
install hostapd and dnsmasq

`sudo apt install hostapd dnsmasq -y`

boom ur done

# note
DO NOT CHANGED VALUES IN BOTH CONFIGS THAT ARE WRAPPED IN %s

# switching pages
you can make your own pages, and do a post/get request to `/get`

for example:
post `{"username": "apple", "password": "banana", "email": "banana@example.com"}` to /get
- OR -
get request to the same endpoint `/get?username=apple&password=banana&email=banana@example.com`

apple and banana will come out on the display, but email wont
BUT email will be saved in the data dump file

# pages
https://github.com/bigbrodude6119/flipper-zero-evil-portal
