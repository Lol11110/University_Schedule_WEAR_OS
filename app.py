from flask import Flask, jsonify, request
import requests
from bs4 import BeautifulSoup
from datetime import datetime

app = Flask(__name__)

@app.route('/api/schedule', methods=['GET'])
def get_schedule():
    # Если дата не передана, берем сегодняшнюю
    date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    
    # URL твоего универа (КНИТУ/КХТИ) с подставленной датой
    url = f"https://www.kstu.ru/www_Ggrid.jsp?f=320&d={date_str}&g=47845&idk=55951"
    
    # Притворяемся обычным браузером, чтобы сайт нас не заблокировал
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    try:
        response = requests.get(url, headers=headers)
        response.encoding = 'windows-1251' # Часто старые .jsp сайты используют эту кодировку, либо 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        daily_schedule = []
        
# Устанавливаем правильную кодировку, указанную в метатеге сайта
        response.encoding = 'utf-8' 
        soup = BeautifulSoup(response.text, 'html.parser')
        
        daily_schedule = []
        
        # Ищем скрытый якорь с нужной датой в мобильной версии таблицы
        date_anchor = soup.find('a', attrs={'name': date_str})
        
        if date_anchor:
            # Поднимаемся до строки <tr>, в которой лежит этот якорь
            current_tr = date_anchor.find_parent('tr')
            
            # Перебираем все следующие строки таблицы
            for sibling in current_tr.find_next_siblings('tr'):
                # Если наткнулись на новый якорь (следующий день) — останавливаем цикл
                if sibling.find('a', attrs={'name': True}):
                    break
                
                # Ищем ячейки со временем и предметом
                tds = sibling.find_all('td')
                if len(tds) == 2:
                    time_div = tds[0].find('div', class_='col-12')
                    lesson_div = tds[1].find('div', class_='col-12')
                    
                    if time_div and lesson_div:
                        # Разбираем содержимое ячейки с парой на текстовые фрагменты.
                        # В HTML пустая пара выглядит как <b></b><br/><br> (даст пустой массив).
                        # Заполненная даст: ['Г-517', 'Иностранный язык (ПЗ)', '1 сен - 30 дек', 'Абдуллина Ю.Е.', '*1 гр']
                        fragments = list(lesson_div.stripped_strings)
                        
                        # Если массив не пустой — пара есть, забираем данные
                        if fragments:
                            # Объединяем "1 пара" и "08:00-09:30"
                            time_text = " ".join(time_div.stripped_strings) 
                            
                            room = fragments[0]
                            subject = fragments[1] if len(fragments) > 1 else ""
                            # Имя преподавателя обычно идет 4-м элементом после дат
                            teacher = fragments[3] if len(fragments) > 3 else "" 
                            # Если есть приписка подгруппы (например, *1 гр)
                            subgroup = fragments[4] if len(fragments) > 4 else ""
                            
                            daily_schedule.append({
                                "time": time_text,
                                "room": room,
                                "subject": f"{subject} {subgroup}".strip(),
                                "teacher": teacher
                            })
        
        return jsonify({
            "status": "success",
            "date": date_str,
            "lessons": daily_schedule
        })
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)