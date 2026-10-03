# daily
Check attendance of various web

Setup (python-telegram-bot 22 needs Python 3.10+)
```
python -m venv .venv
.venv\Scripts\python.exe -m pip install -U -r requirements.txt
```

Run `daily.bat`. Logs go to the `log` folder, which is created automatically.

You need two json files


file name = telegram.json
```
{
    "token" : "",
    "chatID" : ""
}
```

file name = personal.json
```
{
    "ondisk" : {
        "id" : "",
        "pwd" : ""
    },
    "yesfile" : {
        "id" : "",
        "pwd" : ""
    },
    "filenori" : {
        "id" : "",
        "pwd" : ""
    },
    "filebogo" : {
        "id" : "",
        "pwd" : ""
    },
    "inven" : {
        "id" : "",
        "pwd" : ""
    },
    "item_mania" : {
        "id" : "",
        "pwd" : ""
    }
}
```
![image](https://github.com/nebula0225/daily/assets/93500898/ef990cef-936c-4998-9581-0e674dca20d6)


A site without an entry in personal.json is skipped.

`inven2` and `item_mania2` run a second account. Add them to use it.

ex)
```
"inven2" : {
    "id" : "",
    "pwd" : ""
},
```
