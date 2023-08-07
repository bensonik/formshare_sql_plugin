FormShare Remote SQL Plug-in
==============

This plug-in allows executing remote SQL in FormShare using HTTP. It requires:

- FormShare >= 2.22.0
- FormShare Analytics Plug-in (https://github.com/qlands/formshare_analytics_plugin)



Build and use the plugin
---------------

- Activate the FormShare environment.
```
$ . ./path/to/FormShare/bin/activate
```

- Change directory into your newly created plugin.
```
$ cd remoteSQL
```

- Build the plugin
```
$ python setup.py develop
```

- Add the plugin to the FormShare list of plugins by editing the following line in development.ini or production.ini
```
    #formshare.plugins = examplePlugin
    formshare.plugins = remoteSQL
```

- Run FormShare again

## How to use the remote SQL plugin

- Exchange credentials for a token

```python
import json
import requests

url = "http://localhost:5900"

login_dict = {
    "X-API-Key": "My API Key",
    "X-API-Secret": "My API secret",
}
headers = {"Content-type": "application/json", "Accept": "text/plain"}
r = requests.post(
    url + "/api/1/security/login", data=json.dumps(login_dict), headers=headers
)
token = r.json()["result"]["token"]
```

- Get the list of repositories that you have access

```python
headers["Authorization"] = "Bearer " + token
r = requests.get(url + "/user/[user_name]/analytics/tools/remote_sql/databases", headers=headers)
if r.status_code == 200:
    print(r.json())
```

- Get the tables of a schema

```python
dct = {"schema": "The schema ID. Starts is like FS_xxxxxxxx_xxxx_xxxx_xxxx_xxxxxxxxxxxx"}
r = requests.post(
    url + "url + "/user/[user_name]/analytics/tools/remote_sql/tables", data=json.dumps(dct), headers=headers)
if r.status_code == 200:
    print(r.json())
```

- Get the fields on a table

```python
dct = {"schema": "The schema ID. Starts if FS_xxxx", "table": "maintable"}
r = requests.post(
    url + "url + "/user/[user_name]/analytics/tools/remote_sql/fields", data=json.dumps(dct), headers=headers
)
if r.status_code == 200:
    print(r.json())
```

- Execute a remote SQL in a synchronous way. A successful execution always return data in zip file.

```python
dct = {"sql": "SELECT * FROM FS_xxxxxxxx_xxxx_xxxx_xxxx_xxxxxxxxxxxx.maintable"}
r = requests.post(
    url + "url + "/user/[user_name]/analytics/tools/remote_sql/execute", data=json.dumps(dct), headers=headers
)
if r.status_code == 200:
    open('./data.zip', 'wb').write(r.content)    
```

- Execute a remote SQL in an asynchronous way. The request returns a task ID

```python
dct = {"sql": "SELECT * FROM FS_xxxxxxxx_xxxx_xxxx_xxxx_xxxxxxxxxxxx.maintable"}
r = requests.post(
    url + "url + "/user/[user_name]/analytics/tools/remote_sql/execute?async=true", data=json.dumps(dct), headers=headers
)
if r.status_code == 200:
    task_id = r.json()["result"]["task_id"]
```

- Check the status of a task

```python
dct = {"task": "Task ID"}
r = requests.post(
    url + "url + "/user/[user_name]/analytics/tools/remote_sql/task_status", data=json.dumps(dct), headers=headers
)
if r.status_code == 200:
    print(r.json()["result"]["status"]
```

- Get the result of a finished task

```python
dct = {"task": "a326d519-b55c-4b7f-8d33-0f8a6261072f"}
r = requests.post(url + "/user/cquiros/analytics/tools/remote_sql/task_result",data=json.dumps(dct), headers=headers)
if r.status_code == 200:
    print("OK")
    open('./data.zip', 'wb').write(r.content)
```

