from database import get_connection

try:
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT codigo, nome FROM estacoes ORDER BY id;")
            estacoes = cursor.fetchall()

            print("Conexão com o banco funcionando!")
            print("Estações cadastradas:")

            for estacao in estacoes:
                print(estacao)

except Exception as erro:
    print("Erro ao conectar no banco:")
    print(erro)