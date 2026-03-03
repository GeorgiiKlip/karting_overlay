from moviepy import VideoFileClip, TextClip, CompositeVideoClip
from moviepy import vfx, afx # сжатие видео и аудио
from moviepy import *
from playsound import playsound
import csv

import time

import tkinter as tk  
from ffpyplayer.player import MediaPlayer  
from PIL import Image, ImageTk  

FONT_PATH = "consolas.ttf"

def parse_csv_data(path):
    """
    Улучшенный парсер CSV данных.
    Возвращает: 
    - data: структурированные данные как в старом формате
    - drivers_list: список имен гонщиков в порядке как в таблице
    """
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        lines = list(reader)
    
    # Извлекаем информацию о гонке
    race_name = lines[0][1] if len(lines) > 0 else "Unknown Race"
    num_drivers = int(lines[3][1]) if len(lines) > 3 and lines[3][1].isdigit() else 0
    num_laps = int(lines[4][1]) if len(lines) > 4 and lines[4][1].isdigit() else 0
    
    print(f"Гонка: {race_name}")
    print(f"Гонщиков: {num_drivers}, Кругов: {num_laps}")
    
    # Пропускаем заголовки (первые 7 строк + строка с заголовками таблицы)
    data_start = 7
    data_lines = lines[data_start:]
    structured_data = []
    lap_data = []
    
    for line in data_lines:

        # Пропускаем разделители и пустые строки
        if not line or (len(line) == 1 and line[0] == '*'):
            if lap_data:
                # Заполняем пропущенных гонщиков в этом круге
                while len(lap_data) < num_drivers:
                    lap_data.append([-1, 'N/A', -1, 1, [-1, -1, -1], 0])
                structured_data.append(lap_data)
                lap_data = []
            continue
               
        # Парсим данные гонщика
        try:
            lap_n_str = line[0] if len(line) > 0 else "-1"
            driver_name = line[1]
            kart_str = line[2] if len(line) > 2 else "N/A"
            position_str = line[3] if len(line) > 3 else "-1"
            lap_time_str = line[4] if len(line) > 4 else "N/A"
            gap_leader_str = line[5] if len(line) > 5 else "N/A"
            gap_next_str = line[6] if len(line) > 6 else "N/A"
            plus_laps_str = line[7] if len(line) > 7 else "0"


            # Конвертируем данные
            lap_n = -1
            if lap_n_str.isdigit():
                lap_n = int(lap_n_str)

            kart_n = -1
            if kart_str.isdigit():
                kart_n = int(kart_str)

            position = -1
            if position_str.isdigit():
                position = int(position_str)
            
            lap_time = -1
            if lap_time_str != 'N/A':
                try:
                    lap_time = float(lap_time_str)
                except ValueError:
                    pass
            
            gap_leader = -1
            if gap_leader_str != 'N/A':
                try:
                    gap_leader = float(gap_leader_str)
                except ValueError:
                    pass
            
            gap_next = -1
            if gap_next_str != 'N/A':
                try:
                    gap_next = float(gap_next_str)
                except ValueError:
                    pass
            
            plus_laps = 0
            if plus_laps_str.isdigit():
                plus_laps = int(plus_laps_str)
            
            # Сохраняем в структуру старого формата
            racer_data = [
                lap_n,  # Номер круга
                driver_name,  # Имя гонщика
                kart_n,  # Номер карта
                position,  # Позиция
                [lap_time, gap_leader, gap_next],  # Времена
                plus_laps,  # Плюс-круги
            ]
                        
            # Сохраняем данные в правильной позиции
            lap_data.append(racer_data)
            
        except Exception as e:
            print(f"Ошибка парсинга строки: {line}")
            print(f"Ошибка: {e}")
            continue
    
    # Добавляем последний круг, если он есть
    if lap_data:
        # Заполняем пропущенных гонщиков в последнем круге
        while len(lap_data) < num_drivers:
            lap_data.append([-1, 'N/A', -1, 1, [-1, -1, -1], 0])
        structured_data.append(lap_data)
    
    # Проверяем целостность данных
    for lap_n, lap in enumerate(structured_data):
        if len(lap) != num_drivers:
            print(f"Предупреждение: Круг {lap_n + 1} имеет {len(lap)} записей, ожидалось {num_drivers}")
            # Дополняем до нужного размера
            while len(lap) < num_drivers:
                lap.append([-1, 'N/A', -1, 1, [-1, -1, -1], 0])
    
    print(f"Найдено гонщиков: {num_drivers}")
    print(f"Создано кругов: {len(structured_data)}")
    
    return structured_data

def data_by_racer(data, racer_index):
    """
    Извлекает данные для конкретного гонщика по индексу.
    Возвращает: list_of_lap_times, list_of_front_gaps, list_of_positions
    """
    list_of_lap_times = []
    list_of_front_gaps = []
    list_of_positions = []
    
    for lap_data in data:
        if racer_index < len(lap_data):
            racer_data = lap_data[racer_index]
            lap_n, driver_name, kart_n, position, times, plus_laps = racer_data
            lap_time, gap_leader, gap_next = times
            
            list_of_lap_times.append(lap_time)
            list_of_front_gaps.append(gap_next if gap_next != -1 else gap_leader)
            list_of_positions.append(position)
        else:
            # Если гонщика нет на этом круге
            list_of_lap_times.append(-1)
            list_of_front_gaps.append(-1)
            list_of_positions.append(-1)
    
    return list_of_lap_times, list_of_front_gaps, list_of_positions

def racer_overlay(clip, data, racer_index, start, gap_before_start=40, gap_after_finish=10):
    """
    Создает оверлей с данными гонщика для видео.
    """
    lap_times, front_gap, position = data_by_racer(data, racer_index)
    
    # Фильтруем только валидные круги (где есть время)
    valid_lap_times = [t for t in lap_times if t != -1]
    if not valid_lap_times:
        print(f"Нет валидных данных для гонщика с индексом {racer_index}")
        return []
    
    texts = []
    mem_time = gap_before_start
    mem_time_str = ''
    duration = valid_lap_times[0] if valid_lap_times else 0
    
    # Определяем лучшее время круга среди валидных кругов
    best_lap_time = min([t for t in valid_lap_times if t > 0])
    
    for cur_lap in range(len(lap_times)):
        # Пропускаем невалидные круги
        if lap_times[cur_lap] == -1:
            continue
            
        mem_time += duration
        
        # Определяем продолжительность следующего сегмента
        if cur_lap + 1 < len(lap_times):
            next_lap_time = lap_times[cur_lap + 1]
            if next_lap_time == -1:
                # Ищем следующий валидный круг
                for future_lap in range(cur_lap + 2, len(lap_times)):
                    if lap_times[future_lap] != -1:
                        next_lap_time = lap_times[future_lap]
                        break
                else:
                    next_lap_time = gap_after_finish
            duration = next_lap_time
        else:
            duration = gap_after_finish
        
        # Добавляем информацию о круге
        
        mem_time_str += f'L{cur_lap + 1}: {lap_times[cur_lap]}'
        
        # Текст времени круга
        if lap_times[cur_lap] == min(lap_times) and lap_times[cur_lap] != -1:
            text_lap_times = TextClip(
                font=FONT_PATH,
                text=mem_time_str, 
                font_size=TEXT_SIZE,
                margin=(1,5),
                color='purple',
                bg_color='rgba(0,0,0,100)'
            )
        else:
            text_lap_times = TextClip(
                font=FONT_PATH,
                text=mem_time_str, 
                font_size=TEXT_SIZE,
                margin=(1,5),
                color='white',
                bg_color='rgba(0,0,0,100)'
            )
        
        pozition = (0, clip.size[1] / 2 - text_lap_times.size[1])

        text_lap_times = text_lap_times.with_position(pozition).with_duration(duration).with_start(mem_time)
        
        # Текст позиции и интервала
        pos_text = f'P{position[cur_lap]}' if position[cur_lap] != -1 else 'DNF'
        gap_text = f'+{front_gap[cur_lap]:.1f}' if front_gap[cur_lap] != -1 else ''
        text_front_gap = TextClip(
            font=FONT_PATH,
            text=f'{pos_text} gap: {gap_text}', 
            font_size=TEXT_SIZE, 
            color='white',
            bg_color='Black',
            margin=(1,3)
        )
        
        pozition = (0,0)

        text_front_gap = text_front_gap.with_position(pozition).with_duration(duration).with_start(mem_time)
        
        # Добавляем в список
        mem_time_str += '\n'
        texts.append(text_lap_times)
        texts.append(text_front_gap)
    
    return texts

def standings_overlay(clip, data, racer_index, drivers_list, start, gap_before_start=40, gap_after_finish=10):
    lap_times, _, _ = data_by_racer(data, racer_index)
    # Фильтруем только валидные круги (где есть время)
    valid_lap_times = [t for t in lap_times if t != -1]
    if not valid_lap_times:
        print(f"Нет валидных данных для гонщика с индексом {racer_index}")
        return []
    
    texts = []
    mem_time = gap_before_start
    duration = valid_lap_times[0] if valid_lap_times else 0
        
    for cur_lap in range(len(lap_times)):
        # Пропускаем невалидные круги
        if lap_times[cur_lap] == -1:
            continue
            
        mem_time += duration
        
        # Определяем продолжительность следующего сегмента
        if cur_lap + 1 < len(lap_times):
            next_lap_time = lap_times[cur_lap + 1]
            if next_lap_time == -1:
                # Ищем следующий валидный круг
                for future_lap in range(cur_lap + 2, len(lap_times)):
                    if lap_times[future_lap] != -1:
                        next_lap_time = lap_times[future_lap]
                        break
                else:
                    next_lap_time = gap_after_finish
            duration = next_lap_time
        else:
            duration = gap_after_finish
        
        # Добавляем информацию о круге
        
        standings_list = []
        for person in range(len(data[cur_lap])):
            cur_lap_with_skipped = cur_lap + data[cur_lap][person][5] # Корректируем индекс круга если отстает на круг(и)
            standings_list.append([data[cur_lap_with_skipped][person][3], drivers_list[person][0:3], data[cur_lap_with_skipped][person][4][2]]) 

        standings = f'lap {cur_lap + 1}\n'
        for person in sorted(standings_list):
            if person[2] != -1:
                standings += f'P{person[0]} {person[1]} +{person[2]}\n'
            elif person[0] == -1:
                standings += f'P{person[0]} {person[1]} led\n'
        
        standings = standings[0:-1]
        print(standings)
        
        # Текст времени круга
        text_lap_times = TextClip(
            text=standings, 
            font_size=round(TEXT_SIZE * 0.75), 
            color='white',
            bg_color='rgba(0,0,0,100)',
            font=FONT_PATH,
            margin=(1,5)
        )

        pozition = (clip.size[0] - text_lap_times.size[0], round(clip.size[0] / 8))

        text_lap_times = text_lap_times.with_position(pozition).with_duration(duration).with_start(mem_time)
                
        # Добавляем в список
        texts.append(text_lap_times)
    
    return texts


def racer_overlay_only_lap_times(clip, lap_times, gap_before_start=40, gap_after_finish=10):
    """
    Создает оверлей с данными гонщика для видео.
    """
    
    texts = []
    mem_time = gap_before_start
    mem_time_str = ''
    duration = lap_times[0] if lap_times else 0
    
    for cur_lap in range(len(lap_times)):
        # Пропускаем невалидные круги
        if lap_times[cur_lap] == -1:
            continue
            
        mem_time += duration
        
        # Определяем продолжительность следующего сегмента
        if cur_lap + 1 < len(lap_times):
            next_lap_time = lap_times[cur_lap + 1]
            if next_lap_time == -1:
                # Ищем следующий валидный круг
                for future_lap in range(cur_lap + 2, len(lap_times)):
                    if lap_times[future_lap] != -1:
                        next_lap_time = lap_times[future_lap]
                        break
                else:
                    next_lap_time = gap_after_finish
            duration = next_lap_time
        else:
            duration = gap_after_finish
        
        # Добавляем информацию о круге
        
        mem_time_str += f'L{cur_lap + 1}: {lap_times[cur_lap]}'
        
        # Текст времени круга
        if lap_times[cur_lap] == min(lap_times) and lap_times[cur_lap] != -1:
            text_lap_times = TextClip(
                font=FONT_PATH,
                text=mem_time_str, 
                font_size=TEXT_SIZE,
                margin=(1,5),
                color='purple',
                bg_color='rgba(0,0,0,100)'
            )
        else:
            text_lap_times = TextClip(
                font=FONT_PATH,
                text=mem_time_str, 
                font_size=TEXT_SIZE,
                margin=(1,5),
                color='white',
                bg_color='rgba(0,0,0,100)'
            )
        
        pozition = (0, clip.size[1] / 2 - text_lap_times.size[1])

        text_lap_times = text_lap_times.with_position(pozition).with_duration(duration).with_start(mem_time)
        
        # Добавляем в список
        mem_time_str += '\n'
        texts.append(text_lap_times)
    
    return texts


class TkinterFFPyPlayer:  
    def __init__(self, root, video_path):  
        self.root = root  
        self.root.title("ffpyplayer (FFmpeg) Video Player")  
 
        # ffpyplayer setup  
        self.player = MediaPlayer(video_path)  
        self.video_label = tk.Label(root)  
        self.video_label.pack(padx=10, pady=10)  
 
        # Control frame  
        self.control_frame = tk.Frame(root)  
        self.control_frame.pack(pady=5)  
 
        self.play_btn = tk.Button(  
            self.control_frame, text="Play", command=self.toggle_play  
        )  
        self.play_btn.grid(row=0, column=2, padx=5) 

        self.next_frame = tk.Button(  
            self.control_frame, text=">", command=self.frame_forward  
        )  
        self.next_frame.grid(row=0, column=4, padx=5) 

        self.plus = tk.Button(  
            self.control_frame, text="+5s", command=self.plus_5_seconds 
        )  
        self.plus.grid(row=0, column=3, padx=5) 

        self.minus = tk.Button(  
            self.control_frame, text="-5s", command=self.minyus_5_seconds  
        )
        self.minus.grid(row=0, column=1, padx=5) 

        self.ok_buutton = tk.Button(  
            self.control_frame, text="Ok", command=self.ok  
        )
        self.ok_buutton.grid(row=0, column=5, padx=5)
 
        self.is_playing = False  
        self.update_frame()  
 
    def toggle_play(self):  
        self.is_playing = not self.is_playing
        self.player.set_pause(not self.is_playing)
        self.play_btn.config(text="Pause" if self.is_playing else "Play")

    def frame_forward(self):
        self.is_playing = False
        self.player.set_pause(self.is_playing)
        frame, val = self.player.get_frame()

        if frame is not None:
            # Convert ffpyplayer frame to Pillow Image  
            img, time = frame
            img = Image.frombytes("RGB", img.get_size(), img.to_bytearray()[0])  
            imgtk = ImageTk.PhotoImage(image=img)  
            self.video_label.imgtk = imgtk  
            self.video_label.config(image=imgtk)
    
    def plus_5_seconds(self):
        self.player.seek(5, relative=True)
    
    def minyus_5_seconds(self):
        self.player.seek(-5, relative=True)

    def ok(self):
        self.start = self.player.get_pts()
        self.root.destroy()
 
    def update_frame(self):  
        if self.is_playing:  
            frame, val = self.player.get_frame()
 
            if frame is not None:  
                # Convert ffpyplayer frame to Pillow Image  
                img, time = frame
                img = Image.frombytes("RGB", img.get_size(), img.to_bytearray()[0])  
                imgtk = ImageTk.PhotoImage(image=img)  
                self.video_label.imgtk = imgtk  
                self.video_label.config(image=imgtk)  
 
        # Update every ~30ms (adjust based on FPS)  
        self.root.after(int(round(1000 / FPS)), self.update_frame)  
 


class TkinterCollectingData:  
    def __init__(self, root):  
        self.root = root  
        self.root.title("Data Collector")  
  
        # Control frame  
        self.control_frame = tk.Frame(root)  
        self.control_frame.pack(pady=5)  
 
        self.play_btn = tk.Button(  
            self.control_frame, text="Ok", command=self.toggle_Ok
        )  
        self.play_btn.grid(row=13, column=0, padx=5, pady=5) 
  
    def toggle_Ok(self):
        self.clip_path = clip_path_entry.get()
        self.data_path = data_path_entry.get()
        self.output_path = output_path_entry.get()
        self.target_name = target_name_entry.get()
        self.gap_before = gap_before_entry.get()
        self.gap_after = gap_after_entry.get()
        self.compress_video_check = compress_video_check.get()
        self.compress_video_entry = compress_video_entry.get()
        self.render_check = render_check.get()
        self.preview_check = preview_check.get()
        self.only_1_dtiver_check = only_1_dtiver_check.get()
        self.lap_times_entry = lap_times_entry.get()
        root.destroy()

class TkinterEntryData:  
    def __init__(self, control_frame, label_text, default_value, row):   
  
        self.label = tk.Label(control_frame, text=label_text)  
        self.label.grid(row=row, column=0, padx=5, pady=5)  
  
        self.entry = tk.Entry(control_frame,  width=50)  
        self.entry.insert(0, default_value)  
        self.entry.grid(row=row, column=1, padx=5, pady=5) 

    def get(self):  
        return self.entry.get()

class TkinterCheckbuttonData:  
    def __init__(self, control_frame, label_text, default_value, row):   
  
        self.var = tk.IntVar(value=default_value)  
        self.checkbutton = tk.Checkbutton(control_frame, text=label_text, variable=self.var)  
        self.checkbutton.grid(row=row, column=0, padx=5, pady=5)  

    def get(self):  
        return bool(self.var.get())


# Основной код
if __name__ == "__main__":

    root = tk.Tk()

    data_from_user = TkinterCollectingData(root) 
    clip_path_entry = TkinterEntryData(data_from_user.control_frame, "Путь к видеофайлу:", r"C:\Users\Mi\Desktop\Картинг\Primo student 2025.12.26\студ 3 этап примо overlay 26.12.2025.mp4", 0)
    data_path_entry = TkinterEntryData(data_from_user.control_frame, "Путь к CSV файлу:", r"project_karting\parsed data\complete_race_data_Гонка_Новичков_Квалификация_3_20251222.csv", 1)
    output_path_entry = TkinterEntryData(data_from_user.control_frame, "Путь к выходному видеофайлу:", r"C:\Users\Mi\Desktop\Картинг\test1.mp4", 2)
    target_name_entry = TkinterEntryData(data_from_user.control_frame, "Имя гонщика:", "EGGORKA", 3)
    gap_before_entry = TkinterEntryData(data_from_user.control_frame, "Задержка до старта (сек):", "5", 5)
    gap_after_entry = TkinterEntryData(data_from_user.control_frame, "Задержка после финиша (сек):", "5", 6)
    compress_video_check = TkinterCheckbuttonData(data_from_user.control_frame, "Сжимать видео", False, 7)
    compress_video_entry = TkinterEntryData(data_from_user.control_frame, "Высота видео после сжатия", "480", 8)
    render_check = TkinterCheckbuttonData(data_from_user.control_frame, "Рендерить видео", False, 9)
    preview_check = TkinterCheckbuttonData(data_from_user.control_frame, "Показывать превью", False, 10)
    only_1_dtiver_check = TkinterCheckbuttonData(data_from_user.control_frame, "Только 1 гонщик (заполнить вручную времена кругов)", False, 11)
    lap_times_entry = TkinterEntryData(data_from_user.control_frame, "Времена кругов через запятую (если только 1 гонщик):", "31.906, 29.963, 31.307", 12)

    root.mainloop()
    
    clip =  VideoFileClip(data_from_user.clip_path)
    csv_file = data_from_user.data_path
    output_file = data_from_user.output_path
    target_name = data_from_user.target_name
    gap_before = int(data_from_user.gap_before)
    gap_after = int(data_from_user.gap_after)
    compress_video = [data_from_user.compress_video_check, int(data_from_user.compress_video_entry)] # Сжимать ли видео
    render = data_from_user.render_check # Установите в False для пропуска рендеринга видео
    preview = data_from_user.preview_check # Показать несколько превью
    only_1_dtiver = data_from_user.only_1_dtiver_check # Заполнять ли времена кругов вручную
    if only_1_dtiver:
        lap_times_str = data_from_user.lap_times_entry
        lap_times = [float(t.strip()) for t in lap_times_str.split(',') if t.strip().replace('.','',1).isdigit()]


    root = tk.Tk()
    global FPS
    FPS = round(clip.fps)
    player = TkinterFFPyPlayer(root, video_path=data_from_user.clip_path)  
    root.mainloop()

    start = player.start

    if compress_video[0]:
        clip = clip.with_effects([vfx.Resize(height=compress_video[1])])

    global TEXT_SIZE
    TEXT_SIZE = 0.05 * clip.size[1]

    if only_1_dtiver:

        total_time = sum(lap_times)

        # Обрезаем видео
        clip = clip.subclipped(
            start - gap_before,
            start + total_time + gap_after
        )

        time_overlays = racer_overlay_only_lap_times(
            clip, lap_times,
            gap_before, gap_after
        )

        all_overlays = time_overlays

    else:
        data = parse_csv_data(csv_file)
        drivers_list = [name[1] for name in data[0]]
        print(drivers_list)

        try:
            target_index = drivers_list.index(target_name)
            print(f"Найден гонщик: {target_name}, индекс: {target_index}")
        except ValueError:
            print(f"Гонщик {target_name} не найден. Доступные:")
            for i, name in enumerate(drivers_list):
                print(f"  {i}: {name}")
            target_index = 0  # По умолчанию первый гонщик

    
        # Получаем данные целевого гонщика для расчета длительности
        lap_times, _, _ = data_by_racer(data, target_index)
        valid_times = [t for t in lap_times if t != -1]
        
        total_time = sum(valid_times)

        # Обрезаем видео
        clip = clip.subclipped(
            start - gap_before,
            start + total_time + gap_after
        )
        
        # Оверлей времени кругов (левый бок)
        time_overlays = racer_overlay(
            clip, data, target_index,
            gap_before, gap_after
        )

        # Оверлей позиций (правый бок)
        standings_overlays = standings_overlay(
            clip, data, target_index, drivers_list, start,
            gap_before, gap_after
        )
        
        all_overlays = time_overlays + standings_overlays
        


    video_with_overlays = CompositeVideoClip([clip] + all_overlays)

    if preview:
        video_with_overlays.show(gap_before)
        video_with_overlays.show(gap_before + lap_times[0])
        video_with_overlays.show(gap_before + lap_times[0] + lap_times[1])
        video_with_overlays.show(gap_before + sum(lap_times[0:-1]))

    if render:
        video_with_overlays.write_videofile(output_file, codec='libx264', audio_codec='aac')
    
    # Звук завершения
    playsound('project_karting/apple-pay-succes.mp3')
    
    print("Готово!")
    
