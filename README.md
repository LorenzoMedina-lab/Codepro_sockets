# Codepro_sockets
Implementación de sockets
# Proyecto: Reconstrucción del Protocolo (Challenge 2)

Tecnología: Python (Standard Library)
Arquitectura: Cliente-Servidor (TCP/IPv4) con I/O Multiplexing y Multithreading.

Una aplicación de chat en tiempo real por terminal construida desde cero utilizando exclusivamente la API de Sockets subyacente del sistema operativo, sin frameworks ni dependencias externas.

---

### 1. ¿Quién sos después de este reto?
Después de este reto, soy un desarrollador que entiende la infraestructura de red a nivel del sistema operativo. Dejé de depender de abstracciones mágicas para entender cómo fluyen los bytes a través de los descriptores de archivo (File Descriptors). Aprendí a coordinar el flujo asíncrono de datos y a gestionar la concurrencia a bajo nivel, pasando de ser un simple consumidor de APIs a un constructor de protocolos.

### 2. ¿Cómo sobrevivió tu aplicación?
La aplicación sobrevive al caos de múltiples conexiones simultáneas gracias a dos decisiones arquitectónicas clave:
* En el Servidor (I/O Multiplexing): En lugar de crear un hilo pesado por cada usuario que se conecta (lo que saturaría la CPU), utilizo la llamada al sistema `select()`. Esto permite que el kernel del sistema operativo me notifique exactamente qué socket tiene datos listos para leer, manejando decenas de clientes en un solo ciclo de ejecución (Single-threaded).
* En el Cliente (Multithreading): Implementé un hilo demonio (daemon thread) dedicado exclusivamente a escuchar la red. Esto permite al usuario escribir comandos en la terminal (`stdin`) de forma bloqueante, mientras el hilo secundario recibe e imprime los mensajes entrantes (`stdout`) sin interrumpir la experiencia.

### 3. ¿Qué aprendiste cuando todo se rompió?
Aprendí que en el mundo de las redes, la confianza es una ilusión y los errores son la regla, no la excepción:
* Reseteo de conexiones: Comprendí que un cliente puede desaparecer abruptamente sin enviar un paquete TCP de cierre (FIN). 
* Manejo de Excepciones: La aplicación está blindada con bloques `try-except` estratégicos. Si una lectura (`recv()`) o un envío (`send()`) falla, el servidor asume que el socket está muerto, lo elimina de su lista de descriptores activos (`sockets_list.remove()`) y continúa dando servicio al resto de los clientes sin colapsar.
* Flujos Vacíos: Aprendí que si `recv()` devuelve 0 bytes, es el indicador a nivel de sistema de que el host remoto cerró la conexión ordenadamente.

### Instrucciones de Ejecución
1. Levantar el host: `python servidor.py` (Se quedará escuchando en el puerto designado).
2. Levantar uno o más clientes en terminales separadas: `python cliente.py`.
3. Para salir limpiamente del chat, escribir `/exit` o presionar `Ctrl+C`.