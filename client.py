import socket
import shelve
import dbm
import struct

import argparse

BUFFER_SIZE = 512
DB_NAME = 'files.db'


def parse_input_str(string):
    """Разбивает строку по состовляющие"""

    # get /home/user/something
    # cp /home/user/something /local/path/to/something

    method, *paths = string.split()

    if any([all([method == 'get', len(paths) == 1]),
            all([method == 'cp', len(paths) == 2])]):
        return (method, *paths)

    return None


def recv_file(the_socket):
    """Принимает данные из сокета
    Получает размер передаваемых данных и принимает
    их до тех пор, пока не получит все данные"""

    total_data = bytearray()

    sock_data = the_socket.recv(BUFFER_SIZE)
    # данные о размере файла занимают 4 байта
    size = struct.unpack('>i', sock_data[:4])[0]
    total_data += sock_data[4:]
    total_len = len(sock_data[4:])

    while total_len < size:
        sock_data = the_socket.recv(BUFFER_SIZE)
        total_data += sock_data
        total_len += len(sock_data)

    return total_data


def get_from_server(conn, path):
    """Отправляет запрос на сервер для получения указанного файла.
    Возвращает текстовое содержание ошибки или бинарные данные файла
    Проверяет на наличие файла в базе, в случае если с вервера пришла ошибка"""

    conn.send(path.encode('utf-8'))

    data = sock.recv(BUFFER_SIZE)
    status, mes = data.split(b':', 1)
    print(mes.decode('utf-8'))

    if status.decode('utf-8') == 'ok':
        return recv_file(sock)
    else:
        if is_file_in_db(path):
            print('Старая версия файла есть в базе')
        return None


def write_to_disc(binary_data, save_path):
    """Сохраняет файл на жесткий диск"""

    try:
        with open(save_path, 'wb') as out_file:
            out_file.write(binary_data)
        print('Файл успешно сохранен на диск')
    except OSError:
        print('Не могу сохранить файл по указанному пути')


# DB methods

def save_to_db(key, value):
    """Сохранение файла в базу, использован модуль shelve"""

    db = shelve.open(DB_NAME)
    try:
        db[key] = value
    except dbm.error:
        print('Ошибка записи в базу данных')
        return None

    db.close()
    print('Файл успешно сохранен в базу')


def is_file_in_db(key):
    """Проверка на наличие файла в базе, использован модуль shelve"""

    db = shelve.open(DB_NAME)
    res = key in db
    db.close()
    return res


def get_from_db(key):
    """Получение файла из базы, использован модуль shelve"""

    db = shelve.open(DB_NAME)
    try:
        return db[key]
    except KeyError:
        print('Нет такого файла в базе данных')
        return None
    finally:
        db.close()


#  Функции для команд

def get_command(conn, path_to_file):
    f = get_from_server(conn, path_to_file)

    if f is not None:
        save_to_db(path_to_file, f)

    return f


def cp_command(conn, path_to_file, save_path):
    f = get_from_db(parse_res[1])

    if f is None:
        print('Пробуем скачать файл с сервера...')
        f = get_command(conn, path_to_file)

        if f is None:
            return

    write_to_disc(f, save_path)


if __name__ == '__main__':

    # Ввод HOST & PORT через sys.args
    parser = argparse.ArgumentParser()
    parser.add_argument('host', help='Укажите адрес удаленного хоста')
    parser.add_argument('port', help='Укажите порт удаленного хоста')

    host = parser.parse_args().host
    port = int(parser.parse_args().port)

    # main
    with socket.socket() as sock:
        print('Соединение...')
        try:
            sock.connect((host, port))
            print('Подключено')
            print('Ctrl-C чтобы выйти')
        except ConnectionRefusedError as ex:
            print(f'Ошибка подключения: {ex}')
            exit(1)

        while True:
            try:
                command = input('> ')

                parse_res = parse_input_str(command)

                if parse_res is None:
                    print('Неверный запрос')
                    continue

                elif parse_res[0] == 'get':
                    get_command(sock, parse_res[1])

                elif parse_res[0] == 'cp':
                    cp_command(sock, parse_res[1], parse_res[-1])

            except KeyboardInterrupt:
                print('\nВыключение')
                break
