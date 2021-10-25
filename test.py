import json 

with open('modules/authentication/access_tokens.json') as access_tokens_json:
    access_tokens = json.load(access_tokens_json)
    
print(type(access_tokens[0]))
print(access_tokens[1]['token'])
index = next((i for i, item in enumerate(access_tokens) if item["id"] == 908301928309128390), None)
print(index)
print(access_tokens)
access_tokens.pop(index)
print(access_tokens)
