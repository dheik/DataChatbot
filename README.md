# DataChatbot: Assistente de Análise de Dados com IA

## 📖 Sobre o Projeto

O **DataChatbot** é uma aplicação de linha de comando desenvolvida em Python que atua como uma ponte inteligente entre a linguagem humana e a análise de dados técnica. A ferramenta permite que utilizadores façam perguntas em português sobre um conjunto de dados e, utilizando o poder do modelo de linguagem **Google Gemini**, traduz essas perguntas em código Python/Pandas executável.

O objetivo principal é democratizar o acesso a insights e acelerar o fluxo de trabalho de análise, permitindo que tanto utilizadores técnicos quanto não-técnicos possam "conversar" com os seus dados.

---

## ✨ Funcionalidades Principais

* **Tradução de Linguagem Natural:** Converte perguntas complexas em código Pandas preciso.
* **Conectividade Híbrida:** Suporta a ingestão de dados de duas fontes distintas:
    * Bancos de dados **PostgreSQL** robustos e escaláveis.
    * Ficheiros locais como **CSV** e **Excel** para exploração rápida.
* **Execução Segura:** Apresenta todo o código gerado pela IA para revisão e exige confirmação explícita do utilizador antes de o executar.
* **Interface Interativa:** Utiliza a biblioteca `rich` para fornecer uma experiência de utilizador clara, colorida e amigável no terminal.
* **Motor de IA de Ponta:** Integrado com a API do **gemini-2.5-pro** para garantir a melhor interpretação de contexto e geração de código.

---

## 🛠️ Tecnologias Utilizadas

Este projeto foi construído utilizando um conjunto de tecnologias modernas e padrão de mercado no ecossistema Python:

* **Linguagem:** Python 3.x
* **Análise de Dados:** Pandas
* **Inteligência Artificial:** Google Gemini API (`google-generativeai`)
* **Banco de Dados:** PostgreSQL
* **Conexão com BD:** SQLAlchemy & Psycopg2
* **Interface de Terminal:** Rich
* **Gestão de Segredos:** Python-dotenv

---

## 🚀 Instalação e Configuração

Siga os passos abaixo para executar o projeto localmente.

### Pré-requisitos

* Python 3.8 ou superior
* Um servidor PostgreSQL instalado e em execução

### 1. Clonar o Repositórios

git clone [https://github.com/dheik/DataChatbot.git](https://github.com/dheik/DataChatbot.git)
cd DataChatbot

### 2. Criar um Ambiente Virtual e Instalar as Dependências

#### Criar o ambiente virtual
python -m venv .venv

##### Ativar o ambiente virtual
 No Windows:
.venv\Scripts\activate
No macOS/Linux:
source .venv/bin/activate

#### Instalar as bibliotecas necessárias
pip install -r requirements.txt

### 3. Configurar as Variáveis de Ambiente

Crie um ficheiro chamado .env na raiz do projeto. Este ficheiro guardará as suas credenciais de forma segura.
#### No ficheiro .env
GOOGLE_API_KEY="sua_chave_secreta_do_google_aqui"
DATABASE_URL="postgresql://seu_usuario:sua_senha@localhost:5432/nome_do_seu_banco"

Substitua os valores pelos seus dados reais.

### 4. Configurar o Banco de Dados (Opcional)

Para testar a funcionalidade completa com o PostgreSQL, certifique-se de que o seu banco de dados e as suas tabelas estão criados. O chatbot irá listar as tabelas disponíveis para análise.

### 🏃 Como Usar
Com o ambiente configurado, execute o chatbot a partir do seu terminal:
python chatbot_final.py

O programa irá cumprimentá-lo e perguntar de onde deseja carregar os dados. Siga as instruções no ecrã e comece a fazer as suas perguntas!

### 🧠 Aprendizados e Desafios
Este projeto foi de grande aprendizagem para mim, com muitos desafios e horas de persistência. A maior complexidade não estava em um único algoritmo, mas na arquitetura do código em si: orquestrar bibliotecas distintas como o Pandas e a API do Gemini, garantindo que a saída de uma servisse como a entrada correta para a outra. Desenvolver a lógica para gerar e executar código dinamicamente de forma segura, usando exec(), foi um desafio particular que testou a minha resiliência. Essa jornada ensinou-me a pensar como um engenheiro de software, focando em criar um código modular e robusto, e a arte do "prompt engineering" para instruir a IA a gerar saídas precisas e funcionais.

### 🔮 Melhorias Futuras
[ ] Criar uma interface web com Flask ou FastAPI.

[ ] Suporte para visualização de dados (gerar gráficos com Matplotlib/Seaborn).

[ ] Capacidade de analisar múltiplas tabelas e realizar joins.

[ ] Implementar um sistema de cache para perguntas frequentes.

### 📄 Licença
Este projeto está sob a licença MIT. Veja o ficheiro LICENSE para mais detalhes.
