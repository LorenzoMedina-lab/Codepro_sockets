import socket
import threading # Necesario porque el select() de Windows no soporta sys.stdin (teclado). Usamos hilos para concurrencia.
import sys       # Para manipular directamente los flujos de entrada/salida estándar (stdin/stdout).

IP = "127.0.0.1" # Interfaz de loopback (localhost). El cliente busca al servidor en su propia máquina.
PORT = 5000

# Creamos el descriptor de archivo del cliente (IPv4, TCP).
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    # Inicia el 3-way handshake de TCP con el servidor. Bloquea hasta que se establece la conexión.
    client.connect((IP, PORT))
    print("🔗 Conectado al servidor. Escribí un mensaje y presioná Enter.")
except Exception as e:
    # Falla si el servidor no está corriendo (ConnectionRefusedError).
    print(f"💥 Error fatal al conectar: {e}")
    sys.exit()

# Definimos la rutina que ejecutará el hilo secundario: su único trabajo es leer el socket.
def receive_messages():
    while True: # Bucle infinito de escucha.
        try:
            # Bloquea hasta que lleguen bytes desde la red. decode() transforma los bytes crudos a un string Unicode (UTF-8).
            message = client.recv(2048).decode('utf-8')
            
            if message:
                # El \r (carriage return) mueve el cursor al inicio de la línea en la terminal.
                # Esto sobreescribe visualmente la línea actual para que los mensajes entrantes 
                # no rompan lo que el usuario esté escribiendo en ese momento.
                sys.stdout.write(f"\r[Alguien dice]: {message}\n> ")
                sys.stdout.flush() # Fuerza al SO a imprimir el buffer de stdout inmediatamente.
            else:
                # recv() de 0 bytes = servidor apagado o conexión cerrada.
                print("\n🛑 El servidor ha cerrado la conexión.")
                client.close()
                sys.exit() # Mata el hilo.
        except Exception:
            print("\n🛑 Error de red. Desconectado.")
            client.close()
            sys.exit()

# Instanciamos el hilo pasándole la función objetivo.
receive_thread = threading.Thread(target=receive_messages)
# Modo demonio: si el hilo principal (el que lee el teclado) termina, este hilo muere automáticamente con él. No queda colgado.
receive_thread.daemon = True 
receive_thread.start() # Le pide al SO que comience a ejecutar el hilo.

# Hilo principal: se encarga exclusivamente de I/O de usuario (teclado a red).
while True:
    try:
        # Mostramos el prompt básico para indicar que esperamos entrada.
        sys.stdout.write("> ")
        sys.stdout.flush()
        
        # input() bloquea este hilo principal hasta que el usuario presione Enter.
        message = input() 
        
        # Comando para terminar el proceso de forma limpia.
        if message.lower() == '/exit':
            client.close() # Envía el TCP FIN al servidor.
            sys.exit()     # Mata el proceso local.
            
        if message:
            # encode() traduce el string de Python a bytes usando el estándar UTF-8. 
            # Los sockets solo entienden secuencias de bytes.
            client.send(message.encode('utf-8'))
            
    except KeyboardInterrupt:
        # Maneja la señal SIGINT (cuando presionás Ctrl+C en la terminal) para no dejar sockets zombies.
        client.close()
        sys.exit()