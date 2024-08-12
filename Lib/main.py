import tkinter as tk
import networkx as nx
import numpy as np


# Определим функцию для вычисления евклидова расстояния между точками
def euclidean_distance(point1, point2):
    return np.linalg.norm(np.array(point1) - np.array(point2))


class DraggablePoint:
    point_counter = 1  # Счетчик для имен точек

    def __init__(self, canvas, x, y, app):
        self.canvas = canvas
        self.point_name = str(DraggablePoint.point_counter)
        DraggablePoint.point_counter += 1
        self.app = app
        self.is_draggable = True  # Флаг для разрешения/запрещения перетаскивания
        self.oval = canvas.create_oval(x - 8, y - 8, x + 8, y + 8, fill="black", tags=("draggable", self.point_name))
        self.text = canvas.create_text(x + 10, y - 10, text=self.point_name, anchor=tk.W, font=("Arial", 10))
        self.canvas.tag_bind(self.oval, "<ButtonPress-1>", self.on_press)
        self.canvas.tag_bind(self.oval, "<B1-Motion>", self.on_drag)
        self.canvas.tag_bind(self.oval, "<ButtonRelease-1>", self.on_release)
        self.canvas.tag_bind(self.oval, "<Button-3>", self.on_right_click)

        self.is_dragging = False
        self.start_x = 0
        self.start_y = 0

    def on_press(self, event):
        if self.is_draggable and not self.app.add_mode and not self.app.link_mode:
            self.is_dragging = True
            self.start_x = event.x
            self.start_y = event.y

    def on_drag(self, event):
        if self.is_dragging:
            delta_x = event.x - self.start_x
            delta_y = event.y - self.start_y
            self.canvas.move(self.oval, delta_x, delta_y)
            self.canvas.move(self.text, delta_x, delta_y)
            self.start_x = event.x
            self.start_y = event.y

            # Обновление координат точки в списке
            self.app.update_point_coordinates(self.point_name, event.x, event.y)

            # Обновление координат связей на холсте
            self.app.update_edges_coordinates()

    def on_release(self, event):
        self.is_dragging = False

    def on_right_click(self, event):
        if self.app.delete_mode:
            self.app.delete_point_by_name(self.point_name)

class PointFieldApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Точечное поле")

        self.adjacency_list = {}


        # Получение размеров экрана
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()

        # Установка координат для окна Tkinter
        window_width = 1000  # Ширина окна
        window_height = 720  # Высота окна
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2

        self.master.geometry(f"{window_width}x{window_height}+{x}+{y}")  # Установка размеров и положения окна

        self.master.resizable(False, False)
        # Создание холста
        self.canvas = tk.Canvas(self.master, width=600, height=720, bg="white")
        self.canvas.pack(side=tk.LEFT, expand=tk.YES, fill=tk.BOTH)

        # Виджет для отображения режима добавления
        self.mode_label = tk.Label(self.master, text="", font=("Arial", 16), padx=10, pady=5, width=18)
        self.mode_label.pack()

        self.points = {}  # Словарь для хранения информации о точках
        self.edges = []  # Список для хранения информации о связях между точками
        self.draggable_points = []  # Список для хранения объектов DraggablePoint
        self.add_mode = False
        self.delete_mode = False
        self.edit_mode = False
        self.link_mode = False  # Режим связи

        # Создание фрейма для кнопок
        button_frame = tk.Frame(self.master)
        button_frame.pack(fill=tk.Y, anchor="center")

        # Кнопка "Добавить"
        self.add_button = tk.Button(button_frame, text="Добавить", command=self.toggle_add_mode, width=18, height=2, font=('Arial', 15, 'bold'))
        self.add_button.pack(pady=10)

        # Кнопка "Редактировать"
        self.edit_button = tk.Button(button_frame, text="Редактировать", command=self.enable_edit_mode, width=18, height=2, font=('Arial', 15, 'bold'))
        self.edit_button.pack(pady=10)

        # Кнопка "Удалить"
        self.delete_button = tk.Button(button_frame, text="Удалить", command=self.enable_delete_mode, width=18, height=2, font=('Arial', 15, 'bold'))
        self.delete_button.pack(pady=10)

        # Кнопка "Связать"
        self.link_button = tk.Button(button_frame, text="Связать", command=self.toggle_link_mode, width=18, height=2, font=('Arial', 15, 'bold'))
        self.link_button.pack(pady=10)


        # Фрейм для текстового поля и метки
        entry_frame = tk.Frame(button_frame)
        entry_frame.pack(pady=10)

        # Метка "Точка начала"
        start_point_label = tk.Label(entry_frame, text="Начальная точка:", font=("Arial", 12))
        start_point_label.grid(row=0, column=0)

        # Поле ввода для точки начала
        self.start_point_entry = tk.Entry(entry_frame, font=("Arial", 12))
        self.start_point_entry.grid(row=0, column=1)

        # Метка "Конечная точка"
        end_point_label = tk.Label(entry_frame, text="Конечная точка:", font=("Arial", 12))
        end_point_label.grid(row=1, column=0)

        # Поле ввода для конечной точки
        self.end_point_entry = tk.Entry(entry_frame, font=("Arial", 12))
        self.end_point_entry.grid(row=1, column=1)

        # Кнопка "Рассчитать"
        self.calculate_button = tk.Button(entry_frame, text="Рассчитать", command=self.calculate_path, width=18,
                                          height=2, font=('Arial', 15, 'bold'))
        self.calculate_button.grid(row=3, column=0, columnspan=2, pady=10)

        # Метка "Кратчайший путь"
        shortest_path_label = tk.Label(entry_frame, text="Кратчайший путь:", font=("Arial", 12))
        shortest_path_label.grid(row=4, column=0)

        # Поле для вывода кратчайшего пути
        self.shortest_path_entry = tk.Entry(entry_frame, font=("Arial", 12), state='disabled')
        self.shortest_path_entry.grid(row=4, column=1)


        # Привязка события "Button-1" к методу place_point
        self.canvas.bind("<Button-1>", self.place_point)


    def calculate_path(self):
        start_point_name = self.start_point_entry.get()
        end_point_name = self.end_point_entry.get()

        # Проверка наличия начальной и конечной точек в списке точек
        if start_point_name not in self.points or end_point_name not in self.points:
            self.shortest_path_entry.config(state='normal', fg="red")  # Разрешаем редактирование
            self.shortest_path_entry.delete(0, tk.END)  # Очищаем поле
            self.shortest_path_entry.insert(0, "Точки не существует")  # Вставляем сообщение о том, что точек нет
            self.shortest_path_entry.config(state='disabled')  # Запрещаем редактирование
            return

        # Создаем граф
        G = nx.Graph()

        # Добавляем ребра с учетом весов (евклидовых расстояний)
        for edge in self.edges:
            point1 = (self.points[edge[0]]["x"], self.points[edge[0]]["y"])
            point2 = (self.points[edge[1]]["x"], self.points[edge[1]]["y"])
            weight = euclidean_distance(point1, point2)
            G.add_edge(edge[0], edge[1], weight=weight)

        try:
            # Находим кратчайший путь
            shortest_path = nx.shortest_path(G, source=start_point_name, target=end_point_name, weight='weight')

            # Преобразуем путь в строку
            shortest_path_str = "-".join(shortest_path)

            # Выводим результат
            self.shortest_path_entry.config(state='normal')  # Разрешаем редактирование
            self.shortest_path_entry.delete(0, tk.END)  # Очищаем поле
            self.shortest_path_entry.insert(0, shortest_path_str)  # Вставляем кратчайший путь
        except nx.NetworkXNoPath:
            self.shortest_path_entry.config(state='normal')  # Разрешаем редактирование
            self.shortest_path_entry.delete(0, tk.END)  # Очищаем поле
            self.shortest_path_entry.insert(0, "Пути не существует")  # Вставляем сообщение о том, что пути нет
        finally:
            self.shortest_path_entry.config(state='disabled')  # Запрещаем редактирование


    def update_point_coordinates(self, point_name, x, y):
        if point_name in self.points:
            self.points[point_name]["x"] = x
            self.points[point_name]["y"] = y
            print(f"Точка {point_name}: ({x}, {y})")

    def update_edges(self):
        if self.link_mode:
            # Очистим список смежности
            self.adjacency_list = {point: [] for point in self.points}

            # Удаляем все линии
            self.canvas.delete("line")

            # Обновим список рёбер
            self.edges = []
            for draggable_point in self.draggable_points:
                point_name = draggable_point.point_name
                connected_points = self.get_connected_points(point_name)
                for connected_point in connected_points:
                    # Добавляем связь в список рёбер, если её ещё нет
                    if (point_name, connected_point) not in self.edges and (connected_point, point_name) not in self.edges:
                        self.edges.append((point_name, connected_point))

                        # Отображаем связи
                        start_x = self.points[point_name]["x"]
                        start_y = self.points[point_name]["y"]
                        end_x = self.points[connected_point]["x"]
                        end_y = self.points[connected_point]["y"]
                        line_tag = f"line_{point_name}_{connected_point}"
                        self.canvas.create_line(start_x, start_y, end_x, end_y, tags=("line", line_tag), fill="blue")

            # Выводим список смежности в консоль
            print("Список смежности:")
            for point, connected_points in self.adjacency_list.items():
                print(f"{point}: {connected_points}")


    def place_point(self, event):
        if self.add_mode:
            x, y = event.x, event.y

            # Создание объекта DraggablePoint
            draggable_point = DraggablePoint(self.canvas, x, y, self)

            # Добавление точки в словарь с информацией
            self.points[draggable_point.point_name] = {"x": x, "y": y}

            # Добавление объекта DraggablePoint в список
            self.draggable_points.append(draggable_point)

            # Вывод информации в консоль
            print(f"Добавлена точка {draggable_point.point_name}: ({x}, {y})")

    def delete_point_by_name(self, point_name):
        if point_name in self.points:
            # Удаляем связи, касающиеся только этой точки
            connected_points = self.adjacency_list.get(point_name, [])

            # Удаляем линии на холсте, соединенные с удаляемой точкой
            for connected_point in connected_points:
                line_tag_forward = f"line_{point_name}_{connected_point}"
                line_tag_reverse = f"line_{connected_point}_{point_name}"
                self.canvas.delete(line_tag_forward)
                self.canvas.delete(line_tag_reverse)

            # Удаляем связи из списка связей
            self.edges = [edge for edge in self.edges if point_name not in edge]

            # Удаляем точку из списка смежности других точек
            for connected_point in connected_points:
                self.adjacency_list[connected_point] = [p for p in self.adjacency_list[connected_point] if
                                                        p != point_name]

            # Удаляем точку из списка смежности
            if point_name in self.adjacency_list:
                del self.adjacency_list[point_name]

            # Удаляем точку из списка точек
            del self.points[point_name]

            # Удаляем отображение точки на холсте
            for draggable_point in self.draggable_points:
                if draggable_point.point_name == point_name:
                    self.canvas.delete(draggable_point.oval)
                    self.canvas.delete(draggable_point.text)
                    self.draggable_points.remove(draggable_point)
                    break  # выходим из цикла после удаления точки

            # Обновляем отображение связей на холсте
            self.update_edges()

    def get_connected_points(self, point_name):
        return self.adjacency_list[point_name]

    def enable_add_mode(self):
        self.add_mode = True
        self.delete_mode = False
        self.edit_mode = False
        self.link_mode = False  # Добавьте новый атрибут для режима связи
        self.mode_label.config(text="Режим добавления", bg="lightgreen")
        # Устанавливаем временный обработчик событий
        self.canvas.bind("<Button-1>", self.place_point)

    def toggle_add_mode(self):
        if self.add_mode:
            self.add_mode = False
            self.mode_label.config(text="", bg="lightgray")
            self.canvas.unbind("<Button-1>")  # Удаление временного обработчика
        else:
            self.enable_add_mode()

    def enable_delete_mode(self):
        self.add_mode = False
        self.delete_mode = True
        self.edit_mode = False
        self.link_mode = False  # Выключите режим связи при включении режима удаления
        self.mode_label.config(text="Режим удаления", bg="tomato")
        # Устанавливаем временный обработчик событий
        self.canvas.bind("<Button-1>", self.delete_point_on_click)

    def enable_connect_mode(self):
        self.add_mode = False
        self.delete_mode = False
        self.edit_mode = False
        self.link_mode = True
        self.mode_label.config(text="Режим связи", bg="lightblue")
        # Устанавливаем временный обработчик событий
        self.canvas.bind("<Button-1>", self.connect_points)

    def delete_point_on_click(self, event):
        # Если мы в режиме удаления и нажатие произошло на точке
        if self.delete_mode:
            item = self.canvas.find_closest(event.x, event.y)
            tags = self.canvas.gettags(item)
            if "draggable" in tags:
                point_name = tags[1]  # Имя точки
                self.delete_point_by_name(point_name)

    def connect_points(self, event):
        if self.link_mode:
            item = self.canvas.find_closest(event.x, event.y)
            tags = self.canvas.gettags(item)
            if "draggable" in tags:
                point_name = tags[1]  # Имя точки
                if hasattr(self, "first_connected_point"):
                    second_point_name = self.first_connected_point
                    if point_name != second_point_name:
                        # Соединяем точки только если связи еще нет
                        edge = (point_name, second_point_name) if (point_name, second_point_name) not in self.edges and (second_point_name, point_name) not in self.edges else None

                        if edge:
                            # Сохраняем информацию о связи в списке смежности
                            self.adjacency_list.setdefault(point_name, []).append(second_point_name)
                            self.adjacency_list.setdefault(second_point_name, []).append(point_name)

                            # Создаем линию на холсте
                            line_tag = f"line_{point_name}_{second_point_name}"
                            start_x = self.points[point_name]["x"]
                            start_y = self.points[point_name]["y"]
                            end_x = self.points[second_point_name]["x"]
                            end_y = self.points[second_point_name]["y"]
                            self.canvas.create_line(start_x, start_y, end_x, end_y, tags=("line", line_tag), fill="blue")

                            # Добавляем связь в список рёбер
                            self.edges.append(edge)

                        delattr(self, "first_connected_point")

                        # Выводим список смежности в консоль
                        print("Список смежности:")
                        for point, connected_points in self.adjacency_list.items():
                            print(f"{point}: {connected_points}")
                    else:
                        print("Точки совпадают.")
                else:
                    # Если еще нет выбранной точки, сохраняем текущую
                    setattr(self, "first_connected_point", point_name)

    def disable_delete_mode(self):
        self.delete_mode = False
        self.canvas.unbind("<Button-1>")  # Удаление временного обработчика

    def enable_edit_mode(self):
        self.add_mode = False
        self.delete_mode = False
        self.edit_mode = True
        self.link_mode = False  # Выключаем режим связи
        self.mode_label.config(text="Режим редактирования", bg="lightblue", )

        # Включение/выключение редактирования для всех точек
        for draggable_point in self.draggable_points:
            draggable_point.is_dragging = not draggable_point.is_dragging

    def toggle_link_mode(self):
        if self.link_mode:
            self.link_mode = False
            self.mode_label.config(text="", bg="lightgray")
            # Устанавливаем временный обработчик событий для режима редактирования
            self.canvas.bind("<Button-1>", self.edit_point)
        else:
            self.link_mode = True
            self.mode_label.config(text="Режим связи", bg="yellow")
            # Убираем временный обработчик событий для режима редактирования
            self.canvas.unbind("<Button-1>")
            # Устанавливаем временный обработчик событий
            self.canvas.bind("<Button-1>", self.connect_points)

    def show_temporary_text(self, text):
        # Отображение текста на секунду
        self.mode_label.config(text=text, bg="lightgray")
        self.master.after(1000, lambda: self.mode_label.config(text="", bg="lightgray"))  # Скрытие текста после 1 секунды

    def edit_point(self, event):
        if self.edit_mode:
            item = self.canvas.find_closest(event.x, event.y)
            tags = self.canvas.gettags(item)
            if "draggable" in tags:
                point_name = tags[1]  # Имя точки
                self.show_temporary_text(f"Редактирование точки {point_name}")
                # Включение редактирования для выбранной точки
                for draggable_point in self.draggable_points:
                    if draggable_point.point_name == point_name:
                        draggable_point.is_draggable = not draggable_point.is_draggable

    def update_edges_coordinates(self):
        # Обновляем координаты связей
        for edge in self.edges:
            start_x = self.points[edge[0]]["x"]
            start_y = self.points[edge[0]]["y"]
            end_x = self.points[edge[1]]["x"]
            end_y = self.points[edge[1]]["y"]

            # Обновляем координаты линии на холсте
            line_tag_forward = f"line_{edge[0]}_{edge[1]}"
            line_tag_reverse = f"line_{edge[1]}_{edge[0]}"
            self.canvas.coords(line_tag_forward, start_x, start_y, end_x, end_y)
            self.canvas.coords(line_tag_reverse, end_x, end_y, start_x, start_y)


if __name__ == "__main__":
    root = tk.Tk()
    app = PointFieldApp(root)
    root.mainloop()
