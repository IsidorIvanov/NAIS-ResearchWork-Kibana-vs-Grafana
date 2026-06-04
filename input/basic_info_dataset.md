# Osnovne informacije o datasetu

## Osnovne informacije
- Fajl: `access_logs_merged.csv`
- Broj redova: `5,000`
- Broj kolona: `12`
- Kolone: `timestamp`, `method`, `path`, `status_code`, `response_time_ms`, `bytes_sent`, `user_agent`, `ip_address`, `referrer`, `name`, `region`, `role`

## Tipovi podataka

```text
timestamp           datetime64[ns]
method                      object
path                        object
status_code                  int64
response_time_ms             int64
bytes_sent                   int64
user_agent                  object
ip_address                  object
referrer                    object
name                        object
region                      object
role                        object
```

## Kvalitet podataka
- Duplirani redovi: `0`
- Nema nedostajućih vrednosti.

## Vremenski opseg
- Od: `2024-01-01 00:15:12`
- Do: `2024-02-06 13:19:06`
- Broj dana u datasetu: `37`

### Broj zahteva po danu

```text
timestamp
2024-01-01    154
2024-01-02    181
2024-01-03    157
2024-01-04    157
2024-01-05    144
2024-01-06    114
2024-01-07     72
2024-01-08    151
2024-01-09    182
2024-01-10    159
2024-01-11    145
2024-01-12    146
2024-01-13    102
2024-01-14     91
2024-01-15    167
2024-01-16    147
2024-01-17    164
2024-01-18    152
2024-01-19    158
2024-01-20     94
2024-01-21     70
2024-01-22    159
2024-01-23    160
2024-01-24    138
2024-01-25    158
2024-01-26    170
2024-01-27     88
2024-01-28     73
2024-01-29    154
2024-01-30    156
2024-01-31    153
2024-02-01    144
2024-02-02    168
2024-02-03     84
2024-02-04     68
2024-02-05    144
2024-02-06     76
```

## Numeričke metrike

```text
       status_code  response_time_ms  bytes_sent
count      5000.00           5000.00     5000.00
mean        239.22            180.73     9109.84
std          78.67            310.13    22595.24
min         200.00              1.00        5.00
25%         200.00             40.00     1074.00
50%         200.00             90.00     3058.50
75%         201.00            199.25     8474.50
max         503.00           7510.00   778011.00
```

### Percentili vremena odziva (ms)

```text
0.50      90.00
0.75     199.25
0.90     406.00
0.95     627.10
0.99    1459.04
```
- Ukupno poslato podataka: `43.44 MB`
- Prosečno po zahtevu: `8.90 KB`

## HTTP statusi

```text
status_code
200    3638
201     245
301     118
304     292
400     192
401     156
403      52
404     197
500      85
503      25
```
- 4xx greške: `597` (`11.94%`)
- 5xx greške: `110` (`2.20%`)

## Najčešće kategorije

### Najčešće vrednosti za `method`

```text
method
GET       3360
POST      1013
PUT        378
DELETE     158
PATCH       91
```

### Najčešće vrednosti za `path`

```text
path
/about                     191
/api/v2/shipping/rates     167
/api/v2/wishlist           167
/static/images/logo.png    166
/contact                   166
/static/js/app.js          166
/sitemap.xml               164
/docs/{page}               159
/login                     159
/api/v2/categories         158
```

### Najčešće vrednosti za `user_agent`

```text
user_agent
Go-http-client/2.0                                                                 537
Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 Chrome/122.0.0.0       517
Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/605.1.15        510
Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0      508
PostmanRuntime/7.36.1                                                              501
Googlebot/2.1 (+http://www.google.com/bot.html)                                    498
Bingbot/2.0 (+http://www.bing.com/bingbot.htm)                                     496
Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3_1) AppleWebKit/605.1.15 Safari/17.3    490
curl/8.4.0                                                                         479
python-requests/2.31.0                                                             464
```

### Najčešće vrednosti za `ip_address`

```text
ip_address
183.149.15.230    6
186.90.214.239    5
151.170.66.123    5
201.103.7.69      5
62.120.200.11     5
5.76.255.249      5
6.25.183.255      5
88.243.61.129     5
129.1.191.209     5
78.228.36.35      5
```

### Najčešće vrednosti za `referrer`

```text
referrer
https://reddit.com/r/webdev    1037
https://www.google.com/        1027
-                               997
https://twitter.com/            994
https://www.bing.com/           945
```

### Najčešće vrednosti za `name`

```text
name
web-prod-03    1688
web-prod-01    1670
web-prod-02    1642
```

### Najčešće vrednosti za `region`

```text
region
us-east-1    3312
us-west-2    1688
```

### Najčešće vrednosti za `role`

```text
role
api       3312
static    1688
```

## Performanse po serveru

```text
             count    mean  median   max
name                                    
web-prod-02   1642  183.93    94.0  7510
web-prod-01   1670  179.25    88.0  4633
web-prod-03   1688  179.08    88.0  5271
```

## Putanje sa najviše grešaka

```text
path
/api/v2/wishlist           32
/docs/{page}               29
/api/v2/shipping/rates     29
/static/js/app.js          26
/docs                      26
/api/v2/users/login        26
/api/v2/categories         25
/static/images/logo.png    25
/                          24
/favicon.ico               24
```
