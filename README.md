# offline-neural-tts
 Офлайн сервер синтеза речи на нейронных сетях
 
## Зависимости

	* Версия python 3.7x
	
```
pip install https://github.com/kamnsv/ru_number_to text.git
pip install -r requirements.txt 
```
download https://models.silero.ai/models/tts/ru/ru_v3.pt


## Запуск

```
python server.py [PORT] [HOST]
```

## Обращение

* GET запросы

Запрос: `http://[HOST]:[PORT]/[TEXT]`

Ответ: > header 'Content-type: audio/wav'

* POST запросы
Запрос: 
```
header 'Content-Type: application/json' 
'{
    "text": "Добрый день! Как ваши дел+а?",
    "speaker": "xenia",
    "sample_rate": "48000", 
    "accent": "on", 
    "yo": "off",
    "digit": "on", 
    "abr": "on", 
    "trans": "on" 
}'
```
Ответ: `/Добрый день_ Как ваши дел_а_`
