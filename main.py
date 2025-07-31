import os
import sys
from io import StringIO
from typing import Optional, List
import pandas as pd
import google.generativeai as genai
from dotenv import load_dotenv
from rich.console import Console
from rich.syntax import Syntax
from rich.prompt import Prompt, Confirm
from sqlalchemy import create_engine, inspect, Engine
from prompt_template import PROMPT_TEXT

class DataChatbot:

    def __init__(self):
        self.console = Console()
        self.model = self._initialize_model()
        self.df: Optional[pd.DataFrame] = None
        self.engine: Optional[Engine] = None
        self.data_source_name: Optional[str] = None
        self.history: List[str] = []

    def _initialize_model(self) -> Optional[genai.GenerativeModel]:
        load_dotenv()
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            self.console.print("[bold red]Erro: GOOGLE_API_KEY não encontrada no arquivo .env.[/bold red]")
            sys.exit(1)
        try:
            genai.configure(api_key=api_key)
            return genai.GenerativeModel('gemini-2.5-pro')
        except Exception as e:
            self.console.print(f"[bold red]Erro ao inicializar a API: {e}[/bold red]")
            sys.exit(1)

    # --- BANCO DE DADOS ---
    def _connect_to_db(self) -> bool:
        load_dotenv()
        db_url = os.getenv("DATABASE_URL")

        if not db_url:
            self.console.print("[bold red]Erro: DATABASE_URL não encontrada no arquivo .env.[/bold red]")
            return False

        try:
            self.console.print(f"[cyan]Conectando ao banco de dados...[/cyan]")
            self.engine = create_engine(db_url)
            with self.engine.connect() as connection:
                pass
            self.console.print("[green]Conexão estabelecida com sucesso![/green]")
            return True
        except Exception as e:
            self.console.print(f"[bold red]Erro ao conectar ao banco de dados: {e}[/bold red]")
            self.engine = None
            return False

    def _run_database_workflow(self):
        self.console.print("\n[bold cyan]-- Fluxo de Trabalho: Banco de Dados --[/bold cyan]")
        if not self._connect_to_db():
            return

        try:
            inspector = inspect(self.engine)
            table_names = inspector.get_table_names()
            if not table_names:
                self.console.print("[yellow]Nenhuma tabela encontrada no banco de dados.[/yellow]")
                return

            self.console.print("\n[bold]Tabelas disponíveis:[/bold]")
            for name in table_names: self.console.print(f"- {name}")

            chosen_table = Prompt.ask("\nDigite o nome da tabela para analisar", choices=table_names, show_choices=False)
            self.df = pd.read_sql_table(chosen_table, self.engine)
            self.data_source_name = f"da tabela de banco de dados '{chosen_table}'"
        except Exception as e:
            self.console.print(f"[red]Erro ao carregar dados do banco: {e}[/red]")
            self.df = None

    # --- ARQUIVO LOCAL ---
    def _run_file_workflow(self):
        self.console.print("\n[bold cyan]-- Fluxo de Trabalho: Arquivo Local --[/bold cyan]")
        data_dir = "data"
        if not os.path.exists(data_dir):
            self.console.print(f"[yellow]O diretório '{data_dir}/' não foi encontrado. Por favor, crie-o.[/yellow]")
            return

        files = [f for f in os.listdir(data_dir) if f.lower().endswith(('.csv', '.xlsx', '.xls'))]
        if not files:
            self.console.print(f"[yellow]Nenhum arquivo .csv ou .xlsx encontrado em '{data_dir}/'.[/yellow]")
            return

        self.console.print("\n[bold]Arquivos disponíveis em 'data/':[/bold]")
        for name in files: self.console.print(f"- {name}")

        chosen_file = Prompt.ask("\nDigite o nome do arquivo para analisar", choices=files, show_choices=False)
        full_path = os.path.join(data_dir, chosen_file)
        self._load_file_as_dataframe(full_path)
        self.data_source_name = f"do arquivo local '{chosen_file}'"

    def _load_file_as_dataframe(self, file_path: str):
        try:
            if file_path.lower().endswith('.csv'):
                self.df = pd.read_csv(file_path)
            elif file_path.lower().endswith(('.xlsx', '.xls')):
                self.df = pd.read_excel(file_path)
            else:
                self.console.print("[yellow]Formato de arquivo inválido.[/yellow]")
                self.df = None
        except FileNotFoundError:
            self.console.print(f"[red]Erro: Arquivo não encontrado em '{file_path}'[/red]")
            self.df = None
        except Exception as e:
            self.console.print(f"[red]Erro ao ler o arquivo: {e}[/red]")
            self.df = None

    # --- LÓGICA PRINCIPAL DO CHATBOT ---
    def _generate_code(self, question: str) -> Optional[str]:
        if self.df is None: return None
        self.console.print("[cyan]Analisando pergunta...[/cyan]")

        with StringIO() as buffer:
            self.df.info(buf=buffer)
            df_info = buffer.getvalue()

        prompt_context = f"O DataFrame 'df' foi carregado a partir {self.data_source_name}."

        prompt = PROMPT_TEXT.format(
            columns=", ".join(self.df.columns),
            df_info=df_info,
            df_head=self.df.head().to_string(),
            question=f"{prompt_context}\n\nPergunta: {question}"
        )

        try:
            generation_config = genai.types.GenerationConfig(temperature=0.0)
            response = self.model.generate_content(prompt, generation_config=generation_config)
            return response.text.replace("```python", "").replace("```", "").strip()
        except Exception as e:
            self.console.print(f"[red]Erro na chamada da API: {e}[/red]")
            return None

    def _execute_code(self, code: str):
        self.console.print(Syntax(code, "python", theme="monokai", line_numbers=True))
        if Confirm.ask("[bold]Executar este código?[/bold]"):
            self.console.print("[bold cyan]-- Resultado --[/bold cyan]")
            try:
                exec(code, {'df': self.df, 'pd': pd, 'print': self.console.print})
            except Exception as e:
                self.console.print(f"[bold red]Erro na execução do código: {e}[/bold red]")
            self.console.print("[bold cyan]---------------[/bold cyan]")
        else:
            self.console.print("[yellow]Execução cancelada.[/yellow]")

    def run(self):
        self.console.print("[bold]-----Chatbot de Análise de Dados-----[/bold]")

        choice = Prompt.ask(
            "De onde você quer carregar os dados?\n  [1] Banco de Dados\n  [2] Arquivo Local\n",
            choices=["1", "2"],
            default="1"
        )

        if choice == '1':
            self._run_database_workflow()
        elif choice == '2':
            self._run_file_workflow()

        if self.df is None:
            self.console.print("[red]Nenhum dado foi carregado. Encerrando o programa.[/red]")
            sys.exit(1)

        self.console.print(f"\n[green]Dados carregados com sucesso! Colunas: {', '.join(self.df.columns)}[/green]")
        self.console.print("Faça suas perguntas. Digite 'historico' para ver suas pesquisas ou 'sair' para terminar.")

        while True:
            question = Prompt.ask(">")
            if question.lower() == 'sair':
                break

            if question.lower() == 'historico':
                self.console.print("\n[bold cyan]-- Histórico de Pesquisas --[/bold cyan]")
                if not self.history:
                    self.console.print("Nenhuma pesquisa feita ainda.")
                else:
                    for i, item in enumerate(self.history, 1):
                        self.console.print(f"{i}. {item}")
                self.console.print("[bold cyan]---------------------------[/bold cyan]")
                continue
            self.history.append(question)

            generated_code = self._generate_code(question)
            if generated_code:
                self._execute_code(generated_code)

        self.console.print("Flww! Até a próxima!")

if __name__ == "__main__":
    bot = DataChatbot()
    bot.run()