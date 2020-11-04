#Proxy collector
The server collects and provides working proxy servers.

## Requirements
* Python 3.6 and or higher
* Python packages. For install run command from command line:
```sh
pip3 install -r requirements.txt 
```

## Run
```sh
python3 server.ry
```

####Supported request:
Path       | Request Type  | Description
|:---------|:-------|:--------
/http_proxy  | GET | Getting http proxy server
