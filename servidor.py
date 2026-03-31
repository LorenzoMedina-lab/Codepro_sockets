import socket # Interfaz de Python para la API de sockets de C del sistema operativo.
import select # Acceso a la llamada al sistema (syscall) select() para multiplexación de I/O.

# 0.0.0.0 indica al kernel que el socket debe escuchar en todas las interfaces de red disponibles (localhost, Wi-Fi, Ethernet).
IP = "0.0.0.0" 
PORT = 5000 # Puerto arbitrario no privilegiado (mayor a 1024).

# AF_INET especifica la familia de direcciones IPv4. SOCK_STREAM especifica el protocolo TCP (orientado a conexión y flujo de bytes).
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# SOL_SOCKET y SO_REUSEADDR manipulan las opciones del socket a nivel del SO. 
# Esto evita el error "Address already in use" permitiendo reutilizar el puerto si el socket anterior quedó en estado TIME_WAIT.
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# Asocia el file descriptor (FD) del socket con la IP y el puerto específicos.
server.bind((IP, PORT))

# Pasa el socket a modo pasivo. El '5' es el "backlog": el tamaño de la cola del kernel para conexiones entrantes no aceptadas aún.
server.listen(5) 

# Lista que almacena los FDs. El servidor mismo es un FD que "lee" nuevas conexiones.
sockets_list = [server]

print(f"📡 Base de operaciones en línea. Escuchando en {IP}:{PORT}...")

# Bucle infinito del servidor: el corazón del I/O Multiplexing.
while True:
    # select() bloquea el hilo hasta que al menos un FD de 'sockets_list' esté listo para lectura.
    # Devuelve tres listas: legibles, escribibles (ignorada aquí con '_'), y con errores.
    read_sockets, _, exception_sockets = select.select(sockets_list, [], sockets_list)

    # Iteramos solo sobre los descriptores que el SO nos avisó que tienen actividad.
    for notified_socket in read_sockets:
        
        # Si el socket con actividad es el socket del servidor, significa que hay un nuevo cliente intentando el 3-way handshake de TCP.
        if notified_socket == server:
            # accept() crea un NUEVO socket dedicado exclusivamente a hablar con este cliente específico.
            client_socket, client_address = server.accept()
            sockets_list.append(client_socket) # Agregamos el nuevo FD a la lista de monitoreo.
            print(f"🔌 Nueva conexión detectada desde: {client_address}")
        
        # Si el socket activo no es el servidor, es un cliente existente enviando datos.
        else:
            try:
                # recv() lee hasta 2048 bytes del buffer de red del SO.
                message = notified_socket.recv(2048)
                
                # En la API de sockets, si recv() devuelve 0 bytes (un string vacío), 
                # significa que el cliente cerró la conexión (envió un paquete TCP FIN).
                if not message:
                    print(f"⚠️ Cliente desconectado limpiamente.")
                    sockets_list.remove(notified_socket) # Lo sacamos del select loop.
                    notified_socket.close() # Liberamos el FD en el sistema operativo.
                    continue

                # Broadcast: iteramos sobre todos los FDs conocidos.
                for client in sockets_list:
                    # Filtramos para no hacer echo al emisor, ni enviar datos al socket pasivo del servidor.
                    if client != server and client != notified_socket:
                        try:
                            client.send(message) # Empujamos los bytes crudos al cliente destino.
                        except Exception:
                            # Si el send() falla (ej. Broken Pipe), asumimos que el cliente murió abruptamente.
                            sockets_list.remove(client)
                            client.close()

            # Captura excepciones como ConnectionResetError si el cliente cerró la terminal a la fuerza (sin TCP FIN).
            except Exception as e:
                print(f"💥 Error en la conexión: {e}")
                sockets_list.remove(notified_socket)
                notified_socket.close()