import urllib.request
import urllib.parse
import re

data = urllib.parse.urlencode({'name':'Test','email':'test1234567@gmail.com','password':'pw'}).encode()
req = urllib.request.Request('http://localhost:5000/signup', data=data)
try:
    html = urllib.request.urlopen(req).read().decode()
    match = re.search(r'<div class="bg-red[^>]+>(.*?)</div>', html, re.DOTALL)
    print("Error text:", match.group(1).strip() if match else "No error div found")
except Exception as e:
    print("Request failed:", e)
