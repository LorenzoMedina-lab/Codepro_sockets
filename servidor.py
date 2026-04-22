import socket # Interfaz de Python para la API de sockets de C del sistema operativo.
import select # Acceso a la llamada al sistema (syscall) select() para multiplexación de I/O.

# 0.0.0.0 indica al kernel que el socket debe escuchar en todas las interfaces de red disponibles (localhost, Wi-Fi, Ethernet).
IP = "0.0.0.0" 
PUERTO = 5000 #Puerto de escucha

# AF_INET especifica la familia de direcciones IPv4. SOCK_STREAM especifica el protocolo TCP (orientado a conexión y flujo de bytes).(UDP sería SOCK_DGRAM)
servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# SOL_SOCKET y SO_REUSEADDR manipulan las opciones del socket a nivel del Sistema Operativo. 
# SO_REUSEADDR permite que el servidor se reinicie rápidamente sin esperar a que el SO libere el puerto 
servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) #Time and wait para reutilizar el puerto después de cerrar el servidor.

# Bind asocia el file descriptor del socket con la IP y el puerto específicos.
servidor.bind((IP, PUERTO))

# Listen (5) listo para aceptar conexiones entrantes. El número 5 indica cuántas conexiones pendientes puede mantener.
servidor.listen(5) 

# Lista que almacena los FDs. El servidor mismo es un FD que "lee" nuevas conexiones.
lista_sockets = [servidor]  # El servidor es el primer elemento de la lista, porque queremos monitorear su actividad para aceptar nuevos clientes.

print(f"Chat en linea. Escuchando en {IP}:{PUERTO}")

# Bucle infinito del servidor: el corazón del I/O Multiplexing.
while True:
    # select() bloquea el hilo hasta que al menos un FD de 'lista_sockets' esté listo para lectura.
    # Devuelve tres listas: legibles, escribibles (ignorada aquí con '_'), y con errores.
    read_sockets, _, exception_sockets = select.select(lista_sockets, [], lista_sockets) #Socket de escucha.

    # Se itera solo sobre los descriptores que el Sistema avisó que tienen actividad.
    for notified_socket in read_sockets:
        
        # Si el socket con actividad es el socket del servidor, significa que hay un nuevo cliente intentando el 3-way handshake de TCP.
        if notified_socket == servidor: # Si el socket activo es el servidor, no es un mensaje es una nueva conexión entrando.
            # accept() crea un NUEVO socket dedicado exclusivamente a hablar con este cliente específico.
            client_socket, client_address = servidor.accept()
            lista_sockets.append(client_socket) # Agregamos el nuevo FD a la lista de monitoreo.
            print(f"Nueva conexión detectada desde: {client_address}")
        
        # Si el socket activo no es el servidor, es un cliente existente enviando datos.
        else:
            try:
                # recv() lee hasta 2048 bytes del buffer de red del SO.
                message = notified_socket.recv(2048)
                
                # En la API de sockets, si recv() devuelve 0 bytes (un string vacío), 
                # significa que el cliente cerró la conexión (envió un paquete TCP FIN).
                if not message:
                    print(f" Cliente desconectado limpiamente.")
                    lista_sockets.remove(notified_socket) # Lo sacamos del select loop.
                    notified_socket.close() # Liberamos el FD en el sistema operativo.
                    continue

                # Broadcast: iteramos sobre todos los FDs conocidos.
                for client in lista_sockets:
                    # Filtramos para no hacer echo al emisor, ni enviar datos al socket pasivo del servidor.
                    if client != servidor and client != notified_socket:
                        try:
                            client.send(message) # Empujamos los bytes crudos al cliente destino.
                        except Exception:
                            # Si el send() falla (ej. Broken Pipe), asumimos que el cliente murió abruptamente.
                            lista_sockets.remove(client)
                            client.close()

            # Captura excepciones como ConnectionResetError si el cliente cerró la terminal a la fuerza (sin TCP FIN).
            except Exception as e:
                print(f"💥 Error en la conexión: {e}")
                lista_sockets.remove(notified_socket)
                notified_socket.close()