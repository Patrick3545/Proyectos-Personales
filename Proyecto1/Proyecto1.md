
---

# Despliegue de Servidor Híbrido con Azure Arc y Kubernetes

Lo primero que tendremos que hacer antes de empezar con esto sería plantear un esquema para que nos quede más claro todo esto. En mi caso no es algo muy complejo, pero no viene mal para que quede más claro todo. Ya con esto y sabiendo la maquina y cosas de azure que usaremos, podremos seguir adelante.

## Fase 1: Preparación del Servidor con Ansible

En primer lugar, voy a desplegar un playbook de ansible para instalar varias cosas que no vienen nada mal a nuestro Ubuntu. Es algo simple pero que sirve para poder repasar estos comandos y así ahorrarnos tiempo haciendo esas instalaciones y configurando el fail2ban.

El despliegue lo puedes hacer de dos maneras:

* Instalando en la propia VM ansible y ejecutando el archivo.


* O si tienes WSL (Windows subsystem for linux) instalado en tu pc principal pues instalas ahí el ansible y lo ejecutas ahí por si quieres hacerlo más realista.



### 1. Instalación y Configuración

* **Instalación de ansible en Ubuntu:**


*(Inserta aquí la imagen de instalación o el comando de `apt install ansible`)* 


* 
**Creación del archivo de inventario:** Creación del archivo de servidores que tendrá ansible. El contenido del archivo en el que tendremos los servidores, simplemente pondremos la ip de nuestro servidor y le diremos que el usuario que tenga que usar ansible sea el de nuestro Linux.


* 
**Creación del Playbook:** Crearemos un archivo `.yaml` que será en el que luego pondremos las ordenes que queremos darle, es decir, que instale, que servicio inicia, modifica, para… 



### 2. Análisis del Playbook

En este caso, vamos parte por parte a analizar este archivo, es básico, pero a la hora de hacer un archivo de este estilo deberemos de comenzarlo con un `---`:

* 
**Hosts:** básicamente al hacer el otro archivo es el nombre que pusimos en paréntesis, por si tenemos una lista dividida en departamentos y solo queremos que se aplique en algunos.


* **Estructura de tareas:** El resto del archivo se basará en:
* 
`name`: el que queramos, se puede usar para clasificar cada trozo y ver saber que hace.


* 
`apt`: definición del tipo de paquete que usaremos, yum, apt…. Usaremos `state: present` (Le dice a Ansible: "Asegúrate de que esto esté instalado"). Si ya está instalado, no hace nada. Si no, lo instala.


* 
`updated_cache`: lo único que hace es actualizar paquetes (apt update basicamente) por si no lo tuviera o el enlace que tuviera fuera muy antiguo ya que el servidor es nuevo.




* 
**Instalación de Kubernetes (K3s):** Lo siguiente seria kubernetes, en este caso usaremos Shell ya que así se instala de manera real. Usaremos el argumento `creates: /usr/local/bin/k3s`. Esto hace que, si por algún casual usaras el mismo archivo porque se te olvido agregar algo, puedas hacer que ansible compruebe si existe ese archivo y si es así, directamente salte esa parte de la instalación, evitando que quizá si reinstala se cargue algo. Según he visto hay maneras diferentes de hacer esto (condiciones como *when*, *stat* o scripts), pero creo que el `creates` esta bien para el uso que le estoy dando.


* 
**Gestión de Servicios:** El último apartado está pensado como dice el nombre para que paremos el servicio de fail2ban, cuando queramos parar o reinciar algo, simplemente usamos `service` acompañado del nombre del servicio y `state` para decir si lo queremos parado o habilitado.



### 3. Ejecución

Ahora simplemente ejecutaremos nuestro playbook:
*(Inserta aquí el comando `ansible-playbook`)* 

Explicación de los parámetros:

* 
`-i`: básicamente es para definir donde está el archivo de inventario.


* 
`--ask-pass`: preguntara la contraseña de ssh.


* 
`--ask-become-pass`: nos pedira la contraseña de root para que pueda hacer las acciones de dentro de nuestro archivo.



Veremos que empezara a hacer las tareas que le hayamos puesto y si no vemos ningún error cuando termine significa que podemos seguir.

---

Fase 2: Integración con Azure Arc 

Para poder agregar el servidor a azure, buscaremos dentro de azure portal el servicio de “azure arc”.

1. Dentro de este servicio, buscaremos el apartado de “infraestructures” y dentro de este iremos al apartado de “machines”.


2. Una vez aquí, seleccionamos la opción de “Onboard existing machines” en la que pondremos varios parámetros para que así nos haga un script que se usara para agregar el servidor.


3. Dentro, nos pedirá cosas como el grupo de recursos, la suscripción, región y parámetros como si queremos incluir sql servers, la forma en la que conectaremos, ya sea de forma pública o por vpn etc. En mi caso de manera publica ya que estamos en un entorno de pruebas.


4. Definiremos los métodos de autentificación, podremos hacerlo de manera manual o usando un service principal (identidad de seguridad por así decirlo) que se usa para cuando autentificar servicios, apps etc. Lo dicho, es un entorno de pruebas y podemos hacerlo de manera manual.


5. Una vez configurado todo a nuestro caso, veremos que nos dejara acceder sin errores al apartado de scripts, aquí simplemente copiaremos el que nos da azure y a través de ssh o en la vm propia, lo ejecutaremos para que se instale el agente.


6. En algún momento se detendrá y nos dará un código, este lo deberemos de poner en la siguiente página: `microsoft.com/devicelogin`.


7. Veremos que al poner el código y demás, nos empezará a salir que se esta cargando, aparte de esto, aparecerá el id de suscripción etc.



Y si no nos sale ningún error, veremos que termina y nos tocara comprobar si se ha agregado correctamente. Como podemos ver nos saldrá ya nuestro servidor. Veremos que, si clicamos en el servidor, nos dará más detalles sobre este, como que viene de vmware y demás.

---

Fase 3: Kubernetes 

Para este paso, lo primero será iniciar sesión en azure con la vm, para que podamos conectar.

1. En primer lugar, instalamos azure cli.


2. Y ahora haremos un `az login` especificando el id del tenant ya que, si no, quizá nos da un error (me ha pasado) y que nos dé un código.


3. Al igual que antes, deberemos de ir a `microsoft.com/devicelogin` y poner el código que nos de.


4. Una vez termine el proceso, ya podremos ejecutar comandos desde la vm.



### Conexión del Clúster

Ahora pondremos lo siguiente, con este comando lo que conseguimos es agregar el cluster que tenemos en kubernetes al azure arc, deberemos de especificar el rg y demás:
*(Inserta el comando `az connectedk8s connect...` aquí)* 

> 
> **Nota importante:** Al intentar hacerlo así, parece ser que me daba un error ya que las keys estaban en otro lado diferente al sitio en el que busca azure. Para arreglar esto, deberemos de hacer el siguiente comando antes de ejecutar la conexión con azure. El comando lo que hará será exportar la ruta en donde esta lo que busca azure.
> `export KUBECONFIG=/etc/rancher/k3s/k3s.yaml` 
> 
> 

Veremos que empezara la instalación de los agentes. Una vez termine, veremos que en Azure Arc > Infraestructure > Kubernetes cluster, debería de aparecer también el cluster que esta en nuestra vm.

### Prueba de GitOps

Una vez agregado, iremos con la prueba que buscamos hacer. Para este paso, voy a hacer un fork (copia de un repositorio) que se usa para este tipo de pruebas y modificarlo un poco para ver cambios y demás. El repositorio es este: `Azure/arc-k8s-demo: Artifacts for Arc For Kubernetes Demo`.

1. En mi caso me meteré en `cluster-apps/arc-k8s-demo.yaml` y agregare esto, para poder ver mejor esto ya que es una pagina muy sencilla. Tuve que arreglar un problema, en el código, debía agregar lo siguiente en el código, porque me daba error al no saber el namespace.


2. Una vez agregado esto, lo que haremos será irnos al cluster y decirle que este es el repositorio que queremos que mire.


3. Dentro de nuestro cluster de kubernetes que aparece en el azure arc, buscaremos el apartado de settings e iremos a la opción de “gitops”.


4. Deberemos de crear uno en el que pondremos lo siguiente en el primer apartado. Importante poner `cluster` en el scope para evitar algún problema de permisos (es un entorno de laboratorio).


5. En el segundo apartado, le diremos que es un repositorio de git. Especificamos el link, si el repositorio es publico o no y cada cuanto queremos que se actualice, pondré `1m` para pruebas.


6. El ultimo apartado básicamente es en donde le tenemos que decir que archivo queremos que vea, si se lo decimos mal, no podrá ver nuestro `.yaml`. Para ello creamos uno y pondremos lo siguiente.


7. Marcamos el `prune` para que, si borramos el archivo de github, en azure el flux haga lo mismo.



Y ya por ultimo seria ver si la app se levanta, si ejecutamos este comando en la vm, podremos ir viendo que se ha ido desplegando:

```bash
watch kubectl get pods -A

```

---

**¿Te gustaría que te ayude a redactar los bloques de código YAML y Bash exactos para rellenar los huecos donde en tu Word original había capturas de pantalla?**
