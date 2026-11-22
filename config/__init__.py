# PyMySQL працює як заміна mysqlclient (не потребує компіляції, підходить для будь-якої версії Python).
try:
    import MySQLdb  # noqa: F401  — якщо встановлено mysqlclient, використовуємо його
except ImportError:
    import pymysql

    pymysql.install_as_MySQLdb()
