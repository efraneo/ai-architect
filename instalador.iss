; =========================================================
;  Instalador del Arquitecto
;
;  Se compila con Inno Setup (gratis, jrsoftware.org/isinfo.php):
;
;      1. pyinstaller arquitecto.spec
;      2. ISCC.exe instalador.iss
;
;  Sale `salida/ArquitectoSetup.exe`: un archivo que se le pasa a
;  cualquiera, hace doble clic y tiene el arquitecto con su icono en el
;  escritorio. Sin Python, sin terminal y sin pip.
;
;  **Se instala para el usuario, no para la maquina.** `PrivilegesRequired
;  = lowest` evita el aviso de administrador de Windows, que es donde se
;  cae la mitad de la gente. El arquitecto solo escribe en la carpeta del
;  usuario, asi que no necesita mas.
;
;  Lo que este archivo NO hace, y conviene saberlo: firmar. Sin firma
;  digital, Windows SmartScreen avisa de "editor desconocido" la primera
;  vez. Se quita con un certificado de firma de codigo, que cuesta dinero
;  y va a nombre de una empresa. Es un tramite, no un problema tecnico.
; =========================================================

#define Nombre     "Arquitecto"
#define Version    "0.1.0"
#define Autor      "Xentris Tech"
#define Ejecutable "arquitecto.exe"

[Setup]
AppId={{8F3A1C42-9B77-4E51-A0D3-7C6E2B914D58}
AppName={#Nombre}
AppVersion={#Version}
AppPublisher={#Autor}
DefaultDirName={autopf}\{#Nombre}
DefaultGroupName={#Nombre}
DisableProgramGroupPage=yes
OutputDir=salida
OutputBaseFilename=ArquitectoSetup
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern

; Sin permisos de administrador: es donde se cae la mitad de la gente, y
; el arquitecto no los necesita para nada.
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

[Languages]
Name: "es"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "escritorio"; Description: "Crear un acceso directo en el escritorio"; GroupDescription: "Accesos directos:"

; Que las tareas programadas funcionen con el programa cerrado. Va sin
; marcar: registrar algo en el Programador de tareas es un cambio que
; sobrevive al programa, y eso se pregunta, no se hace de tapadillo.
Name: "tareas"; Description: "Dejar que revise repositorios solo, aunque este cerrado"; GroupDescription: "Opcional:"; Flags: unchecked

[Files]
Source: "dist_tmp\arquitecto\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#Nombre}"; Filename: "{app}\{#Ejecutable}"; Parameters: "conversar"
Name: "{autodesktop}\{#Nombre}"; Filename: "{app}\{#Ejecutable}"; Parameters: "conversar"; Tasks: escritorio

[Run]
; El primer arranque pide la clave y explica que hace falta. Sin esto, la
; primera vez que alguien lo abra vera una cara que no puede pensar y no
; sabra por que.
Filename: "{app}\{#Ejecutable}"; Parameters: "configurar"; Description: "Configurar la clave ahora"; Flags: postinstall shellexec

Filename: "{app}\{#Ejecutable}"; Parameters: "tareas . --registrar"; Tasks: tareas; Flags: runhidden

[UninstallRun]
; Al desinstalar se quita tambien del Programador de tareas. Una tarea
; huerfana que intenta arrancar un programa que ya no existe es basura que
; queda dando errores en el visor de sucesos para siempre.
Filename: "{app}\{#Ejecutable}"; Parameters: "tareas --desregistrar"; Flags: runhidden; RunOnceId: "quitartareas"

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
