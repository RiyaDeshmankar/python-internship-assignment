try:
    import pymysql

    pymysql.install_as_MySQLdb()
except ModuleNotFoundError:
    # PyMySQL will be available after installing requirements.
    pass
