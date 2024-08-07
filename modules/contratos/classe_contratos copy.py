





    def excluir_database(self):
        reply = QMessageBox.question(self, 'Confirmar Exclusão', 'Tem certeza que deseja excluir a tabela controle_contratos?', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.database_manager.execute_query("DROP TABLE IF EXISTS controle_contratos")
                QMessageBox.information(self, "Sucesso", "Tabela controle_contratos excluída com sucesso.")
                self.refresh_model()
            except Exception as e:
                QMessageBox.warning(self, "Erro ao excluir", f"Erro ao excluir a tabela: {str(e)}")


    def carregar_tabela(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Abrir arquivo de tabela", "", "Tabelas (*.xlsx *.xls *.ods *.csv)")
        if filepath:
            try:
                if filepath.endswith('.csv'):
                    df = pd.read_csv(filepath)
                else:
                    df = pd.read_excel(filepath)
                self.validate_and_process_data(df)
                df['status'] = 'Minuta'

                with self.database_manager as conn:
                    DatabaseContratosManager.create_table_controle_contratos(conn)

                self.database_manager.save_dataframe(df, 'controle_contratos')
                Dialogs.info(self, "Carregamento concluído", "Dados carregados com sucesso.")
            except Exception as e:
                logging.error("Erro ao carregar tabela: %s", e)
                Dialogs.warning(self, "Erro ao carregar", str(e))

    def validate_and_process_data(self, df):
        try:
            self.validate_columns(df)
            self.add_missing_columns(df)
            self.salvar_detalhes_uasg_sigla_nome(df)
        except ValueError as e:
            Dialogs.warning(self, "Erro de Validação", str(e))
        except Exception as e:
            Dialogs.error(self, "Erro Inesperado", str(e))

    def validate_columns(self, df):
        missing_columns = [col for col in self.required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Colunas obrigatórias faltando: {', '.join(missing_columns)}")

    def add_missing_columns(self, df):
        for col in self.required_columns:
            if col not in df.columns:
                df[col] = ""

    def salvar_detalhes_uasg_sigla_nome(self, df):
        with sqlite3.connect(self.database_om_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT uasg, sigla_om, orgao_responsavel FROM controle_om")
            om_details = {row[0]: {'sigla_om': row[1], 'orgao_responsavel': row[2]} for row in cursor.fetchall()}
        df['sigla_om'] = df['uasg'].map(lambda x: om_details.get(x, {}).get('sigla_om', ''))
        df['orgao_responsavel'] = df['uasg'].map(lambda x: om_details.get(x, {}).get('orgao_responsavel', ''))