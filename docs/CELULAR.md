# Mandar el celular con la voz

«Architect, llama a Juan». «Architect, pon Tití me preguntó». «Architect,
bloquea el celular». Architect no vive en el teléfono: **le manda la orden por
tu bot de Telegram** con una forma fija, y una automatización del teléfono la
lee de la notificación y la ejecuta. Sin servidores nuevos ni apps propias.

```
📱 LLAMAR|3001234567
📱 COLGAR|
📱 BLOQUEAR|
📱 MUSICA|Bad Bunny Tití me preguntó
📱 PAUSAR|      📱 REANUDAR|      📱 SIGUIENTE|      📱 ANTERIOR|
📱 VOLUMEN|40
📱 ABRIR|WhatsApp
📱 NAVEGAR|https://…
📱 SONAR|
📱 MENSAJE|3001234567|texto
```

## Lo que se puede y lo que no

| Orden | Android (Tasker) | iPhone |
|---|---|---|
| Llamar, colgar | sí (colgar: Android 9+ con accesibilidad) | solo con Siri en el propio teléfono |
| Bloquear la pantalla | sí | sí, pero solo desde un Atajo en el teléfono |
| **Desbloquear** | **no** | **no** |
| Música, pausar, siguiente, volumen | sí | solo desde un Atajo en el teléfono |
| Abrir app, abrir web, hacerlo sonar | sí | parcial |

Desbloquear no lo permite ningún sistema: sería un programa saltándose la
clave. Siri tampoco lo hace sin tu cara o tu huella. Todo lo demás en Android
funciona con Tasker (o Automate); en iPhone no hay forma de que un mensaje
remoto dispare un Atajo, así que las órdenes al iPhone se quedan en Siri.

## Configurar el Android (Tasker, una vez)

1. Instala **Tasker** y dale permisos de notificaciones, llamadas y
   accesibilidad (para «colgar» y «bloquear»).
2. Ten el bot de Architect en Telegram (`architect canales` te dice cómo) y
   activa las notificaciones de ese chat.
3. Crea un **Perfil → Evento → UI → Notificación**, propietario *Telegram*,
   texto `📱*`.
4. Su **Tarea**:
   - `Variable Set %orden To %evtprm2` (el texto de la notificación).
   - `Variable Search Replace %orden` para quitar `📱 `, y `Variable Split %orden` por `|`
     → `%orden1` es la acción, `%orden2` el argumento.
   - `If %orden1 ~ LLAMAR` → **Phone → Call** `%orden2`.
     Si llega un nombre en vez de un número, antes: **Contacts → Contact Via App**
     o un `Test Phone` para resolverlo.
   - `COLGAR` → **Phone → End Call**.
   - `BLOQUEAR` → **Display → System Lock**.
   - `MUSICA` → **App → Open URL** `spotify:search:%orden2` (o **Media Control →
     Play** con tu reproductor); `PAUSAR`/`REANUDAR`/`SIGUIENTE`/`ANTERIOR` →
     **Media Control**.
   - `VOLUMEN` → **Audio → Media Volume** `%orden2`.
   - `ABRIR` → **App → Launch App** `%orden2`.
   - `NAVEGAR` → **App → Open URL** `%orden2`.
   - `SONAR` → **Audio → Media Volume 100** + **Alert → Beep**.
   - `MENSAJE` → **Phone → Send SMS** (`%orden2` lleva `número|texto`: vuelve a
     partir por `|`).
5. Prueba desde el PC: `architect hacer "haz sonar mi celular" --si`, o de viva
   voz «Architect, ¿dónde está mi celular?».

## Contactos

«Architect, recuerda que el número de Juan es 300 123 4567» lo guarda en
`~/.ai_architect/contactos.json`. Después, «llama a Juan» manda el número; si
no lo conoce, manda el nombre y el teléfono busca en su agenda.

## Por voz, sin modelo

Estas órdenes se reconocen en el sitio (`ai_architect/canales/celular.py`,
`entender`) y salen al instante, sin pasar por el modelo: llamar y mandar SMS
piden un «sí» antes; lo demás va directo.

## Aprobar desde el celular

Cuando Architect deja un cambio esperando permiso, te llega a Telegram con
botones: **✅ Aprobar** / **❌ Rechazar** por cambio, y **Aprobar todo**.
También por texto: `/si <id>`, `/no <id>`, `/si todo`, `/pendientes`. Al
aprobar, se aplica y te contesta qué hizo; si la cara está abierta, se entera.

Las tareas largas (una auditoría, una corrección) ya no se abandonan a los
tres minutos: Architect dice «sigo con ello» y, al terminar, lo cuenta en voz
alta y por Telegram con el permiso que haga falta.
