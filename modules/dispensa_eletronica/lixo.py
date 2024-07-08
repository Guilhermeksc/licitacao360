    def fill_frame4(self):
        self.frame4.setObjectName("fill_frame4")
        self.frame4.setStyleSheet("#fill_frame4 { background-color: #050f41; }")

        self.frame4_group_box_layout = QHBoxLayout()
        self.frame4.setLayout(self.frame4_group_box_layout)

        self.frame4.setFixedWidth(1505)
        self.frame4.setFixedHeight(340)

        self.frame4_layout.setContentsMargins(0, 0, 0, 0)
        self.frame4_layout.addLayout(self.frame4_group_box_layout)

        self.frame4_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        self.update_frame4_content()

    def update_frame4_content(self):
        for i in reversed(range(self.frame4_group_box_layout.count())):
            widget_to_remove = self.frame4_group_box_layout.itemAt(i).widget()
            if widget_to_remove is not None:
                widget_to_remove.setParent(None)


        if self.selected_tooltip == " Autorização para abertura do processo de Dispensa Eletrônica":
            # Adiciona o texto central específico
            authorization_text = """
                Instruções<br><br>
                Após aprovado pelo Ordenador de Despesas a situação deverá ser alterada de "Planejamento" para <span style="color: red;">"Aprovado"</span><br><br>
                Após publicado no PNCP a situação deverá ser alterada de "Aprovado" para <span style="color: red;">"Sessão Pública"</span><br><br>
                Após a homologação situação deverá ser alterada de "Sessão Pública" para <span style="color: red;">"Homologado"</span><br><br>
                Após a o empenho a situação deverá ser alterada de "Homologado" para <span style="color: red;">"Concluído"</span>
            """
            text_edit = QTextEdit()
            text_edit.setReadOnly(True)
            text_edit.setHtml(authorization_text)
            text_edit.setStyleSheet("background-color: #050f41; color: white; font-size: 12pt;")
            painel_layout.addWidget(text_edit)
        elif self.selected_tooltip == "Documentos de Planejamento (CP, DFD, TR, etc.)":
            document_details_widget = DocumentDetailsWidget(self.df_registro_selecionado, self)
            painel_layout.addWidget(document_details_widget)
        elif self.selected_tooltip == "Aviso de dispensa eletrônica":
            pass
        elif self.selected_tooltip == "Lista de Verificação":
            pass

        self.carregarAgentesResponsaveis()
        self.setupGrupoSIGDEM(layout_direita)
