FormShare Remote SQL Plug-in
==============

This plug-in allows executing remote SQL in FormShare using HTTP. It requires:

- FormShare >= 2.20.0
- FormShare Analytics Plug-in (https://github.com/qlands/formshare_analytics_plugin)



Getting Started
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
