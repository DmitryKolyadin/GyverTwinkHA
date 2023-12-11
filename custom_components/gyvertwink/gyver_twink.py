import socket
import time
from typing import Optional


class GyverTwink:
    """
    Класс для управления гирляндой GyverTwink через WiFi.

    Доступные методы:
        - `discover(net_ip: str, timeout: int = 2) -> List["GyverTwink"]`:
          Поиск гирлянд в указанной сети и возвращает список найденных гирлянд.

        - `set_leds(count: int) -> None`:
          Устанавливает количество светодиодов гирлянды.

        - `get_settings() -> Dict[str, Any]`:
          Получает настройки гирлянды и возвращает словарь с настройками.
            - leds: Количество светодиодов.
            - power: Состояние питания.
            - brightness: Яркость (от 0 до 255).
            - auto_change: Флаг автоматической смены режимов.
            - random_change: Флаг случайной смены режимов.
            - change_period: Период смены режимов (от 1 до 10).
            - timer_active: Флаг активности таймера выключения.
            - timer_value: Время до выключения (от 1 до 240 минут).

        - `set_power(_on: bool) -> None`:
          Устанавливает состояние питания гирлянды.

        - `on() -> None`:
          Включает гирлянду.

        - `off() -> None`:
          Выключает гирлянду.

        - `set_brightness(value: int) -> None`:
          Устанавливает яркость гирлянды.

        - `set_auto_change(_on: bool) -> None`:
          Устанавливает флаг автоматической смены режимов.

        - `set_random_change(_on: bool) -> None`:
          Устанавливает флаг случайной смены режимов.

        - `set_change_period(value: int) -> None`:
          Устанавливает период смены режимов.

        - `next_effect() -> None`:
          Переключается на следующий эффект.

        - `set_timer(_on: bool) -> None`:
          Устанавливает состояние таймера выключения.

        - `set_timer_value(value: int) -> None`:
          Устанавливает время до выключения.

        - `select_effect(number: int) -> Optional[dict]`:
          Выбирает эффект по его номеру и возвращает информацию о нём.
            - Параметры:
                - number: Номер выбранного эффекта.
            - Возвращает словарь с информацией о выбранном эффекте (favorite, scale, speed).

        - `set_favorite(_on: bool) -> None`:
          Устанавливает флаг избранного для текущего эффекта.

        - `set_scale(value: int) -> None`:
          Устанавливает масштаб текущего эффекта.

        - `set_speed(value: int) -> None`:
          Устанавливает скорость текущего эффекта.

    Атрибуты:
        - `twink_ip`: IP-адрес гирлянды.
        - `last_reqest_time`: Время последнего запроса к гирлянде.

    Примеры использования:
        ```python
        # Поиск гирлянд в сети
        twinks = GyverTwink.discover("192.168.0.255")
        twink = twinks[0]

        # ИЛИ

        # Создание объекта для управления гирляндой по IP-адресу
        twink = GyverTwink("192.168.0.100")

        # Включение гирлянды
        twink.on()

        # Установка яркости
        twink.set_brightness(150)

        # Получение текущих настроек гирлянды
        settings = twink.get_settings()
        print(settings)

        # Выключение гирлянды
        twink.off()
        ```

    """

    def __init__(self, twink_ip: str) -> None:
        """
        Создает объект GyverTwink для управления гирляндой по указанному IP-адресу.

        :param twink_ip: IP-адрес гирлянды.
        """

        self.twink_ip = twink_ip
        self.server_address = (twink_ip, 8888)
        self.settings_ = {}
        self.last_reqest_time = time.time()

    def sock(
        self,
        send_data: bytes,
        wait_answer: bool = False,
        timeout: int = 2,
        __bufsize: int = 30,
        retry: int = 1,
    ) -> Optional[bytes]:
        """
        Отправляет данные по UDP и получает ответные данные.

        :param send_data: Данные для отправки.
        :param wait_answer: Ожидать ли ответные данные.
        :param timeout: Таймаут ожидания ответа.
        :param __bufsize: Размер буфера для получения данных.
        :param retry: Количество попыток повторной отправки в случае таймаута.

        :return: Ответные данные (если ожидается) или None.
        """

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        try:
            _ = time.time() - self.last_reqest_time
            if _ < 0.5:
                time.sleep(_ + 0.2)

            sock.sendto(send_data, self.server_address)

            if wait_answer:
                # Получение данных
                sock.settimeout(timeout)
                try:
                    data, server = sock.recvfrom(__bufsize)
                except TimeoutError:
                    if retry > 0:
                        return self.sock(
                            send_data, wait_answer, timeout, __bufsize, retry - 1
                        )
                    else:
                        raise TimeoutError("Timeout")

                if not data.startswith(b"GT"):
                    return None

                return data[2:]

        finally:
            self.last_reqest_time = time.time()

            sock.close()

    @classmethod
    def discover(cls, net_ip, timeout=2) -> list["GyverTwink"]:
        """
        Поиск гирлянд в сети.

        :param ip: IP-адрес cети для поиска гирлянд.
        :param timeout: Таймаут ожидания ответа. (по умолчанию 2 секунды)

        :return: Список найденных гирлянд.

        """

        server_address = (net_ip, 8888)

        request_data = bytes([ord("G"), ord("T"), 0])

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        try:
            sock.settimeout(timeout)
            sock.sendto(request_data, server_address)

            twinks = []

            while True:
                try:
                    # Получение данных
                    data, server = sock.recvfrom(30)

                    if data.startswith(b"GT"):
                        ip_octet = data[-1]

                        ip_ = net_ip.split(".")
                        ip_[3] = str(ip_octet)
                        twinks.append(cls(".".join(ip_)))

                except socket.timeout:
                    break

            return twinks

        finally:
            sock.close()

    def set_leds(self, count: int) -> None:
        """
        Устанавливает количество светодиодов гирлянды.

        :param count: Количество светодиодов.

        """
        # {2, 0, am1, am2} - отправить кол-во ледов (am1 = колво_led/100, am2 = колво_led%100)

        request_data = bytes([ord("G"), ord("T"), 2, 0, count // 100, count % 100])

        self.sock(request_data)

    def get_settings(self):
        """
        Получает настройки гирлянды.

        :return: Словарь с настройками гирлянды.
            - leds: Количество светодиодов.
            - power: Состояние питания.
            - brightness: Яркость (от 0 до 255).
            - auto_change: Флаг автоматической смены режимов.
            - random_change: Флаг случайной смены режимов.
            - change_period: Период смены режимов (от 1 до 10).
            - timer_active: Флаг активности таймера выключения.
            - timer_value: Время до выключения (от 1 до 240 минут).

        """
        # {колво_led/100, колво_led%100, питание, яркость, автосмена, случайная_смена, период, таймер активен, время таймера}
        request_data = bytes([ord("G"), ord("T"), 1])

        data = self.sock(request_data, wait_answer=True)

        if not data:
            return None
        else:
            data = data[1:]

            settings = {
                "leds": data[0] * 100 + data[1],
                "power": True if data[2] else False,
                "brightness": data[3],
                "auto_change": True if data[4] else False,
                "random_change": True if data[5] else False,
                "change_period": data[6],
                "timer_active": True if data[7] else False,
                "timer_value": data[8],
            }

            self.settings_ = settings

            return settings

    @property
    def settings(self):
        return self.settings_ or self.get_settings()

    def set_power(self, _on: bool) -> None:
        """
        Устанавливает состояние питания гирлянды.

        :param _on: Флаг включения/выключения питания.
        """
        # {2, 1, val} - отправить состояние питания
        value = 1 if _on else 0

        request_data = bytes([ord("G"), ord("T"), 2, 1, value])

        self.sock(request_data)

    def on(self):  # noqa
        """Включает гирлянду."""
        self.set_power(1)

    def off(self):
        """Выключает гирлянду."""
        self.set_power(0)

    def set_brightness(self, value: int) -> None:
        """
        Устанавливает яркость гирлянды.

        :param value: Яркость (от 0 до 255).
        """
        # {2, 2, val} - отправить яркость
        value = max(0, min(255, value))

        request_data = bytes([ord("G"), ord("T"), 2, 2, value])

        self.sock(request_data)

    def set_auto_change(self, _on: bool) -> None:
        """
        Устанавливает флаг автоматической смены режимов.

        :param _on: Флаг включения/выключения автоматической смены режимов.
        """
        # {2, 3, val} - отправить флаг авто смены режимов
        value = 1 if _on else 0

        request_data = bytes([ord("G"), ord("T"), 2, 3, value])

        self.sock(request_data)

    def set_random_change(self, _on: bool) -> None:
        """
        Устанавливает флаг случайной смены режимов.

        :param _on: Флаг включения/выключения случайной смены режимов.
        """
        # {2, 4, val} - отправить флаг случайной смены режимов
        value = 1 if _on else 0

        request_data = bytes([ord("G"), ord("T"), 2, 4, value])

        self.sock(request_data)

    def set_change_period(self, value: int) -> None:
        """
        Устанавливает период смены режимов.

        :param value: Период смены режимов (от 1 до 10).
        """
        # {2, 5, val} - отправить период смены режимов
        value = max(1, min(10, value))

        request_data = bytes([ord("G"), ord("T"), 2, 5, value])

        self.sock(request_data)

    def next_effect(self):
        """
        Переключается на следующий эффект.
        """
        # {2, 6} - следующий эффект

        request_data = bytes([ord("G"), ord("T"), 2, 6])

        self.sock(request_data)

    def set_timer(self, _on: bool) -> None:
        """
        Устанавливает состояние таймера выключения.

        :param _on: Флаг включения/выключения таймера.
        """
        # {2, 7} - отправить состояние таймера выключения
        value = 1 if _on else 0

        request_data = bytes([ord("G"), ord("T"), 2, 7, value])

        self.sock(request_data)

    def set_timer_value(self, value: int) -> None:
        """
        Устанавливает время до выключения.

        :param value: Время до выключения (от 1 до 240 минут).
        """
        # {2, 8, val} - отправить время до выключения
        value = max(1, min(240, value))

        request_data = bytes([ord("G"), ord("T"), 2, 8, value])

        self.sock(request_data)

    def select_effect(self, number: int) -> Optional[dict]:
        """
        Выбирает эффект по его номеру и возвращает информацию о нём.

        :param number: Номер выбранного эффекта.

        :return: Информация о выбранном эффекте (favorite, scale, speed)
        """
        # {4, 0, n} - выбрать эффект под номером n

        request_data = bytes([ord("G"), ord("T"), 4, 0, number])

        data = self.sock(request_data, wait_answer=True)

        if not data:
            return None
        else:
            data = data[1:]

            effect = {
                "favorite": True if data[0] else False,
                "scale": data[1],
                "speed": data[2],
            }

            return effect

    def set_favorite(self, _on: bool) -> None:
        """
        Устанавливает флаг избранного для текущего эффекта.

        :param _on: Включить (True) или выключить (False) флаг избранного.
        """
        # {4, 1, val} - установить флаг избранного val
        value = 1 if _on else 0

        request_data = bytes([ord("G"), ord("T"), 4, 1, value])

        self.sock(request_data)

    def set_scale(self, value: int) -> None:
        """
        Устанавливает масштаб текущего эффекта.

        :param value: Масштаб эффекта (1-255).
        """
        # {4, 2, val} - установить масштаб val
        value = max(1, min(255, value))

        request_data = bytes([ord("G"), ord("T"), 4, 2, value])

        self.sock(request_data)

    def set_speed(self, value: int) -> None:
        """
        Устанавливает скорость текущего эффекта.

        :param value: Скорость эффекта (1-255).
        """
        # {4, 3, val} - установить скорость val
        value = max(1, min(255, value))

        request_data = bytes([ord("G"), ord("T"), 4, 3, value])

        self.sock(request_data)

    def __repr__(self):
        return f"GyverTwink({self.twink_ip})"


if __name__ == "__main__":
    net_ip = input("Введите ip адрес сети. Например 192.168.0.255\n")

    twinks = GyverTwink.discover(net_ip)

    print("Найденные гирлянды:")
    for twink in twinks:
        print(twink)
