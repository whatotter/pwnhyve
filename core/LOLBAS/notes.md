[cmstp](https://lolbas-project.github.io/lolbas/Binaries/Cmstp/) is too much for a pi - maybe host it on the pi? would break the whole duckyscript thing  
maybe add a file hosting command to duckyscript commands

5/14/23: i will go with above answer but i will not do that
5/27/23: what the fuck did i say above

# ENVIROMENT VARIABLES
`DS_FILE` is used for files on the host - exfil and etc.  
`DS_IP` is used for target ip of a command  
`DS_PORT` is used for target port of a command  
`DS_WEBDAV` is used for a web drive, ex: ftp for exfilling files  
`DS_EXECUTABLE` is used for an executable to run on the host  
`DS_REVERSE_SHELL` is used for a reverse shell on another host: example of this value is 10.10.10.10:8466  
`DS_INPUT` is usually used for input files, like a prompt or etc.
`DS_OUTPUT` is usually used for output files, like logs
`DS_SOURCE` is used for a source url, to download payloads or etc.
`DS_DIRECTORY` is used for the directory of a file
`DS_HEXFILE` is rarely used but is used for `certutil-hex.txt` and more to come
`DS_FAKEFILE` is used for `alt. data streams` in `cmd`, and is used for running a file as a batch file