#Proxy collector
The server collects and provides working proxy servers.

## Requirements
* Python 3.7 and higher
* Python packages. For install run command from command line:
    ```sh
    pip3 install -r requirements.txt 
    ```
* Optional: to running in container needed
    * docker version 19.03 and higher
    * docker compose version 3.8 and higher

## Run
0. On local machine
    * Run command from the project directory for running server
        ```sh
        python3 ./src/server.py
        ```
    * Press `CTRL + C` to stop server
0. Using docker compose
    * Run command from the project directory for running server
        ```sh
        docker-compose up -d
        ```
    * Run command to stop server        
        ```sh
        docker-compose down
        ```  

#### Supported request:
Path         | Request Type  | Description
|:-----------|:-------|:--------
/http_proxy  | GET   | Getting http proxy server
