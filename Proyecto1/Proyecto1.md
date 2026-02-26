# Despliegue de Servidor Híbrido con Azure Arc y Kubernetes

Lo primero que tendremos que hacer antes de empezar con esto sería plantear un esquema para que nos quede más claro todo esto. En mi caso no es algo muy complejo, pero no viene mal para que quede más claro todo. Ya con esto y sabiendo la máquina y cosas de Azure que usaremos, podremos seguir adelante.

<img width="885" height="547" alt="Diagrama Proyecto 1" src="https://github.com/user-attachments/assets/b14f3326-b0e6-4b3b-8b63-470c6b963294" />

---

## Índice (por si quieres ir directo)
- [Fase 1: Preparación del Servidor con Ansible](#fase-1-preparación-del-servidor-con-ansible)
- [Fase 2: Integración con Azure Arc](#fase-2-integración-con-azure-arc)
- [Fase 3: Kubernetes](#fase-3-kubernetes)
- [Fase 4: Seguridad Zero-Trust (Sentinel)](#fase-4-seguridad-zero-trust-sentinel)
- [Fase 5: Final](#fase-5-final)

---

## Fase 1: Preparación del Servidor con Ansible

En primer lugar, voy a desplegar un playbook de Ansible para instalar varias cosas que no vienen nada mal a nuestro Ubuntu. Es algo simple pero sirve para poder repasar estos comandos y así ahorrarnos tiempo haciendo esas instalaciones y configurando el Fail2Ban.

El despliegue lo puedes hacer de dos maneras:

- Instalando en la propia VM Ansible y ejecutando el archivo.
- O si tienes WSL (Windows Subsystem for Linux) instalado en tu PC principal, instalas ahí Ansible y lo ejecutas ahí, por si quieres hacerlo más realista.

### 1. Instalación y Configuración

- **Instalación de Ansible en Ubuntu:**
```bash
sudo apt update && sudo apt install ansible
```
<img width="695" height="58" alt="image" src="https://github.com/user-attachments/assets/4a52a4ca-c37d-439c-b2bb-83cbdf82a697" />

- **Creación del archivo de inventario:** creación del archivo de servidores que tendrá Ansible.

<img width="502" height="75" alt="image" src="https://github.com/user-attachments/assets/f6ac5ac9-42d1-4dee-8db4-e92a61fff861" />

- El contenido del archivo en el que tendremos los servidores: simplemente pondremos la IP de nuestro servidor y le diremos que el usuario que tenga que usar Ansible sea el de nuestro Linux.

<img width="600" height="114" alt="image" src="https://github.com/user-attachments/assets/319c5a85-3cb9-408f-95c5-ba43ab651d34" />

- **Creación del playbook:** crearemos un archivo `.yaml` que será en el que luego pondremos las órdenes que queremos darle, es decir: que instale, que servicio inicie, modifique, pare…

<img width="686" height="55" alt="image" src="https://github.com/user-attachments/assets/d7888d76-8c69-4387-99f9-df6c48bb0bd4" />

### 2. Análisis del Playbook

- **Playbook entero**:
```yaml
---
- name: Configuración Base
  hosts: servidores
  become: true
  tasks:
    - name: Herramientas básicas que considero útiles para entornos de pruebas
      apt:
        name: [curl, git, htop, fail2ban]
        state: present
        update_cache: yes

    - name: Instalar K3s (Kubernetes para luego integrar en Azure)
      shell: curl -sfL https://get.k3s.io | sh -
      args:
        creates: /usr/local/bin/k3s

    # IMPORTANTE: Paramos Fail2Ban para permitir la demo de ataque luego
    - name: Detener Fail2Ban temporalmente
      service:
        name: fail2ban
        state: stopped
        enabled: yes
```

En este caso, vamos parte por parte a analizar este archivo. Es básico, pero a la hora de hacer un archivo de este estilo deberíamos comenzarlo con un `---`:

<img width="608" height="143" alt="image" src="https://github.com/user-attachments/assets/775fe4ef-96a4-41e3-ad71-63cd0aa1ccbc" />

- **Hosts:** básicamente, al hacer el otro archivo, es el nombre que pusimos en paréntesis. Esto viene bien por si tenemos una lista dividida en departamentos y solo queremos que se aplique a algunos.

**Estructura de tareas:** el resto del archivo se basará en:

- `name`: el que queramos, se puede usar para clasificar cada trozo y saber qué hace.
- `apt`: definición del tipo de paquete que usaremos (yum, apt...). Usaremos `state: present` (le dice a Ansible: "asegúrate de que esto esté instalado"). Si ya está instalado, no hace nada. Si no, lo instala.
- `update_cache`: lo único que hace es actualizar paquetes (`apt update`, básicamente) por si no lo tuviera o el enlace fuera muy antiguo ya que el servidor es nuevo.

**Instalación de Kubernetes (K3s):** lo siguiente sería Kubernetes. En este caso usaremos `shell` ya que así se instala de manera real. Usaremos el argumento `creates: /usr/local/bin/k3s`. Esto hace que, si por algún casual usas el mismo archivo porque se te olvidó agregar algo, Ansible compruebe si existe ese archivo y, si es así, directamente se salte esa parte de la instalación, evitando que quizá si reinstala se cargue algo. Según he visto hay maneras diferentes de hacer esto (condiciones como `when`, `stat` o scripts), pero creo que el `creates` está bien para el uso que le estoy dando.

<img width="694" height="98" alt="image" src="https://github.com/user-attachments/assets/94ee8c67-58f8-4cbe-8647-f7d5824459e7" />

**Gestión de Servicios:** el último apartado está pensado como dice el nombre para que paremos el servicio de Fail2Ban. Cuando queramos parar o reiniciar algo, simplemente usamos `service` acompañado del nombre del servicio y `state` para decir si lo queremos parado o habilitado.

<img width="681" height="155" alt="image" src="https://github.com/user-attachments/assets/a0f8e923-cf20-42ca-a7bd-56bb9ddf4dc7" />

### 3. Ejecución

Ahora simplemente ejecutaremos nuestro playbook:

<img width="725" height="32" alt="image" src="https://github.com/user-attachments/assets/ed757c21-d1f2-4947-a29a-53d25e6a5fa5" />

Explicación de los parámetros:

- `-i`: básicamente es para definir dónde está el archivo de inventario.
- `--ask-pass`: preguntará la contraseña de SSH.
- `--ask-become-pass`: nos pedirá la contraseña de root/sudo para que pueda hacer las acciones de dentro de nuestro archivo.

Veremos que empezará a hacer las tareas que le hayamos puesto y si no vemos ningún error cuando termine significa que podemos seguir. (Si da algún error, prueba a entrar una vez por SSH a la máquina y descarga `sshpass` si es necesario).

<img width="676" height="197" alt="image" src="https://github.com/user-attachments/assets/e268eb9f-0001-4cc8-b9e3-04e792f3d257" />

---

## Fase 2: Integración con Azure Arc

1. Para poder agregar el servidor a Azure, buscaremos dentro de Azure Portal el servicio de “Azure Arc”.

<img width="313" height="289" alt="image" src="https://github.com/user-attachments/assets/98c6a52b-548e-4dbc-bb99-7c21fbc37db4" />

2. Dentro de este servicio, buscaremos el apartado de “Infrastructure” y dentro de este iremos al apartado de “Machines”.

<img width="358" height="188" alt="image" src="https://github.com/user-attachments/assets/e16cb8ed-6938-499e-ab24-72976424a113" />

3. Una vez aquí, seleccionamos la opción de “Onboard existing machines” en la que pondremos varios parámetros para que así nos haga un script que se usará para agregar el servidor.

<img width="886" height="415" alt="image" src="https://github.com/user-attachments/assets/becca2cd-b184-4352-8b67-fedc2a40040c" />

4. Dentro, nos pedirá cosas como el grupo de recursos, la suscripción, región y parámetros como si queremos incluir SQL Servers, la forma en la que conectaremos (de forma pública o por VPN, etc.). En mi caso de manera pública ya que estamos en un entorno de pruebas.

<img width="886" height="537" alt="image" src="https://github.com/user-attachments/assets/c3a29b95-7b3e-44c8-8529-e66ec4903861" />

5. Definiremos los métodos de autenticación. Podremos hacerlo de manera manual o usando un service principal (identidad de seguridad por así decirlo) que se usa para autentificar servicios, apps, etc. Lo dicho, es un entorno de pruebas y podemos hacerlo de manera manual.

<img width="886" height="720" alt="image" src="https://github.com/user-attachments/assets/fc7e680c-df03-4c99-b6ef-205a2a3d93c7" />

6. Una vez configurado todo a nuestro caso, veremos que nos dejará acceder al apartado de scripts. Aquí simplemente copiaremos el que nos da Azure y a través de SSH o en la VM propia lo ejecutaremos para que se instale el agente.

<img width="886" height="438" alt="image" src="https://github.com/user-attachments/assets/14538698-0991-486b-b913-0fd277e6821a" />

7. Una vez ejecutado, en algún momento se detendrá y nos dará un código. Este lo deberemos poner en la siguiente página: `microsoft.com/devicelogin`.

<img width="886" height="143" alt="image" src="https://github.com/user-attachments/assets/12ad49ee-4035-4265-b068-f105ac3feced" />

8. Veremos que al poner el código y demás, nos empezará a salir que se está cargando. Aparte de esto, aparecerá el ID de suscripción, etc.

<img width="886" height="58" alt="image" src="https://github.com/user-attachments/assets/8e2af9f5-0dcf-4e18-808c-dbc2f53d0021" />

- Y si no nos sale ningún error, veremos que termina y nos tocará comprobar si se ha agregado correctamente. Como podemos ver nos saldrá ya nuestro servidor. Veremos que, si clicamos en el servidor, nos dará más detalles sobre este, como que viene de VMware y demás.

<img width="886" height="80" alt="image" src="https://github.com/user-attachments/assets/5457fd9a-b4bd-45e9-b3b3-3890ead3b8ac" />
<img width="886" height="310" alt="image" src="https://github.com/user-attachments/assets/bf3874fe-29ff-4628-93dd-ba406859305a" />

---

## Fase 3: Kubernetes

Aquí lo dividiré en antes de Azure y Azure en sí, ya que a través de los intentos, al intentar hacer el GitOps, el servidor se quedaba sin una IP externa. Para ello hice uso de MetalLB, que en pocas palabras hace la función de un load balancer y así pude arreglar el problema. Quizá hay mejores maneras pero esta me funcionó a mí. Aquí igualmente dejo lo que hice:

- Empezamos con la instalación del servicio, este se aplica sobre Kubernetes usando manifiestos.

<img width="886" height="37" alt="image" src="https://github.com/user-attachments/assets/b608123d-78a8-4c7a-bb09-f67b8bff1790" />

- Luego de esto simplemente creamos un archivo, yo le puse de nombre `metallb-pool.yaml`, dentro de esto deberemos definir el rango de direcciones que queremos y demás.

<img width="480" height="594" alt="image" src="https://github.com/user-attachments/assets/241f0917-e1dd-488a-bfa9-64905b4d5e71" />

- Por último deberemos aplicar este archivo a la configuración con el siguiente comando:

```bash
kubectl apply -f metallb-pool.yaml
```

Explicado esto seguimos con la implementación a Azure, lo primero será iniciar sesión en Azure con la VM, para que podamos conectar.

### Inicio de sesión en Azure desde la VM

1. Para ello, instalamos Azure CLI.

<img width="886" height="49" alt="image" src="https://github.com/user-attachments/assets/6998397a-7967-477e-aab2-801f293da58a" />

2. Y ahora haremos un `az login` especificando el ID del tenant ya que, si no, quizá nos da un error (me ha pasado) y que nos dé un código. (En mi caso tuve que poner el `az login` sin la parte del tenant y ya cuando me dijo el ID de tenant que debía poner, usé el comando que se ve en la foto, por si a alguien le sirve).

<img width="886" height="52" alt="image" src="https://github.com/user-attachments/assets/ad873f1a-62f6-4e6d-aa04-7bf9367fb377" />

3. Al igual que antes, deberemos ir a `microsoft.com/devicelogin` y poner el código que nos dé. Una vez termine el proceso, ya podremos ejecutar comandos de Azure desde la VM.

### Conexión del clúster

Antes de conectarlo, recomiendo registrar esto si tu cuenta es nueva/estudiante y demás:

<img width="886" height="68" alt="image" src="https://github.com/user-attachments/assets/cd870ae3-7216-4f41-b8e6-665a47fbf4ec" />

Ahora pondremos lo siguiente, con este comando lo que conseguimos es agregar el clúster que tenemos en Kubernetes al Azure Arc, deberemos especificar el RG y demás:

<img width="886" height="29" alt="image" src="https://github.com/user-attachments/assets/72a99871-6038-45c1-8078-ca681572d655" />

> **Nota importante:** al intentar hacerlo así, parece ser que me daba un error ya que las keys estaban en otro lado diferente al sitio en el que busca Azure. Para arreglar esto, deberemos hacer el siguiente comando antes de ejecutar la conexión con Azure. El comando lo que hará será exportar la ruta donde está lo que busca Azure.
>
> `export KUBECONFIG=/etc/rancher/k3s/k3s.yaml`

<img width="886" height="50" alt="image" src="https://github.com/user-attachments/assets/8675cf2c-a421-45bc-a74c-7650358d4c15" />

Veremos que empezará la instalación de los agentes. Una vez termine, veremos que en Azure Arc > Infrastructure > Kubernetes cluster, debería aparecer también el clúster que está en nuestra VM.

<img width="886" height="83" alt="image" src="https://github.com/user-attachments/assets/2f1fed2f-eadf-4ca3-b876-6545bf0e552c" />

---

## Fase 4: Seguridad Zero-Trust (Sentinel)
Ya teniendo todo, voy a enseñar como crear alguna alerta para un server que no esta en la nube, lo primero sera configurar el sentinel. Para ello deberemos de hacer varias cosas dentro de azure, como configurar microsoft sentinel que en pocas palabras en una solucion de seguridad en la nube que recopila logs, detecta amenazas, te permite crear alertas y automatizar soluciones en funcion del tipo de ataque que te hagan (playbooks con automation rules etc)

1.	Configuracion para Sentinel:
   * Crea un Log Analytics Workspace en Azure.
      * Para ello buscamos Log Analytics Workspace en el buscador o entre los servicios que se nos ofrece en azure
        
        <img width="319" height="75" alt="image" src="https://github.com/user-attachments/assets/edfff4d4-7708-4cfa-8a4f-6d1a69d67f57" />

     * Una vez dentro de esta opcion, pondremos nombre, region y en que grupo de recursos queremos ponerlo, esto ya depende de cada quien.

       <img width="501" height="419" alt="image" src="https://github.com/user-attachments/assets/ba0e7ee3-74a3-4db9-b545-4f001cb5e390" />

  * Una vez creado el workspace, simplemente deberemos de buscar el servicio de Microsoft Sentinel
    
    <img width="163" height="188" alt="image" src="https://github.com/user-attachments/assets/5d2afd4f-1429-4746-9dd8-40c8c179ee33" />

  * Buscaremos crear uno

    <img width="428" height="194" alt="image" src="https://github.com/user-attachments/assets/75b85acb-2311-4e21-8478-346969ef5aa6" />

  * Cuando le hayamos dado, nos debera de salir nuestro workspace, simplemente lo escogeremos

     <img width="550" height="144" alt="image" src="https://github.com/user-attachments/assets/332bd229-b845-4e24-ab68-f0069eca34a0" />
     
  * Ya dentro de este servicio, buscaremos en `content management` la opcion de content hub (catálogo de soluciones y contenido, tiene workbooks, conectores, reglas ....)

    <img width="284" height="328" alt="image" src="https://github.com/user-attachments/assets/ae2c97ec-f53e-472d-bde3-718043bff449" />

  * Y buscaremos el de syslog, para poder conectar los logs de nuestra maquina
    
    <img width="294" height="437" alt="image" src="https://github.com/user-attachments/assets/2948e89b-6a8f-4c3e-8b1f-336977d6bad4" />
    > 
> **Nota importante:** Como dato, estuve bastante tiempo y no me di cuenta que el syslog no conectaba básicamente porque la carpeta de syslog que mira este conector ni estaba en mi Ubuntu
> Para eso instala Rsyslog
> ```
> sudo apt install -y rsyslog
> sudo systemctl enable --now rsyslog
> sudo systemctl status rsyslog --no-pager
> #Reinicias el ssh
> sudo systemctl restart ssh
> ```
> 

  * Una vez aclarado esto, seleccionaremos esta solucion y la instalaremos
    
    <img width="281" height="401" alt="image" src="https://github.com/user-attachments/assets/e3765379-4f75-4c6d-8ced-9f7081eeccaf" />

  * En sentinel iremos al apartado de data connectors
    
    <img width="408" height="192" alt="image" src="https://github.com/user-attachments/assets/98d736f2-15cb-4136-a742-cc95bfe0c527" />

  * Y buscaremos el que acabamos de instalar

    <img width="414" height="283" alt="image" src="https://github.com/user-attachments/assets/0834d0c0-acc3-42bf-adbf-d2276e6076cf" />

  * Y le daremos a la opcion de Open connector page

    <img width="325" height="84" alt="image" src="https://github.com/user-attachments/assets/17540850-93dd-47ce-ad93-9dab5aa2617a" />

  * Dentro de la pagina del connector, lo que haremos sera crear una DCR (Data collection rule) con el fin de especificar que queremos que se recopile dentro de una vm (pudiendo especificar cual) y a donde queremos mandarlo (workspace normalmente)

      <img width="588" height="420" alt="image" src="https://github.com/user-attachments/assets/e3c11e95-db8d-4e90-a67e-33bd6c5cb47c" />

  * En la primera parte de la configuracion, le pondremos un nombre a la regla, subscripcion y rg

    <img width="528" height="241" alt="image" src="https://github.com/user-attachments/assets/f13e233b-030e-45aa-92a7-d61201d2fbfe" />

  * En el apartado de resources, deberemos de especificar la maquina a la que le extraeremos los logs

    <img width="886" height="217" alt="image" src="https://github.com/user-attachments/assets/3fdec653-1ca0-449f-a000-9a9221997382" />

  * Y en el apartado de collect, buscaremos que tipo de log en especifico es lo que queremos que extraiga y en la parte de la derecha definiremos a que nivel queremos extraerlo, el log level tal y como lo ponemos en la imagen por ejemplo extraeria solo mensajes graves en la autentificacion tipo warning/notice/error. Y si ponemos un LOG_DEBUG, recogeria mas volumen de datos (no siempre es bueno, depende del objetivo), que en nuestro caso seria perjudicial ya que tendrias cosas que no nos sirven y seria mas tedioso de analizar luego.

    <img width="789" height="334" alt="image" src="https://github.com/user-attachments/assets/3a202f2b-8cda-49bc-869b-b88dfa397759" />

  * Luego de esto, en el apartado de `configuration` buscaremos analytics
    
    <img width="363" height="269" alt="image" src="https://github.com/user-attachments/assets/ec2633fa-96b4-411e-8f16-0afa4df5a8f5" />

    
  > ***Nota Importante*** antes se hacia en esta misma ventana, ahora te redirigira a una pestaña aparte 

  * Dentro de la ventana del defender, buscaremos la opcion de crear reglas con una consulta programada

    <img width="638" height="476" alt="image" src="https://github.com/user-attachments/assets/3fff31f2-e7cf-411e-852a-db9cb7efc047" />

  * Dentro de la regla, le pondremos nombre y yo le pondre gravedad alta para probar

    <img width="638" height="476" alt="image" src="https://github.com/user-attachments/assets/9667aa25-0307-46f0-841b-1122aa314333" />

  * El siguiente apartado es la logica de nuestra regla, deberemos de decirle que consulta debera hacerle a los logs y en funcion del resultado que se active. Para ello pondremos la siguiente consulta:
```
Syslog
| where Facility == "auth" or Facility == "authpriv"
| where SyslogMessage contains "Failed password"
| summarize Intentos = count() by Computer, HostIP
| where Intentos > 10
```
  <img width="886" height="268" alt="image" src="https://github.com/user-attachments/assets/068fbb5d-7e19-4a15-a79a-5cad60088407" />

  * Una vez le hayamos puesto la consulta, bajaremos hasta llegar a la parte de la programacion de la consulta, aqui definiremos cada cuanto la hara. Para este laboratorio pondre 5 minutos.

    <img width="886" height="307" alt="image" src="https://github.com/user-attachments/assets/b57fc018-9117-4a6d-9bba-4c08c91c9b3c" />
    

  * Una vez hayamos puesto esto, ya que estamos probando, no tocare nada mas, simplemente revisaremos y crearemos la regla

    <img width="886" height="391" alt="image" src="https://github.com/user-attachments/assets/8cd70fab-86ce-4455-bb2a-a37b3be07f37" />

2.	El Ataque:
  * Desde otra maquina que tenga acceso a la vm que tenemos agregada a azure, deberemos de hacer varios intentos fallidos de inicio de sesion de ssh para que lo detecte como ataque.
    Para ello tengo este script que hara 50 intentos y asi podemos probar esto mejor
    
    ```
    for i in {1..50}; do echo "Intento de hackeo $i..."; sshpass -p "clavefalsa$i" ssh -o StrictHostKeyChecking=no adminuser@IP_DE_TU_VM "exit" 2>/dev/null; done
    ```
    
  * Una vez hechos, veremos que si vamos a los logs de la propia maquina, ya saldran ahi
    
    <img width="886" height="93" alt="image" src="https://github.com/user-attachments/assets/ba5ba355-a3c0-4702-9aad-4cd2b818fc5f" />

  * Y si vamos al apartado de alertas, cuando haya hecho la consulta, veremos que tenemos la alerta

    <img width="886" height="197" alt="image" src="https://github.com/user-attachments/assets/166635b3-1b92-49ea-86eb-ed2ae2cbd0e2" />


    <img width="571" height="521" alt="image" src="https://github.com/user-attachments/assets/15bde8a1-fd03-4fea-885d-dcec99fd34e9" />


  * Y como dato extra, podremos ver en el apartado de nuestro collector, el numero de logs que ha pillado

    <img width="886" height="530" alt="image" src="https://github.com/user-attachments/assets/da8ace9a-9cfb-4ff8-869f-1c0fd1ad6275" />

________________________________________

## Fase 5: Final
Ya hemos llegado al final, es un laboratorio bastante simple pero que hacerlo me a servido para ir familiarizando con servicios como el azure arc. Admito que no era tan simple, ya que tuve muchos problemas con la parte de kubernetes ya que es lo que menos he tocado y con la parte del syslog ya que estuve un rato buscando culpables por todo azure. Dicho esto, espero que esto le sirva a alguien, ya que como tal no hay tutoriales tan especificos de esto. Gracias por leerlo y a ver que mas proyectos se me van ocurriendo

---
