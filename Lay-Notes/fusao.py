import tkinter as tk
from tkinter import filedialog, ttk, messagebox, Text, Toplevel
import pandas as pd
import xml.etree.ElementTree as ET
import ttkbootstrap as tb
from collections import defaultdict
import os
from datetime import datetime

# CLASSE 1: LÓGICA E INTERFACE DO VALIDADOR DE RATES

class RateValidatorApp:
    def __init__(self, parent_frame):
        self.parent = parent_frame
        # DataFrames para armazenar os dados
        self.master_df = pd.DataFrame()
        self.resultado_tam = pd.DataFrame()
        self.resultado_gol = pd.DataFrame()
        self.resultado_azul = pd.DataFrame()
        self.resultado_internacional = pd.DataFrame()
        
        self.create_widgets()

    def create_widgets(self):
        # --- Frame de Controles ---
        frame_controles = tb.Frame(self.parent, bootstyle="dark")
        frame_controles.pack(fill='x', padx=10, pady=(10,5))
        frame_controles.columnconfigure(1, weight=1)

        btn_selecionar = tb.Button(frame_controles, text="1. Processar Arquivos CSV", command=self.processar_arquivos, bootstyle="primary")
        btn_selecionar.grid(row=0, column=0, rowspan=2, sticky="ns", padx=(0, 15))
        
        tb.Label(frame_controles, text="Quartos já vistos (separados por vírgula ou quebra de linha):", anchor="w").grid(row=0, column=1, sticky="ew", pady=(0, 2))
        self.entry_quartos_vistos = Text(frame_controles, height=2, width=30, bg="#2a2a2a", fg="white", font=("Segoe UI", 9), bd=0, insertbackground="white")
        self.entry_quartos_vistos.grid(row=1, column=1, sticky="ew")
        
        btn_atualizar_cores = tb.Button(frame_controles, text="2. Atualizar", command=self.revalidar_dados, bootstyle="success")
        btn_atualizar_cores.grid(row=0, column=2, rowspan=2, sticky="ns", padx=(15, 5))
        
        btn_lista_status = tb.Button(frame_controles, text="Gerar Listas", command=self.gerar_listas_status, bootstyle="secondary")
        btn_lista_status.grid(row=0, column=3, rowspan=2, sticky="ns", padx=(5,0))
        
        self.chk_fim_de_semana_var = tk.BooleanVar()
        chk_fim_de_semana = tb.Checkbutton(frame_controles, text="Fim de Semana", variable=self.chk_fim_de_semana_var, bootstyle="info-round-toggle")
        chk_fim_de_semana.grid(row=0, column=4, rowspan=2, sticky="ns", padx=(15, 0))

        # --- Frame de Ordenação ---
        sort_frame = tb.Frame(self.parent)
        sort_frame.pack(fill='x', padx=10, pady=(5,0))
        tb.Label(sort_frame, text="Ordenar por:").pack(side='left', padx=(0, 5))
        self.sort_combo = tb.Combobox(
            sort_frame, 
            state="readonly", 
            values=["Nº do Quarto (Crescente)", "Status (Incorretos Primeiro)"]
        )
        self.sort_combo.current(0)
        self.sort_combo.pack(side='left', fill='x', expand=True)

        # --- Notebook com a nova aba ---
        notebook = tb.Notebook(self.parent)
        notebook.pack(expand=True, fill='both', padx=10, pady=10)
        abas = ['Tam / Latam', 'Gol', 'Azul', 'Internacional']
        self.tabelas = {}
        for nome in abas:
            aba = tb.Frame(notebook)
            notebook.add(aba, text=nome)
            self.tabelas[nome] = self._criar_tabela(aba)

    def _criar_tabela(self, parent_tab):
        frame = tb.Frame(parent_tab)
        frame.pack(fill='both', expand=True)
        cols = ["Room", "Adults", "Rate", "Status"]
        tabela = tb.Treeview(frame, columns=cols, show="headings", bootstyle="dark")
        
        tags = {'correto': '#32CD32', 'incorreto': '#FF4136', 'novo_correto': '#00FFFF', 'novo_incorreto': '#FFA500'}
        for tag, color in tags.items():
            tabela.tag_configure(tag, foreground=color)
        tabela.tag_configure('group_odd', background='#2a2a2a')
        tabela.tag_configure('group_even', background='#3c3c3c')

        for col in cols:
            tabela.heading(col, text=col)
            tabela.column(col, width=150, anchor="center")
        
        sb_y = tb.Scrollbar(frame, orient="vertical", command=tabela.yview, bootstyle="round")
        tabela.configure(yscrollcommand=sb_y.set)
        sb_y.pack(side='right', fill='y')
        tabela.pack(side='left', fill='both', expand=True)
        return tabela

    def validar_rate(self, df, single_rate, double_rate, is_weekend=False):
        if df.empty: return df
        df = df.copy()
        if 'Rate' not in df.columns or 'Room' not in df.columns or 'Adults' not in df.columns:
            messagebox.showerror("Erro de Coluna", "Colunas essenciais (Rate, Room, Adults) não encontradas.")
            return pd.DataFrame()

        df['Rate'] = pd.to_numeric(df['Rate'].astype(str).str.replace('R$', '', regex=False).str.strip(), errors='coerce').fillna(0)
        df['Room'] = df['Room'].str.strip()
        df['Adults'] = pd.to_numeric(df['Adults'], errors='coerce').fillna(0).astype(int)
        df['Status'] = "Incorreto"

        rate_para_validacao = single_rate if is_weekend else double_rate

        for _, group in df.groupby('Room'):
            indices = group.index
            count = len(group)
            
            if count == 1:
                row = group.iloc[0]
                if row['Adults'] == 1 and row['Rate'] == single_rate:
                    df.loc[indices, 'Status'] = "Correto"
            elif count > 1:
                main_res = group[(group['Adults'] == 2) & (group['Rate'] == rate_para_validacao)]
                shared_res = group[(group['Adults'] == 0) & (group['Rate'] == 0.00)]
                if len(main_res) == 1 and (len(main_res) + len(shared_res) == count):
                    df.loc[indices, 'Status'] = "Correto"
        return df

    def processar_arquivos(self):
        caminhos = filedialog.askopenfilenames(title="Selecione um ou mais arquivos CSV", filetypes=[("Arquivos CSV", "*.csv")])
        if not caminhos: return

        try:
            lista_dfs = []
            for c in caminhos:
                df = pd.read_csv(c, dtype={'Room': str}, on_bad_lines='skip')
                df.columns = df.columns.str.strip()
                lista_dfs.append(df)
            self.master_df = pd.concat(lista_dfs, ignore_index=True)
            
            if 'Company' not in self.master_df.columns or 'Rate Code' not in self.master_df.columns:
                messagebox.showerror("Erro de Coluna", "As colunas 'Company' e 'Rate Code' não foram encontradas no CSV.")
                self.master_df = pd.DataFrame()
                return
            
            messagebox.showinfo("Sucesso", f"{len(caminhos)} arquivo(s) carregado(s) com sucesso!")
            self.revalidar_dados()

        except Exception as e:
            self.master_df = pd.DataFrame()
            messagebox.showerror("Erro", f"Ocorreu um erro ao processar os arquivos:\n{e}")

    def revalidar_dados(self):
        if self.master_df.empty:
            messagebox.showwarning("Aviso", "Por favor, processe um arquivo CSV primeiro usando o botão '1. Processar Arquivos CSV'.")
            return

        df = self.master_df.copy()
        df['Company'] = df['Company'].str.strip()
        df['Rate Code'] = df['Rate Code'].astype(str).str.strip().str.upper()
        df['Rate_Original'] = df['Rate']

        cias_nacionais = "TAM|LATAM|GOL|AZUL"
        df_tam = df[df['Company'].str.contains("TAM|LATAM", case=False, na=False)]
        df_gol = df[df['Company'].str.contains("GOL", case=False, na=False) & (df['Rate Code'] == 'LAY')]
        df_azul = df[df['Company'].str.contains("AZUL", case=False, na=False) & (df['Rate Code'] == 'LAY')]
        
        df_internacional = df[
            (df['Rate Code'] == 'LAY') & 
            (~df['Company'].str.contains(cias_nacionais, case=False, na=False))
        ]
        
        is_weekend = self.chk_fim_de_semana_var.get()
        
        self.resultado_tam = self.validar_rate(df_tam, 349.00, 389.00, is_weekend)
        self.resultado_gol = self.validar_rate(df_gol, 359.00, 399.00, is_weekend)
        self.resultado_azul = self.validar_rate(df_azul, 359.00, 399.00, is_weekend)
        self.resultado_internacional = self.validar_rate(df_internacional, 419.00, 469.00, is_weekend=False)

        self._atualizar_visualizacao_tabelas()

    def _atualizar_visualizacao_tabelas(self):
        quartos_vistos_str = self.entry_quartos_vistos.get("1.0", tk.END).strip()
        quartos_vistos = set(filter(None, quartos_vistos_str.replace(',', '\n').split()))
        
        sort_by = self.sort_combo.get()
        datasets = {
            self.tabelas['Tam / Latam']: self.resultado_tam,
            self.tabelas['Gol']: self.resultado_gol,
            self.tabelas['Azul']: self.resultado_azul,
            self.tabelas['Internacional']: self.resultado_internacional
        }

        for tabela, df in datasets.items():
            if df is not None and not df.empty:
                df_copy = df.copy()
                if sort_by == "Status (Incorretos Primeiro)":
                    df_copy.sort_values(by=['Status', 'Room'], ascending=[False, True], inplace=True)
                else:
                    df_copy.sort_values(by='Room', inplace=True)
                self.popular_tabela(tabela, df_copy, quartos_vistos)
            else:
                tabela.delete(*tabela.get_children())


    def popular_tabela(self, tree, df, quartos_vistos):
        tree.delete(*tree.get_children())
        if df.empty: return

        current_color_group = {}
        color_index = 0

        for _, row in df.iterrows():
            room = row['Room']
            if room not in current_color_group:
                color_index += 1
                current_color_group[room] = 'group_even' if color_index % 2 == 0 else 'group_odd'
            
            bg_tag = current_color_group[room]
            status = row['Status']

            is_correct = (status == 'Correto')
            is_seen = (room in quartos_vistos)
            
            if not is_seen and is_correct:   status_tag = 'novo_correto'
            elif not is_seen and not is_correct: status_tag = 'novo_incorreto'
            elif is_seen and is_correct:     status_tag = 'correto'
            else:                            status_tag = 'incorreto'

            tree.insert("", "end", values=(room, row['Adults'], row['Rate_Original'], status), tags=(status_tag, bg_tag))

    def gerar_listas_status(self):
        if all(df.empty for df in [self.resultado_tam, self.resultado_gol, self.resultado_azul, self.resultado_internacional]):
            messagebox.showwarning("Aviso", "Processe os arquivos primeiro.")
            return

        popup = Toplevel(self.parent)
        popup.title("Listas de Status dos Quartos")
        popup.geometry("600x450")
        
        notebook_listas = tb.Notebook(popup)
        notebook_listas.pack(expand=True, fill='both', padx=10, pady=10)

        dados = {
            "Tam/Latam": self.resultado_tam, 
            "Gol": self.resultado_gol, 
            "Azul": self.resultado_azul,
            "Internacional": self.resultado_internacional
        }

        for nome, df in dados.items():
            if df.empty: continue
            aba = tb.Frame(notebook_listas)
            notebook_listas.add(aba, text=nome)
            
            corretos = sorted(df[df['Status'] == 'Correto']['Room'].unique())
            incorretos = sorted(df[df['Status'] == 'Incorreto']['Room'].unique())

            tb.Label(aba, text="Quartos CORRETOS:", font=("Segoe UI", 11, 'bold'), bootstyle="success").pack(anchor='w')
            txt_corretos = Text(aba, height=5, wrap='word', bg="#2a2a2a", fg="white", bd=0, font=("Segoe UI", 9))
            txt_corretos.pack(expand=True, fill='both', pady=(2, 10))
            txt_corretos.insert('1.0', ",".join(corretos) or "Nenhum")
            txt_corretos.config(state='disabled')

            tb.Label(aba, text="Quartos INCORRETOS:", font=("Segoe UI", 11, 'bold'), bootstyle="danger").pack(anchor='w')
            txt_incorretos = Text(aba, height=5, wrap='word', bg="#2a2a2a", fg="white", bd=0, font=("Segoe UI", 9))
            txt_incorretos.pack(expand=True, fill='both', pady=(2, 0))
            txt_incorretos.insert('1.0', ",".join(incorretos) or "Nenhum")
            txt_incorretos.config(state='disabled')



# CLASSE 2: LÓGICA E INTERFACE DO VERIFICADOR XML/GIH

class XmlCheckerApp:
    def __init__(self, parent_frame):
        self.parent = parent_frame
        self.xml_file = ""
        self.create_widgets()

    def create_widgets(self):
        frame_top = tb.Frame(self.parent)
        frame_top.pack(fill="x", padx=10, pady=5)
        btn_arquivo = tb.Button(frame_top, text="Selecionar XML", command=self.carregar_xml, bootstyle="info")
        btn_arquivo.pack(side="left")
        self.lbl_arquivo = tb.Label(frame_top, text="Nenhum arquivo selecionado")
        self.lbl_arquivo.pack(side="left", padx=10)

        frame_input = tb.LabelFrame(self.parent, text="Quartos já olhados (Separados por vírgula)", bootstyle="primary")
        frame_input.pack(fill="x", padx=10, pady=5)
        self.txt_quartos = Text(frame_input, height=3, bg="#2a2a2a", fg="white", insertbackground="white")
        self.txt_quartos.pack(fill="x", padx=5, pady=5)

        frame_controls = tb.Frame(self.parent)
        frame_controls.pack(pady=5)
        btn_processar = tb.Button(frame_controls, text="Processar", bootstyle="success", command=self.processar)
        btn_processar.pack(side="left", padx=5)
        btn_limpar = tb.Button(frame_controls, text="Limpar", bootstyle="danger", command=self.limpar_interface)
        btn_limpar.pack(side="left", padx=5)
        
        self.lbl_total = tb.Label(self.parent, text="Total de quartos: -")
        self.lbl_total.pack()
        self.lbl_sem_coment = tb.Label(self.parent, text="Total SEM comentários: -")
        self.lbl_sem_coment.pack()

        notebook = tb.Notebook(self.parent)
        notebook.pack(fill="both", expand=True, padx=10, pady=5)

        tab_rates = tb.Frame(notebook)
        notebook.add(tab_rates, text="Rates e Notes")
        tab_rates.grid_columnconfigure(1, weight=1)
        tab_rates.grid_rowconfigure(0, weight=1)
        tab_rates.grid_rowconfigure(1, weight=1)
        
        self.txt_sem_notes = self._create_text_box(tab_rates, "SEM notes (Para checar)", 0, 0, "primary")
        self.txt_divergentes = self._create_text_box(tab_rates, "Notes divergentes (Falta TRF)", 0, 1, "primary")
        self.txt_fantasmas = self._create_text_box(tab_rates, "Fantasmas (Na sua lista, mas não no XML)", 1, 0, "primary")
        self.txt_sem_checar = self._create_text_box(tab_rates, "Sem Checar (No XML, mas não na sua lista)", 1, 1, "primary")

        tab_adults = tb.Frame(notebook)
        notebook.add(tab_adults, text="Divergências de Adultos")
        linha_adults = tb.Frame(tab_adults)
        linha_adults.pack(fill="both", expand=True, padx=5, pady=5)

        self.txt_sem_adulto_principal = self._create_text_box(linha_adults, "1. Sem Adulto Principal (< 1 Adults)", side="left", bootstyle="danger")
        
        frame_stacked = tb.Frame(linha_adults)
        frame_stacked.pack(side="left", fill="both", expand=True, padx=3)
        self.txt_adults_divergentes = self._create_text_box(frame_stacked, "2. Adults != Contagem (Sem LAY)", side="top", bootstyle="warning")
        self.txt_adults_divergentes_lay = self._create_text_box(frame_stacked, "3. Adults != Contagem (com RATE=LAY)", side="top", bootstyle="info")
        
    def _create_text_box(self, parent, label, grid_row=None, grid_col=None, bootstyle="secondary", side=None):
        frame = tb.LabelFrame(parent, text=label, bootstyle=bootstyle)
        if side:
            frame.pack(side=side, fill="both", expand=True, padx=3, pady=3)
        else:
            frame.grid(row=grid_row, column=grid_col, sticky="nsew", padx=5, pady=5)
            
        widget = Text(frame, wrap="word", bg="#2a2a2a", fg="white", insertbackground="white")
        widget.pack(fill="both", expand=True, padx=3, pady=3)
        tb.Button(frame, text="Copiar", bootstyle="secondary", command=lambda: self.copiar_conteudo(widget)).pack(side="bottom", fill="x", padx=5, pady=3)
        return widget
        
    def copiar_conteudo(self, widget):
        conteudo = widget.get("1.0", "end").strip()
        if conteudo:
            app.clipboard_clear()
            app.clipboard_append(conteudo)
            messagebox.showinfo("Copiado", "Conteúdo copiado para a área de transferência!")

    def carregar_xml(self):
        self.xml_file = filedialog.askopenfilename(title="Selecione o arquivo XML", filetypes=[("Arquivos XML", "*.xml")])
        if self.xml_file:
            self.lbl_arquivo.config(text=f"Arquivo: {os.path.basename(self.xml_file)}")
        else:
            self.lbl_arquivo.config(text="Nenhum arquivo selecionado")
            
    def limpar_interface(self):
        self.xml_file = ""
        self.txt_quartos.delete("1.0", "end")
        self.txt_sem_notes.delete("1.0", "end")
        self.txt_divergentes.delete("1.0", "end")
        self.txt_fantasmas.delete("1.0", "end")
        self.txt_sem_checar.delete("1.0", "end")
        self.txt_sem_adulto_principal.delete("1.0", "end")
        self.txt_adults_divergentes.delete("1.0", "end")
        self.txt_adults_divergentes_lay.delete("1.0", "end")
        self.lbl_arquivo.config(text="Nenhum arquivo selecionado")
        self.lbl_total.config(text="Total de quartos: -")
        self.lbl_sem_coment.config(text="Total SEM comentários: -")
        messagebox.showinfo("Limpo", "A interface foi limpa com sucesso.")

    def processar(self):
        if not self.xml_file:
            messagebox.showwarning("Aviso", "Selecione um arquivo XML primeiro!")
            return
        user_list = self.txt_quartos.get("1.0", "end").strip()
        if not user_list:
            # Permite processar mesmo sem quartos na lista de "vistos"
            user_rooms = set()
        else:
            user_rooms = set(filter(None, user_list.replace("\n", "").replace(",", " ").split()))

        try:
            tree = ET.parse(self.xml_file)
            root = tree.getroot()
        except Exception as e:
            messagebox.showerror("Erro de XML", f"Não foi possível ler o arquivo XML: {e}")
            return
        
        quartos_totais, quartos_sem_comentarios, divergentes = [], [], []
        adults_check = defaultdict(lambda: {"sum": 0, "count": 0, "has_main": False, "has_lay": False})

        for res in root.findall('.//G_RESERVATION'):
            room_elem = res.find('.//ROOM')
            if room_elem is None or not room_elem.text: continue
            room = room_elem.text.strip()
            
            def get_text(element_name):
                elem = res.find(f'.//{element_name}')
                return elem.text.strip() if elem is not None and elem.text is not None else ""

            persons_txt, rate, adults_txt = get_text('PERSONS'), get_text('RATE_CODE'), get_text('ADULTS')
            comments = [c.text.upper() for c in res.findall('.//RES_COMMENT') if c.text]
            
            adults = int(adults_txt) if adults_txt.isdigit() else 0
            
            adults_check[room]["sum"] += adults
            adults_check[room]["count"] += 1
            if adults >= 1: adults_check[room]["has_main"] = True
            if rate == "LAY": adults_check[room]["has_lay"] = True

            if persons_txt.isdigit() and int(persons_txt) >= 1:
                quartos_totais.append(room)
                all_comments = " ".join(comments)
                
                if not all_comments.strip():
                    quartos_sem_comentarios.append(room)
                
                if rate != "LAY":
                    if "TRF" not in all_comments:
                        divergentes.append(room)

        sem_adulto_principal, ad_diverg, ad_diverg_lay = [], [], []
        for room, data in adults_check.items():
            if not data["has_main"]: sem_adulto_principal.append(room)
            elif data["sum"] != data["count"]:
                if data["has_lay"]: ad_diverg_lay.append(room)
                else: ad_diverg.append(room)
        
        unique = lambda seq: sorted(list(set(seq)))
        def filter_seen(rooms): return [r for r in unique(rooms) if r not in user_rooms]

        xml_rooms = unique(quartos_totais)
        
        # "SEM notes" ignora a lista de quartos vistos
        self.preencher_caixa(self.txt_sem_notes, unique(quartos_sem_comentarios))
        
        # As outras listas continuam filtrando os quartos já vistos
        self.preencher_caixa(self.txt_divergentes, filter_seen(divergentes))
        self.preencher_caixa(self.txt_fantasmas, sorted(list(user_rooms - set(xml_rooms))))
        self.preencher_caixa(self.txt_sem_checar, sorted(list(set(xml_rooms) - user_rooms)))
        self.preencher_caixa(self.txt_sem_adulto_principal, filter_seen(sem_adulto_principal))
        self.preencher_caixa(self.txt_adults_divergentes, filter_seen(ad_diverg))
        self.preencher_caixa(self.txt_adults_divergentes_lay, filter_seen(ad_diverg_lay))

        self.lbl_total.config(text=f"Total de quartos: {len(xml_rooms)}")
        self.lbl_sem_coment.config(text=f"Total SEM comentários: {len(unique(quartos_sem_comentarios))}")
        
    def preencher_caixa(self, widget, lista):
        widget.delete("1.0", "end")
        if lista:
            widget.insert("end", ",".join(lista))

#==============================================================================
# APLICAÇÃO PRINCIPAL (HUB)
#==============================================================================
class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Análise de Reservas")
        self.root.geometry("950x650")

        main_notebook = tb.Notebook(self.root)
        main_notebook.pack(expand=True, fill='both', padx=10, pady=10)

        rate_validator_frame = tb.Frame(main_notebook)
        xml_checker_frame = tb.Frame(main_notebook)

        main_notebook.add(rate_validator_frame, text="  Validador de Rates (CSV)   ")
        main_notebook.add(xml_checker_frame, text="  Verificador de Quartos (XML)   ")

        self.rate_app = RateValidatorApp(rate_validator_frame)
        self.xml_app = XmlCheckerApp(xml_checker_frame)

if __name__ == "__main__":
    app = tb.Window(themename="darkly")
    main_app = MainApp(app)

    app.mainloop()
