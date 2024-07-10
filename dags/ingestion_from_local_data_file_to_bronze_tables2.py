#
# Author: GersonRS
# Email: gersonrodriguessantos8@gmail.com
#
"""
Este é um exemplo de DAG que usa SparkKubernetesOperator e SparkKubernetesSensor.
Neste exemplo, crio duas tarefas que são executadas sequencialmente.
A primeira tarefa é enviar sparkApplication no cluster Kubernetes.
E a segunda tarefa é verificar o estado final do sparkApplication que enviou
no primeiro estado.
"""

from datetime import timedelta

# [INICIO import_module]
# O decorator dag; precisaremos disso para instanciar um DAG
from airflow.decorators import dag

# Operadores; precisamos disso para funcionar!
from airflow.providers.cncf.kubernetes.operators.spark_kubernetes import SparkKubernetesOperator
from airflow.providers.cncf.kubernetes.sensors.spark_kubernetes import SparkKubernetesSensor
from airflow.utils.dates import days_ago

# [FIM import_module]
# Documentação baseada em Markdown que serão renderizados nas páginas Grid , Graph e Calendar.
doc_md_DAG = """
# DAG Entrega dos dados que vem da landing para o lake

Este é um exemplo de DAG que usa SparkKubernetesOperator e SparkKubernetesSensor.
Neste exemplo, crio duas tarefas que são executadas sequencialmente.
A primeira tarefa é enviar sparkApplication no cluster Kubernetes.
E a segunda tarefa é verificar o estado final do sparkApplication que enviou no primeiro estado.

## Objetivo desta DAG

* Processar todos os dados da landing referentes aos dados de user, subscription, credit_card e movies e passar para o lake

Execute para testar.
"""

# [INICIO default_args]
# Esses argumentos serão basicamete repassados para cada operador
# Você pode substituí-los pelos valores que quiser durante a inicialização do operador
default_args = {
    "owner": "Gersonrs",
    "depends_on_past": False,
    "start_date": days_ago(1),
    "email": ["gersonrodriguessantos8@gmail.com"],
    "email_on_failure": False,
    "email_on_retry": False,
    "max_active_runs": 1,
    "retries": 1,
    "retry_delay": timedelta(1),
}
# [FIM default_args]


# [INICIO dag]
@dag(
    dag_id="ingestion-from-local-data-file-to-bronze-tables2",
    default_args=default_args,
    catchup=False,
    schedule_interval="@once",
    max_active_runs=1,
    tags=["spark", "kubernetes", "s3", "sensor", "minio", "bronze"],
    doc_md=doc_md_DAG,
)
def ingestion_from_local_data_file_to_bronze_tables_dag() -> None:
    """
    `ingestion_from_local_data_file_to_bronze_tables_dag()` é uma função que define um DAG
    (Directed Gráfico acíclico) no Apache Airflow. Este DAG é responsável por ingerir
    dados locais da imagem para o minio. Consiste em duas tarefas:
    """

    # [INICIO set_tasks]

    # A variável(task) `submit` está criando uma instância da classe
    # `SparkKubernetesOperator`. Esse operador é responsável por enviar um
    # `SparkApplication` para execução em um cluster Kubernetes. Atravez da definição
    # de yaml para acionar o processo, usando o spark-on-k8s para operar com base nos
    # dados e criando um `SparkApplication` em contêiner.
    submit = SparkKubernetesOperator(
        task_id="ingestion_from_local_data_file_to_bronze_tables_submit",
        namespace="processing",
        application_file="spark_jobs/ingestion_from_local_data_file_to_bronze_tables.yaml",
        kubernetes_conn_id="kubernetes_default",
        do_xcom_push=True,
        # O parâmetro `params` no `SparkKubernetesOperator` é usado para passar parâmetros
        # adicionais para o `SparkApplication` que será executado no cluster Kubernetes.
        # Esses parâmetros podem ser acessados no código do aplicativo Spark.
        params={
            "mainApplicationFile": "s3a://scripts/ingestion/ingestion_to_bronze.py",
            "job_name": "ingestion_from_local_data_file_to_bronze_tables-{{ ts_nodash | lower }}-{{ task_instance.try_number }}",  # noqa: E501
            "minio_bucket": "curated",
        },
        doc_md="""
        ### Proposta desta tarefa

        * Ser responsável por enviar um `SparkApplication` para execução em um cluster Kubernetes.

        * Definir um yaml para acionar o processo, usando o spark-on-k8s para operar com base nos
        dados e criando um `SparkApplication` em contêiner.
        """,
    )

    # A variável(task) `sensor` está criando uma instância da classe
    # `SparkKubernetesSensor`. Este sensor é responsável por monitorar o status de um
    # `SparkApplication` em execução em um cluster Kubernetes. Usando o sensor para ler
    # e visualizar o resultado do `SparkApplication`, lê do xcom e verifica o par de
    # status [chave e valor] do `submit`, contenco o nome do `SparkApplication` e
    # passando para o `SparkKubernetesSensor`.
    sensor = SparkKubernetesSensor(
        task_id="ingestion_from_local_data_file_to_bronze_tables_sensor",
        namespace="processing",
        application_name="{{task_instance.xcom_pull(task_ids='ingestion_from_local_data_file_to_bronze_tables_submit')['metadata']['name']}}",  # noqa: E501
        kubernetes_conn_id="kubernetes_default",
        attach_log=True,
        doc_md="""
        ### Proposta desta tarefa

        * Ser responsável por monitorar o status de um `SparkApplication` em execução em um cluster
        Kubernetes.

        * Usar o sensor para ler e visualizar o resultado do `SparkApplication`.

        * Ler do xcom e verifica o par de status [chave e valor] do `submit`, contenco o nome do
        `SparkApplication` e passando para o `SparkKubernetesSensor`.
        """,
    )
    # [FIM set_tasks]

    # [INICIO task_sequence]
    # `submit >> sensor` está definindo a dependência entre a tarefa `submit` e a
    # tarefa `sensor`. Isso significa que a tarefa `sensor` só começará a ser executada
    # após a tarefa `submit` for concluída com sucesso.
    submit >> sensor
    # [FIM task_sequence]


# [FIM dag]
