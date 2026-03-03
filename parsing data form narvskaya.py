  import bs4
import requests
import re   
import csv
from datetime import datetime

def parse_and_save_race_data(url):
    """
    Парсит и сохраняет данные гонки в CSV файл.
    """
    
    # Получаем данные с сайта
    response = requests.get(url)
    soup = bs4.BeautifulSoup(response.text, 'html.parser')
    race_name = soup.title.text.strip()
    
    # Извлекаем данные
    n_racers = int(soup.body.table.find_all('tr')[0].find_all('th')[-1].text)
    
    # Номера картов
    karts_row = soup.body.table.find_all('tr')[2]
    karts = list(map(int, karts_row.text.split('\n')[2:-1]))
    
    # Список гонщиков
    drivers = []
    drivers_row = soup.body.table.find_all('tr')[1]
    for i in drivers_row.text.split('\n'):
        if i != '' and i != 'Driver':
            drivers.append(i.strip())
    
    # Данные по кругам
    all_laps_data = []
    lap_rows = soup.body.table.find_all('tr')[3:-4]
    
    for lap_num, row in enumerate(lap_rows, 1):
        lap_data = []
        cells = row.find_all('td')
        
        for driver_idx, cell in enumerate(cells):
            try:
                cell_text = cell.text
                
                # Позиция
                position = int(cell.span.text[2:]) if cell.span else -1
                
                # Плюс-круги
                plus_laps = 0
                plus_match = re.findall(r'(\d+)l', cell_text)
                if plus_match:
                    plus_laps = int(plus_match[0])
                
                # Времена
                times = list(map(float, re.findall(r'\d+\.\d{3}', cell_text)))
                
                # Время больше минуты
                minute_match = re.search(r'(\d+):(\d+\.\d{3})', cell_text)
                if minute_match and times:
                    minutes = int(minute_match.group(1))
                    seconds = float(minute_match.group(2))
                    times[0] = minutes * 60 + seconds
                
                lap_data.append({
                    'lap': lap_num,
                    'driver': drivers[driver_idx] if driver_idx < len(drivers) else f"Driver_{driver_idx+1}",
                    'kart': karts[driver_idx] if driver_idx < len(karts) else None,
                    'position': position,
                    'lap_time': times[0] if len(times) > 0 else None,
                    'gap_leader': times[1] if len(times) > 1 else None,
                    'gap_next': times[2] if len(times) > 2 else None,
                    'plus_laps': plus_laps,
                })
                
            except:
                lap_data.append({
                    'lap': lap_num,
                    'driver': drivers[driver_idx] if driver_idx < len(drivers) else f"Driver_{driver_idx+1}",
                    'kart': karts[driver_idx] if driver_idx < len(karts) else None,
                    'position': -1,
                    'lap_time': None,
                    'gap_leader': None,
                    'gap_next': None,
                    'plus_laps': 0,
                })
        
        all_laps_data.append(lap_data)
    
    # Создаем имя файла
    timestamp = datetime.now().strftime("%Y%m%d")
    safe_name = re.sub(r'[^\w\s-]', '', race_name)
    safe_name = re.sub(r'[-\s]+', '_', safe_name)[:30]
    filename = f'project_karting\parsed data\complete_race_data_{safe_name}_{timestamp}.csv'
    
    # Сохраняем в CSV
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        # Информация о гонке
        writer.writerow(['Race:', race_name])
        writer.writerow(['URL:', url])
        writer.writerow(['Date:', datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        writer.writerow(['Drivers:', len(drivers)])
        writer.writerow(['Laps:', len(all_laps_data)])
        writer.writerow([])
        
        # Заголовки таблицы
        writer.writerow(['Lap', 'Driver', 'Kart', 'Position', 'Lap_Time', 'Gap_to_Leader', 'Gap_to_Next', 'Plus_Laps'])
        
        # Данные
        for lap_data in all_laps_data:
            for driver_data in lap_data:
                writer.writerow([
                    driver_data['lap'],
                    driver_data['driver'],
                    driver_data['kart'],
                    driver_data['position'] if driver_data['position'] != -1 else 'N/A',
                    f"{driver_data['lap_time']:.3f}" if driver_data['lap_time'] else 'N/A',
                    f"{driver_data['gap_leader']:.3f}" if driver_data['gap_leader'] else 'N/A',
                    f"{driver_data['gap_next']:.3f}" if driver_data['gap_next'] else 'N/A',
                    driver_data['plus_laps']
                ])
            writer.writerow(['*'])  # Пустая строка между кругами
    
    print(f"✅ Данные сохранены в файл: {filename}")
    print(f"🏁 Гонка: {race_name}")
    print(f"👥 Гонщиков: {len(drivers)}")
    print(f"⏱️  Кругов: {len(all_laps_data)}")
    
    return filename

# Запуск
if __name__ == "__main__":
    url = "https://timing.batyrshin.name/tracks/narvskaya/heats/106323"
    filename = parse_and_save_race_data(url)
    print(f"\nФайл готов для анализа: {filename}")
