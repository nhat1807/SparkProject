import sys
import uuid

from pyspark.sql.functions import *

from lib import configLoader, DataLoader, Utils, Transformations
from lib.logger import Log4j

if __name__ == "__main__":

    if len(sys.argv) < 3:
        print("Usage: sbdl {local, qa, prod} {load_date} : Arguments are missing")
        sys.exit(-1)

    job_run_env = sys.argv[1].upper()
    load_date = sys.argv[2]
    job_run_id = "SBDL-" + str(uuid.uuid4())

    print("Initializing SBDL Job in " + job_run_env + " Job ID: " + job_run_id)
    conf = configLoader.get_config(job_run_env)
    enable_hive = True if conf["enable_hive"] == 'true' else False
    hive_db = conf['hive.database']

    print("Creating Spark Session")
    spark = Utils.get_spark_session(job_run_env)

    logger = Log4j(spark)

    logger.info("Reading SBDL Account DF")
    account_df = DataLoader.read_account(spark, job_run_env, enable_hive, hive_db)
    contract_df = Transformations.get_contract(account_df)

    logger.info("Reading SBDL Party DF")
    party_df = DataLoader.read_parties(spark, job_run_env, enable_hive, hive_db)
    relations_df = Transformations.get_relations(party_df)

    logger.info('Reading SBDL Address DF')
    address_df = DataLoader.read_address(spark, job_run_env, enable_hive, hive_db)
    relation_address_df = Transformations.get_address(address_df)

    logger.info("Join Party Relations and Address")
    party_address_df = Transformations.join_party_address(relations_df, relation_address_df)

    logger.info("Join Account and Parties")
    data_df = Transformations.join_contract_party(contract_df, party_address_df)

    logger.info("Apply Header and create Event")
    final_df = Transformations.apply_header(spark, data_df)
    logger.info("Preparing to send data top Kafka")
    kafka_kv_df = final_df.select(col("payload.contractIdentifier").alias("key"),
                                  to_json(struct("*")).alias("value"))
    input("Press Any Key")
    



    logger.info("Finished creating Spark Session")
    logger.info("One more message")