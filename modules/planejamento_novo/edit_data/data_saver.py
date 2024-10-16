class DataSaver:
    def __init__(self, database_manager, df_registro_selecionado):
        self.database_manager = database_manager
        self.df_registro_selecionado = df_registro_selecionado

    def save_changes(self, data):
        try:
            # Atualizar o DataFrame com os novos valores
            for key, value in data.items():
                # Check if the DataFrame column is of type int64 and the value is boolean
                if self.df_registro_selecionado[key].dtype == 'int64' and isinstance(value, bool):
                    value = int(value)
                self.df_registro_selecionado.at[self.df_registro_selecionado.index[0], key] = value

            # Atualizar banco de dados
            self.update_database(data)

        except Exception as e:
            raise Exception(f"Ocorreu um erro ao salvar as alterações: {str(e)}")


    def update_database(self, data):
        try:
            with self.database_manager as connection:
                cursor = connection.cursor()

                # Get available columns
                available_columns = self.get_available_columns(cursor)

                # Filter data to include only columns that exist in the database
                filtered_data = {key: value for key, value in data.items() if key in available_columns}

                # Build the SQL query
                set_part = ', '.join([f"{key} = ?" for key in filtered_data.keys()])
                valores = list(filtered_data.values())
                valores.append(self.df_registro_selecionado['id_processo'].iloc[0])

                query = f"UPDATE controle_processos SET {set_part} WHERE id_processo = ?"
                cursor.execute(query, valores)
                connection.commit()

        except Exception as e:
            raise Exception(f"Erro ao atualizar o banco de dados: {str(e)}")

    def get_available_columns(self, cursor):
        cursor.execute("PRAGMA table_info(controle_processos)")
        columns_info = cursor.fetchall()
        return [col[1] for col in columns_info]
