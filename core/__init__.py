
import os

if not os.getenv("DATABASE_URL"):
    import pymysql
    pymysql.install_as_MySQLdb()