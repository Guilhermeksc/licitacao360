import sys
import os
import subprocess
from openai import OpenAI
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLineEdit, QPushButton, QLabel
from config import API_KEY  # Importe a configuração da API_KEY

# Configure sua chave API da OpenAI aqui
client = OpenAI(api_key=API_KEY)

class QuestionAnswerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Layout vertical
        layout = QVBoxLayout()

        # Campo de entrada para a primeira parte da pergunta
        self.question_input1 = QLineEdit(self)
        self.question_input1.setPlaceholderText("Digite o material ou serviço desejado...")
        layout.addWidget(self.question_input1)

        # Botão para gerar resposta
        self.answer_button = QPushButton('Obter Resposta', self)
        self.answer_button.clicked.connect(self.show_answer)
        layout.addWidget(self.answer_button)

        # Label para mostrar a resposta
        self.answer_label = QLabel('')
        layout.addWidget(self.answer_label)

        self.setLayout(layout)
        self.setWindowTitle('Consulta de Contratações Públicas')
        self.setGeometry(300, 300, 400, 200)


    def show_answer(self):
        # Pegar a pergunta do usuário
        user_input1 = self.question_input1.text()
        # user_input2 = self.question_input2.text()

        context = """
No planejamento de uma contratação pública, a descrição da necessidade de contratação deve ser meticulosamente delineada para assegurar alinhamento com o interesse público e deve:

Identificar claramente o problema e sua relevância para a continudade do serviço público.
Avaliar os possíveis impatado e como eles ocorrem.
Projetar as consequências de não resolver o problema.
Integrar soluções que abordem tanto as necessidades imediatas quanto estratégicas.
Além disso, é vital que o processo de contratação demonstre um compromisso com o planejamento cuidadoso e a excelência na gestão.

O Centro de Intendência da Marinha em Brasília (CeIMBra) é o órgão responsável pelo planejamento e centralização das demandas das seguintes organizações militares apoiadas:

COMANDO DO 7º DISTRITO NAVAL (Com7ºDN) - UASG 787000
CAPITANIA FLUVIAL DE ARAGUAIA-TOCANTINS (CFAT) - UASG 787310
CAPITANIA FLUVIAL DE BRASÍLIA (CFB) - UASG 787320
GRUPAMENTO DE FUZILEIROS NAVAIS DE BRASÍLIA (GptFNB) - UASG 787200
CENTRO DE INSTRUÇÃO E ADESTRAMENTO DE BRASÍLIA (CIAB) - UASG 787900
ESTAÇÃO RÁDIO DA MARINHA EM BRASÍLIA (ERMB) - UASG 787400
CAPITANIA FLUVIAL DE GOIÁS (CFGO) - UASG 787330
HOSPITAL NAVAL DE BRASÍLIA (HNBRA) - UASG 787700
Alem dessas organizações, outras organizações também são participantes das licitações realizadas pelo CeIMBra.

No planejamento da contratação deve ser considerado que as demandas serão para as organizações militares da Marinha do Brasil, localizadas na cidade de Brasília-DF.
"""

        # Formatar a pergunta com o contexto
        formatted_question = f"""
A identificação da necessidade da contratação é o primeiro aspecto a ser abordado em um estudo técnico preliminar, justamente para permitir a reflexão sobre os motivos pelos quais determinada contratação foi solicitada, investigando assim qual a necessidade final a ser atendida, que pode inclusive ser distinta a depender da finalidade do órgão ou entidade, ainda que o objeto indicado pelo setor requisitante seja o mesmo.
Essa investigação inicial é expressamente demandada no art. 18, I e §1º, I da NLLC, já reproduzidos no presente parecer. Trata-se de etapa fundamental do processo, por meio da qual o problema colocado para a Administração pode vir a ser compreendido sob outra perspectiva e assim contribuir para que outras soluções se mostrem propícias a atender a demanda, quando se passar à fase de levantamento de mercado, tratada mais à frente. A clareza da necessidade administrativa é a base para possíveis inovações.
Também por meio dela é possível fazer uma reflexão para extrair quais os requisitos essenciais sem os quais a necessidade não seria atendida. Trata-se de requisitos da própria necessidade, portanto, e não de eventuais soluções a serem adotadas, até porque, nessa primeira etapa, ainda não se sabe quais as soluções disponíveis. Nesse sentido, o art. 18, §1º da Lei n. 14.133, de 2022, que estabelece os elementos do ETP, prevê os requisitos da contratação no seu inciso III, enquanto o levantamento de mercado (quando se buscam as soluções disponíveis) somente no inciso V.
Além disso, a descrição da necessidade de contratação deve conter manifestação acerca da essencialidade e interesse público da contratação, para os fins do previsto no art. 3º do Decreto nº 8.540/2015, a ser interpretado em consonância com a Lei n. 14.133, de 2022, devendo portanto ser avaliado o interesse público também na perspectiva de se haverá impacto ambiental negativo decorrente da contratação e se há opções que atendam ao princípio do desenvolvimento nacional sustentável, considerando o ciclo de vida do objeto (artigo 11, I, Lei n. 14.133, de 2021)
    Desenvolva uma Descrição Detalhada da Necessidade para justificar uma contratação de {user_input1}

    Inclua na sua descrição:
    - Uma análise detalhada do impacto específico do problema no serviço público prestado pelas forças armadas, identificando as áreas críticas afetadas.
    - Uma discussão sobre as consequências potenciais para a operação e a eficiência dos serviços se o problema não for resolvido, incluindo impactos a longo prazo.
    - Uma lista exemplificativa e análise crítica dos possíveis itens a serem adquiridos. Explique como cada item contribui para resolver os problemas identificados, e avalie sua relevância e eficácia em relação aos objetivos estratégicos e operacionais. Essa análise deve considerar não apenas a adequação técnica, mas também a viabilidade econômica e a sustentabilidade.
    - Explique como essas necessidades alinham-se com o interesse público e como a contratação contribuirá para os objetivos do Centro de Intendência da Marinha em Brasília (CeIMBra) e das organizações militares apoiadas.

    O texto deve ser em parágrafos, sem tópicos e deve ser articulado, claro e abrangente, variando entre 25 a 35 linhas, que ofereça uma perspectiva completa sobre as necessidades e soluções propostas.
    """

        # Chamar a nova API da OpenAI para obter a resposta
        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": context},  # Contexto enviado como mensagem de sistema
                    {"role": "user", "content": formatted_question}  # Pergunta do usuário
                ],
                model="gpt-3.5-turbo"
            )
            #gpt-3.5-turbo gpt-4-turbo
            # Imprimir a estrutura completa para diagnóstico
            print(chat_completion)
            
            # Processar a resposta inicial
            if chat_completion.choices:
                first_choice = chat_completion.choices[0]
                initial_answer = first_choice.message.content if hasattr(first_choice, 'message') and hasattr(first_choice.message, 'content') else "Resposta não encontrada na estrutura esperada."
            else:
                initial_answer = "Não foi possível obter uma resposta."

            self.answer_label.setText(initial_answer)

            # Segunda pergunta sobre o órgão responsável
            follow_up_question = "Qual é objeto a ser contratado e quais os benefícios obtidos com essa contratação?"

            # Atualizar o contexto incluindo a resposta inicial
            updated_context = context + "\n" + initial_answer

            # Segunda chamada à API para obter a resposta seguindo o contexto atualizado
            follow_up_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": updated_context},
                    {"role": "user", "content": follow_up_question}
                ],
                model="gpt-3.5-turbo"
            )

            # Processar a resposta de acompanhamento
            if follow_up_completion.choices:
                second_choice = follow_up_completion.choices[0]
                follow_up_answer = second_choice.message.content if hasattr(second_choice, 'message') and hasattr(second_choice.message, 'content') else "Resposta não encontrada na estrutura esperada."
            else:
                follow_up_answer = "Não foi possível obter uma resposta."

            # Exibir a resposta de acompanhamento
            print(follow_up_answer)  # Mostrar no console ou manejar conforme necessário

            # Terceira pergunta sobre a Descrição da Solução como todo
            follow_up_question_2 = f"""
Crie um texto em parágrafos, sem tópicos que deve ser articulado, claro e abrangente, variando entre 25 a 30 linhas, que identifique a melhor solução para a contratação de {user_input1}, visando o interesse público.

Pregão Eletrônico por Registro de Preços consiste em um conjunto de procedimentos para registro formal de preços relativos à prestação de serviços e aquisição de bens,para contratações futuras. Ou seja, uma modalidade de cotação que pode, ou não, gerar uma contratação em seguida. O sistema é
utilizado quando a Administração possui incertezas quanto às quantidades e quanto ao momento em que vai adquirir o produto e, conforme o artigo 3º do decreto nº 11.462/2023 poderá ser adotado nas seguintes hipóteses:

Inciso I - quando, pelas características do objeto, houver necessidade de contratações permanentes ou frequentes;
Inciso II - quando for conveniente a aquisição de bens com previsão de entregas parceladas;
Inciso III - quando for conveniente para atendimento a mais de um órgão ou a mais de uma entidade, inclusive nas compras centralizadas, aumentando o potencial de economia da licitação;
Inciso V - quando, pela natureza do objeto, não for possível definir previamente o quantitativo a ser demandado pela Administração.

Na solução deverá contextualizar que o inciso III foi atendido, contextualize também outra hipoteses prevista nos Incisos I, II ou V do artigo 3º do decreto nº 11.462/2023.

Conclua que o registro de preço é a melhor solução para o objeto a ser contratado e que todos os demais elementos necessários ao atendimento à demanda da Administração estarão dispostos no Termo de Referência, entre eles as obrigações e responsabilidades da contratada e demais especificidades do objeto.
"""
            # # Atualizar o contexto incluindo a resposta inicial
            # updated_context= context + "\n" + initial_answer + "\n" + follow_up_answer

            # Terceira chamada à API para obter a resposta seguindo o contexto atualizado
            follow_up_completion_2 = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": updated_context},
                    {"role": "user", "content": follow_up_question_2}
                ],
                model="gpt-3.5-turbo"
            )

            # Processar a resposta de acompanhamento
            if follow_up_completion_2.choices:
                third_choice = follow_up_completion_2.choices[0]
                follow_up_answer_2 = third_choice.message.content if hasattr(third_choice, 'message') and hasattr(third_choice.message, 'content') else "Resposta não encontrada na estrutura esperada."
            else:
                follow_up_answer_2 = "Não foi possível obter uma resposta."

            # Exibir a resposta de acompanhamento
            print(follow_up_answer_2)  # Mostrar no console ou manejar conforme necessário

            # Terceira pergunta sobre a Descrição da Solução como todo
            follow_up_question_3 = f"""
Uma vez identificada a necessidade administrativa, o próximo passo é buscar soluções que tenham o potencial de atendê-la. Não se trata, portanto, de realizar estimativa de preços, e sim estudar as práticas do mercado e de outros órgãos e entidades públicas, a fim de verificar se existe alguma outra solução para atender a necessidade administrativa ou então novas metodologias de execução/contratação que gerem ganhos de produtividade ou economia para a Administração.
Já o art. 44 da Lei nº 14.133, de 2021, determina que a Administração promova a avaliação dos custos e benefícios das opções de compra e locação de bens, quando ambas as soluções foram viáveis, de modo a indicar a alternativa que se revelou mais vantajosa no caso concreto. Neste ponto, ressalte-se que a vantajosidade deve considerar o ciclo de vida do objeto, nos termos dos artigos 11, I e 18, VIII, da mesma lei.
Assim, essa prospecção e avaliação deverá ser realizada, ainda que leve à conclusão de que as metodologias já tradicionalmente empregadas em contratações anteriores são as mais aptas à satisfação da necessidade administrativa. Seja qual for a solução adotada, sua escolha deve ser expressamente motivada nos autos.

Gere um texto detalhado descrevendo o procedimento de levantamento de mercado para a aquisição de {user_input1}.
O texto deve ser em parágrafos, sem tópicos e deve ser articulado, claro e abrangente, variando entre 25 a 35 linhas e deve abranger todos os aspectos essenciais do levantamento de mercado, incluindo a compatibilidade entre os requisitos propostos pela área demandante e as soluções disponíveis no mercado.
Destaque que, após consultas ao histórico de aquisições e a sítios de internet, foi verificado que existe uma grande oferta de empresas capazes de fornecer os itens requeridos, o que sugere uma competição acirrada e preços mais baixos.
Ressalte também que, por ser uma demanda de material comum e não complexa, não foram identificados obstáculos para a participação de microempresas e empresas de pequeno porte (ME/EPP).
Adicionalmente, mencione que no levantamento foram consideradas as licitações realizadas pelo Comando do 7º Distrito Naval (Com7ºDN) e por outras organizações militares da Marinha, com o objetivo de identificar novas metodologias, tecnologias ou inovações que possam melhor atender às necessidades da Administração.
O texto deve enfatizar a importância de um levantamento de mercado eficaz para evitar direcionamento ou conluio e garantir a transparência e eficácia do processo de aquisição.

busca por soluções de mercado, não tendo justificado, entretanto, recomendando-se que o faça, o que pode inclusive alterar o próprio objeto licitatório, em se encontrando uma solução mais adequada à necessidade administrativa.
"""
            # # Atualizar o contexto incluindo a resposta inicial
            # updated_context= context + "\n" + initial_answer + "\n" + follow_up_answer

            # Terceira chamada à API para obter a resposta seguindo o contexto atualizado
            follow_up_question_3 = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": updated_context},
                    {"role": "user", "content": follow_up_question_3}
                ],
                model="gpt-3.5-turbo"
            )

            # Processar a resposta de acompanhamento
            if follow_up_question_3.choices:
                choice_4 = follow_up_question_3.choices[0]
                follow_up_answer_3 = choice_4.message.content if hasattr(choice_4, 'message') and hasattr(choice_4.message, 'content') else "Resposta não encontrada na estrutura esperada."
            else:
                follow_up_answer_3 = "Não foi possível obter uma resposta."

            # Exibir a resposta de acompanhamento
            print(follow_up_answer_3)  # Mostrar no console ou manejar conforme necessário

            follow_up_question_4 = f"""
Gere um texto detalhado que justifique o parcelamento ou não da solução em uma aquisição de {user_input1}.
O texto deve ser em parágrafos, sem tópicos e deve ser articulado, claro e abrangente, variando entre 25 a 35 linhas e deve discutir tecnicamente a viabilidade e as vantagens econômicas do parcelamento, conforme estabelecido na alínea b do inciso V do artigo 40 da Lei 14.133/2021, que orienta o parcelamento quando tecnicamente viável e economicamente vantajoso.
Destaque que, apesar da equipe de planejamento ter considerado a possibilidade de agrupar os itens em lotes para tornar o processo mais atrativo para as empresas, limitações da plataforma comprasnet e da legislação vigente tornaram inviável o agrupamento por grupos. Assim, concluiu-se que o parcelamento por itens individuais é mais vantajoso e operacionalizável.
Inclua no texto que a licitação foi estruturada de modo a atender um nicho de mercado específico, e que, portanto, não é necessária mais de uma licitação para a solução escolhida.
Adicionalmente, o texto deve afirmar que:
O mercado fornecedor tem plena capacidade de atender à demanda.
A contratação é técnica e economicamente viável.
O parcelamento dos itens não resultará em perda de economia de escala.
Na especificação dos itens, foram tomados cuidados para maximizar a amplitude de mercado e a competitividade.
Finalmente, cite a Súmula nº 247 do TCU, que obriga a admissão da adjudicação por item e não por preço global em licitações divisíveis, para reforçar a justificativa legal e prática do parcelamento.
"""
            # # Atualizar o contexto incluindo a resposta inicial
            # updated_context= context + "\n" + initial_answer + "\n" + follow_up_answer

            # Terceira chamada à API para obter a resposta seguindo o contexto atualizado
            follow_up_question_4 = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": updated_context},
                    {"role": "user", "content": follow_up_question_4}
                ],
                model="gpt-3.5-turbo"
            )

            # Processar a resposta de acompanhamento
            if follow_up_question_4.choices:
                choice_5 = follow_up_question_4.choices[0]
                follow_up_answer_4 = choice_5.message.content if hasattr(choice_5, 'message') and hasattr(choice_5.message, 'content') else "Resposta não encontrada na estrutura esperada."
            else:
                follow_up_answer_4 = "Não foi possível obter uma resposta."

            # Exibir a resposta de acompanhamento
            print(follow_up_answer_4)  # Mostrar no console ou manejar conforme necessário

            # Salvar as respostas no arquivo de bloco de notas
            with open("response.txt", "w", encoding='utf-8') as file:
                file.write("Descrição da Necessidade da Contratação" + "\n\n" + initial_answer + "\n\n" + "Levantamento de Mercado" + "\n\n" + follow_up_answer_3 + "\n\n" + "Benefícios a Serem Alcançados" + "\n\n" + follow_up_answer + "\n\n" + "Descrição da Solução como um todo" + "\n\n" + follow_up_answer_2 + "\n\n" + "Justificativa para o Parcelamento ou não da Solução" + "\n\n" + follow_up_answer_4)  # Adicionar ambas as respostas ao arquivo

            # Abrir o arquivo de bloco de notas
            if sys.platform == "win32":
                os.startfile("response.txt")
            else:
                subprocess.call(["open", "response.txt"])

        except Exception as e:
            error_message = f"Erro: {str(e)}"
            print(error_message)
            self.answer_label.setText(error_message)

# Executar a aplicação
def main():
    app = QApplication(sys.argv)
    ex = QuestionAnswerApp()
    ex.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()