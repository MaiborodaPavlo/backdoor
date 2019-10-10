import socket
import struct

HOST = ""
PORT = 5000
BUFFER_SIZE = 512


def get_file(path_to_file):
    """Пытается открыть файл в бинарном режиме
    В случае успеха - возвращается бинарное содержание файла;
    В случае ошибки - возвращается сообщение об ошибке"""

    try:
        with open(path_to_file, 'rb') as f:
            return f.read()

    except (FileNotFoundError, PermissionError, OSError) as err:
        return f'Проблемы с доступом к файлу: {err}'


def send_msg(soc, data):
    """Отправляется сообщение
    Файл, в случае, если к нему есть доступ
    В противном случае - отправляется сообщение об ошибке"""

    if type(data) == str:
        status = 'error'
        msg = data.encode('utf-8')
        soc.sendall(status.encode('utf-8') + b':' + msg)

    elif len(data).bit_length() > 31:
        status = 'error'
        msg = f'Слишком большой размер фала: {len(data)} Б'
        soc.sendall(status.encode('utf-8') + b':' + msg.encode('utf-8'))

    else:
        status = 'ok'
        msg = f'Отправляется файл размером: {len(data)} Б'
        soc.sendall(status.encode('utf-8') + b':' + msg.encode('utf-8'))

        soc.sendall(struct.pack('>i', len(data))+data)


with socket.socket() as sock:
    sock.bind((HOST, PORT))
    sock.listen()

    while True:
        conn, addr = sock.accept()
        with conn:
            while True:

                try:
                    data = conn.recv(BUFFER_SIZE)
                except ConnectionError:
                    break

                if not data:
                    break

                path = data.decode('utf-8')
                file = get_file(path)
                try:
                    send_msg(conn, file)
                except ConnectionError:
                    break
