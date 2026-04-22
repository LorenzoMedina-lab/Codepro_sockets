import socket
import threading # Necesario porque el select() de Windows no soporta sys.stdin (teclado). Usamos hilos para concurrencia.
import sys       # Para manipular directamente los flujos de entrada/salida estándar (stdin/stdout).
import time      # Necesario para las pausas en los intentos de reconexión.

IP = "127.0.0.1" # Interfaz de loopback (localhost). El cliente busca al servidor en su propia máquina.
PUERTO = 5000 #Puerto de envio 
apagando = False # Bandera global indica si el programa se está cerrando a propósito para evitar reconexiones innecesarias.

# Creamos el descriptor de archivo del cliente (IPv4, TCP).
cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try: # la palabra clave 'try' es para manejar excepciones que puedan surgir al intentar conectar, como si el servidor no está corriendo.
    # Inicia el 3-way handshake de TCP con el servidor. Bloquea hasta que se establece la conexión.
    cliente.connect((IP, PUERTO))
    print("🔗 Conectado al servidor. Escribí un mensaje y presioná Enter.")
except Exception as e:
    # Falla si el servidor no está corriendo (ConnectionRefusedError).
    print(f"Error fatal al conectar: {e}")
    sys.exit()

# Definimos la rutina de supervivencia para reconectar si el servidor cae.
def reconectar():
    global cliente # Modificamos el descriptor de archivo global
    while True:
        if apagando: # Si se esta cerrando con el comando /exit se cancela la reconexión.
            return
            
        print("\n🔄 Intentando reconectar en 3 segundos...")
        time.sleep(3)
        try:
            # Creamos un NUEVO descriptor de archivo porque el anterior está muerto
            cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Intentamos el 3-way handshake de TCP de nuevo
            cliente.connect((IP, PUERTO))
            
            sys.stdout.write("\n🔗 ¡Reconexión exitosa! Podés volver a escribir.\n> ")
            sys.stdout.flush()
            return # Salimos del bucle para volver a la normalidad
        except Exception:
            pass # Si falla, el bucle repite el sleep

# Definimos la rutina que ejecutará el hilo secundario: su único trabajo es leer el socket.
def recibir_mensajes():
    global cliente, apagando # Modifica el descriptor y lee la bandera de estado global
    while True: # Bucle infinito de escucha.
        try:
            # Bloquea hasta que lleguen bytes desde la red. decode() transforma los bytes crudos a un string Unicode (UTF-8).
            mensaje = cliente.recv(2048).decode('utf-8')
            
            if mensaje:
                # El \r (carriage return) mueve el cursor al inicio de la línea en la terminal.
                # Esto sobreescribe visualmente la línea actual para que los mensajes entrantes 
                # no rompan lo que el usuario esté escribiendo en ese momento.
                sys.stdout.write(f"\r[Alguien dice]: {mensaje}\n> ")
                sys.stdout.flush() # Fuerza al SO a imprimir el buffer de stdout inmediatamente.
            else:
                # recv() de 0 bytes = servidor apagado o conexión cerrada.
                if apagando: 
                    break # Si se esta cerrando con el comando /exit.
                print("\n🛑 El servidor ha cerrado la conexión limpiamente.")
                cliente.close()
                reconectar() # Disparamos la reconexión en lugar de matar el hilo
                
        except Exception: # Captura cualquier excepción de red, como si el servidor se cayó abruptamente (ConnectionResetError).
            if apagando: 
                break # Si el usuario escribió /exit, morimos en silencio.
            print("\n🛑 Error de red. Desconectado.")
            cliente.close()
            reconectar() # Disparamos la reconexión en lugar de matar el hilo

# Instanciamos el hilo pasándole la función objetivo. Un hilo es una linea de ejecucion independiente dentro del mismo proceso.
receive_thread = threading.Thread(target=recibir_mensajes)
# Si el hilo principal (el que lee el teclado) termina, este hilo muere automáticamente con él. No queda colgado.
receive_thread.daemon = True # Esto es importante para que el programa pueda cerrarse limpiamente. 
receive_thread.start() # Le pide al SO que comience a ejecutar el hilo.

# Hilo principal: se encarga exclusivamente de I/O de usuario (teclado a red).
while True:
    try:
        # Mostramos el prompt básico para indicar que esperamos entrada.
        sys.stdout.write("> ")
        sys.stdout.flush()
        
        # input() bloquea este hilo principal hasta que el usuario presione Enter.
        mensaje = input() 
        
        # Comando para terminar el proceso de forma limpia.
        if mensaje.lower() == '/exit':
            apagando = True # Se levanta la bandera para que los hilos sepan que se está cerrando a propósito y no intenten reconectar.
            try:
                # shutdown() apaga el flujo de red (Envía TCP FIN al servidor) antes de destruir el socket
                cliente.shutdown(socket.SHUT_RDWR) # SHUT_RDWR indica que no se enviarán ni recibirán más datos.
            except Exception:
                pass 
            cliente.close() # Destruimos el file descriptor localmente.
            sys.exit()     # Mata el proceso local.
            
        if mensaje:
            # Envolvemos el envío por si el hilo secundario está en medio de una reconexión
            try:
                # encode() traduce el string de Python a bytes usando el estándar UTF-8. 
                # Los sockets solo entienden secuencias de bytes.
                cliente.send(mensaje.encode('utf-8'))
            except OSError:
                print("\n⚠️ El socket no está listo. Esperando reconexión...")
            
    except KeyboardInterrupt:
        # Maneja la señal SIGINT (cuando presionás Ctrl+C en la terminal) para no dejar sockets colgados.
        apagando = True # 🚩 LEVANTAMOS LA BANDERA
        try:
            cliente.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass
        cliente.close()
        sys.exit()