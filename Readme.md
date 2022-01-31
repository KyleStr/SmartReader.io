*Esta herramienta digital forma parte del catálogo de herramientas del **Banco Interamericano de Desarrollo**. Puedes conocer más sobre la iniciativa del BID en: [code.iadb.org](https://code.iadb.org/es)*

## *SmartReader*

### Descripción y contexto

---

*SmartReader* es una herramienta que utiliza técnicas de Procesamiento de Lenguaje Natural para proporcionar una nueva perspectiva a tu investigación (pregunta de investigación y literatura recopilada). Esto lo hace a través de consultar a Google y recuperar información actualizada y relacionada con tu pregunta de investigación. *SmartReader* es una alternativa para hacerle frente a la necesidad que tienen los trabajadores de conocimiento de mantener el ritmo a la cantidad exponencial de información que se genera todos los días y que se comparte en el internet.

El Departamento de Conocimiento Innovación y Comunicación del **Banco Interamericano de Desarrollo** creó esta herramienta luego de reconocer esta necesidad además de querer explorar tecnologías como la Inteligencia Artificial y el Procesamiento del Lenguaje Natural para asistir en el proceso de Gestión del Conocimiento.

La herramienta consta de cuatro interfaces: 1) *Definición del modelo*, 2) *Estado del modelo*, 3) *Aplicación del modelo*, e 4) *Interfaz de resultados*. El siguiente diagrama de flujo explica el funcionamiento de la herramienta:

Como se muestra en la gráfica, de izquierda a derecha y de arriba a abajo, el proceso comienza cuando el usuario crea un modelo al ingresar un conjunto de temas y subtemas que son relevantes a una determinada pregunta de investigación. Con este conjunto de palabras, la herramienta generará cadenas de consulta utilizadas para recuperar los datos más relevantes disponibles en Google. Luego, al aplicar *sklearn.TfidfVectorizer*, se creará un modelo con términos ponderados. Posteriormente, se aplica un modelo al corpus de documentos que el usuario carga en un archivo comprimido de archivos *.txt*. El proceso ocurre al calificar los párrafos de cada documento, extraer sus entidades y ubicaciones correspondientes y ordenar estos párrafos en orden descendente. Después de elegir los párrafos con mayor calificación (se seleccionó un número aleatorio de 50 párrafos), la herramienta procederá a seleccionar las oraciones más relevantes. Los cálculos dará como resultado un archivo *.json* y la visualización de las palabras clave, entidades, ubicaciones geográficas y frases más relevantes de nuestro corpus de documentos. Para obtener más información sobre cómo contribuir a este proyecto, consulta la [siguiente entrada](https://www.google.com/) en nuestro blog Abierto al Público.

## Guía de instalación (Para desarrollar)

---
## Requisitos
Se deberá disponer previamente de:
* Un API key de [CORE](https://core.ac.uk/) 
* Un API key y secret de un usuario en AWS con permisos de acceso al bucket S3 con las publicaciones del BID y modelos de GloVe.

## Usando Docker
Para que el proyecto sea reproducible en distintos entornos, se recomienda utilizar [docker](https://www.docker.com/). Primero creamos las imágenes necesarias. Este proyecto se basa en una imagen de Python y en una imagen de MongoDB.

### Construir
Para construir las imágenes ejecutamos el siguiente comando:
```
docker-compose -p smart-reader-app build
```
### Arrancar
En cada entorno en el que nos encontremos podemos proveer las siguientes variables de entorno para arrancar la aplicación:
* `DB_USER`: Usuario de base de datos
* `DB_PWD`: Contraseña de base de datos 
* `DB_PORT`: Puerto de la base de datos
* `DB_HOST`: Host de la base de datos (por defecto es el contenedor de la MongoDB)
* `AWS_ACCESS_KEY_ID`: Identificador de usuario de AWS
* `AWS_SECRET_ACCESS_KEY`: Secret key del usuario de AWS
* `DOWNLOAD_MODELS`: Flag para determinar si descargar o no los modelos. Se recomienda ponerlo a `true` la primera vez y a `false` las siguientes veces para acelerar el arranque del contenedor
* `CORE_API_KEY`: API key de CORE
* `MIN_FILES`: Número mínimo de documentos a analizar
* `LOG_LEVEL`: Nivel de log

En entorno local, debemos crear un fichero `.env` en la raíz del proyecto con el siguiente contenido:
```
DB_USER=user
DB_PWD=pass
DB_PORT=27017
DB_HOST=localhost
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
DOWNLOAD_MODELS=true
CORE_API_KEY=
MIN_FILES=50
LOG_LEVEL=INFO
```

Para arrancar la aplicación basta con ejecutar:
```
docker-compose -p smart-reader-app up -d
```
Para parar la aplicación ejecutaremos:
```
docker-compose -p smart-reader-app stop
```

## Sin usar Docker

#### Requerimientos mínimos del sistema

1. El servidor deberá contar con al menos 20GB de espacio en disco y un RAM de 4GB. La herramienta ocupa un espacio de mínimo 3GB.
2. Se recomienda una buena conexión a Internet dado que una gran cantidad de datos se descarga durante la configuración del servidor.
3. Recomendamos instalar la aplicación en una distribución de CentOS.


#### Instalación de Python (3.9)

Primero comprueba si python 3.9 ya está instalado en el servidor ejecutando el comando:
```
python3 -V
```

En caso contrario, sigue los siguientes pasos:

```
sudo yum update -y
sudo yum install -y python39
```

#### Instalación de pip

```
sudo yum -y install python39-pip
sudo pip install –upgrade pip
```
Confirma la instalación con: `pip3 -V`

#### Instalación de MongoDB para el almacenamiento de datos

1. Navega a la carpeta madre (home)
2. Haz clic [aquí](https://www.digitalocean.com/community/tutorials/how-to-install-mongodb-on-centos-7) para ver los pasos de instalación de MongoDB. Si el enlace no funciona, copia y pega la siguiente url en tu navegador https://www.digitalocean.com/community/tutorials/how-to-install-mongodb-on-centos-7 

#### Crea un entorno

1. Crea una nueva carpeta para el proyecto y navega a esa carpeta
2. Crea un entorno virtual e instala python3 en el entorno con el siguiente comando: `python3.6 -m venv my_env` (donde `my_env` es el nombre del entorno)
3. Activa el entorno recién creado con el siguiente comando: `source my_env/bin/activate`  
4. Para desactivar el entorno usa el siguiente comando: `deactivate`  

#### Instalación de dependencias

1. Activa el entorno que creaste en el paso anterior
1. Navega hacia la carpeta donde reside el proyecto
1. Para instalar el resto de los paquetes deberás modificar tu configuración local usando la siguiente línea: `export LC_ALL=C`.
1. Instala todas las librerías que están en el archivo `requirements.txt` usando el siguiente comando:
    ```python
    pip3 install -r requirements.txt
    ```
1. Descarga los datos en inglés de la librería *spacy* así:
    ```python    
    python3 -m spacy download en_core_web_sm
    python3 -m spacy download es_core_news_sm
    ```
1. La librería *nltk* deberá usarse utilizando python. Para esto, activa `python` en la línea de comandos.
1. Importa *nltk* y descarga todos los datos usando los siguientes comandos:
    ```python3
    python -m nltk.downloader all
    ```
1. Descarga el modelo GloVe y las publicaciones del BID desde el bucket S3 de AWS ejecutando los siguientes comandos. Necesitarás la herramienta [awscli](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html):
    ```bash
    aws s3 cp s3://smart-reader-app-models/glove.6B.100d.txt data/glove/glove.6B.100d.txt
    aws s3 cp s3://smart-reader-app-models/glove-sbwc.i25.txt data/glove/glove-sbwc.i25.txt
    aws s3 cp s3://smart-reader-app-publications/publications.tar.gz data/publications.tar.gz
    aws s3 cp s3://smart-reader-app-publications/blogs/blogs.json data/repositories/blogs.json
    tar --strip-components 1 -xzf data/publications.tar.gz -C data/repositories/
    rm data/publications.tar.gz
    ```
1. Completa los datos de conexión a la BD en el fichero `config/config.ini` e inserta el corpus en la BD utilizando el siguiente comando:
    ```bash
    python src/main/python/smart_reader_app/mongo_insert_corpus.py
    ```

## Guía de usuario

---

## Configuración

- Rellena la configuración del inicial `config/config.ini`

- Rellena la configuración de los logs `config/log.conf`

- Por defecto coge los archivos de la carpeta `config`, si quieres introducir otros archivos de configuración se pasan la ruta por parametro.

    `-e` es la ruta del fichero de configuracion del entorno.

    `-lf` es la ruta de configuracion de los logs.

### Server Startup

1. Ve a la carpeta donde se encuentra el paquete a ejecutar.

    ```bash
    cd smart-reader-app/src/main/python
    ```

2. Ejecuta el paquete de esta forma:

    ```bash
    python -m smart_reader_app
    ```

3. El servidor estará funcionando. Para acceder a la aplicación, utilizando tu navegador de preferencia, navega a http://127.0.0.1:8080

## Cómo funciona

SmartReader utiliza técnicas modernas de procesamiento de lenguaje natural y aprendizaje automático para acelerar tu proceso de investigación. Siga estos cuatro pasos:

1. ### Definición del Modelo

En esta página se define el tema principal y los subtemas de la investigación. Describe cada subtema que incluyas, escribiendo un conjunto de palabras clave relacionadas con dicho subtema, separadas por comas. Al pulsar Enviar, SmartReader utilizará la información para crear un modelo de lenguaje que aplicará durante el análisis.

2. ### Estado del Entrenamiento del Modelo
Esta página muestra el estado del entrenamiento del modelo definido en el paso 1. El estado se mostrará como "Processing" durante el entrenamiento y "Done" una vez que el modelo esté listo.

3. ### Aplicación del Modelo
En esta página se selecciona el modelo entrenado y se elige la colección de textos que se desean analizar con el modelo. Puedes elegir entre la colección de publicaciones y blogs del BID, o una colección de artículos de investigación de acceso abierto de instituciones académicas. Cuando presiones Enviar, SmartReader usará el modelo definido para analizar la colección elegida.

4. ### Resultados de SmartReader
Esta página muestra el estado de procesamiento del análisis junto al nombre del modelo seleccionado en el paso 3. Una vez finalizado el análisis, verás un botón azul con la opción de "Visualizar resúmenes". También puedes descargar los resultados en formato JSON

## Interpretación de los resultados
* El primer resultado que muestra SmartReader es el resultado de un proceso de **Modelado de Temas**, que agrupa las ideas clave del corpus según su similitud y las ubica en 5 círculos distintos. Cada círculo representa un tema, que está conformado conceptualmente por la lista de palabras clave relacionadas que fueron extraídas del texto.

* En esta visualización, el tamaño del círculo indica la prevalencia de este tema en todo el corpus, y la distancia entre cada círculo indica la similitud de los temas. Esto le da al investigador un resumen visual de la distribución temática del corpus y podría revelar temas importantes que no se trazaron inicialmente, para ayudar a guiar su investigación posterior.

* Acompañando la visualización hay una extracción de **Oraciones Clave** de los textos que son muy representativos de cada tema individual y relativamente únicos en cuanto a las otras oraciones relacionadas.

* También hay una lista de **Clasificación de Documentos** que clasifica los documentos del corpus analizado según su relevancia, con enlaces que puedes seguir para leer más.

* Además de ese análisis, SmartReader también prepara un conjunto de **Nubes de Conceptos** a nivel del tema general y al nivel de cada subtema que definió en el modelo. Las nubes se generan para palabras clave, ubicaciones y entidades. Por último, para cada subtema SmartReader selecciona un conjunto de **Oraciones de Resumen** y las resalta en el texto original, para facilitar la lectura posterior por parte del investigador.


## Cómo contribuir

---

Hemos puesto a disposción el código de esta herramienta y nos encataría escuchar tu experiencia con ella. Para ver un listado de posibles mejoras que podrías hacer a *SmartReader* consulta la pestaña *Issues* de este repositorio y el [CONTRIBUTING.md](https://github.com/EL-BID/SmartReader/blob/master/CONTRIBUTING.md).  
Finalmente, te comentamos que escribimos una entrada sobre *SmartReader* en *Abierto al Público*. El enlace al blog está en la sección de [Información Adicional](#información-adicional) de este documento. ¡Quedamos atentos!

## Código de Conducta

---

Puedes ver el código de conducta [aquí](https://github.com/EL-BID/SmartReader/blob/master/CODE-OF-CONDUCT.md)

## Autores

---
© 2017 Banco Interamericano de Desarrollo e Instituto para el Futuro.
Este software es el resultado de una asociación entre el Banco Interamericano de Desarrollo y el [Instituto para el Futuro](http://www.iftf.org/).
Los derechos de autor del software son compartidos por ambas organizaciones, incluso si el licenciante es únicamente el Banco Interamericano de Desarrollo.

Banco Interamericano de Desarrollo  
Involucrados:

- [Daniela Collaguazo](mailto:danielaco@iadb.org)
- [Kyle Strand](mailto:kyles@iadb.org)
- Seaford Bacchas

## Información Adicional

---

[Blog en Abierto al Público](https://blogs.iadb.org/abierto-al-publico/2018/09/07/smartreader-herramienta-de-analisis-de-texto/)

## Licencia

---

Puedes ver la licencia del código fuente [aquí](https://github.com/EL-BID/SmartReader/blob/master/LICENSE.md)

La Documentación de Soporte y Uso del software se encuentra licenciada bajo Creative Commons IGO 3.0 Atribución-NoComercial-SinObraDerivada (CC-IGO 3.0 BY-NC-ND)

## Limitación de responsabilidades

---

El BID no será responsable, bajo circunstancia alguna, de daño ni indemnización, moral o patrimonial; directo o indirecto; accesorio o especial; o por vía de consecuencia, previsto o imprevisto, que pudiese surgir:

i. Bajo cualquier teoría de responsabilidad, ya sea por contrato, infracción de derechos de propiedad intelectual, negligencia o bajo cualquier otra teoría; y/o

ii. A raíz del uso de la Herramienta Digital, incluyendo, pero sin limitación de potenciales defectos en la Herramienta Digital, o la pérdida o inexactitud de los datos de cualquier tipo. Lo anterior incluye los gastos o daños asociados a fallas de comunicación y/o fallas de funcionamiento de computadoras, vinculados con la utilización de la Herramienta Digital.