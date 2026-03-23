import customtkinter as ctk
import sqlite3
import webbrowser
import os
import sys
import ctypes
import shutil
import hashlib
from datetime import datetime, timedelta
from tkinter import messagebox, ttk
import urllib.parse

# --- 1. CONFIGURAÇÕES DE CAMINHO E SEGURANÇA ---

def obter_caminho_dados():
    if getattr(sys, 'frozen', False):
        diretorio_atual = os.path.dirname(sys.executable)
    else:
        diretorio_atual = os.path.dirname(os.path.abspath(__file__))
    
    app_dir = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), "CantinhoAnimal")
    if not os.path.exists(app_dir):
        os.makedirs(app_dir)
    return os.path.join(app_dir, "dados_veterinaria.db")

def recurso_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def aplicar_icone(janela):
    try:
        diretorio_base = os.path.dirname(os.path.abspath(sys.argv[0]))
        caminho_logo = os.path.join(diretorio_base, "logo.ico")
        if not os.path.exists(caminho_logo):
            caminho_logo = recurso_path("logo.ico")
        if os.path.exists(caminho_logo):
            janela.after(200, lambda: janela.iconbitmap(caminho_logo))
    except Exception as e:
        print(f"Aviso - Ícone não carregado: {e}")

def gerar_hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

# --- 2. INICIALIZAÇÃO DO BANCO DE DADOS (VERSÃO BLINDADA) ---

def inicializar_banco():
    caminho_db = obter_caminho_dados()
    conn = sqlite3.connect(caminho_db)
    cursor = conn.cursor()
    
    # Cria a tabela inicial caso não exista nada
    cursor.execute('''CREATE TABLE IF NOT EXISTS pets (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        cliente TEXT, pet TEXT, telefone TEXT)''')

    # --- CORREÇÃO AUTOMÁTICA DE COLUNA ---
    # Tenta adicionar a coluna sobrenome. Se já existir, o SQLite ignora o erro.
    try:
        cursor.execute("ALTER TABLE pets ADD COLUMN sobrenome TEXT")
    except sqlite3.OperationalError:
        pass # Coluna já existe, não faz nada

    cursor.execute('''CREATE TABLE IF NOT EXISTS vacinas (
                        id_vacina INTEGER PRIMARY KEY AUTOINCREMENT,
                        id_pet INTEGER, nome_vacina TEXT, vencimento TEXT,
                        FOREIGN KEY (id_pet) REFERENCES pets (id) ON DELETE CASCADE)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        login TEXT UNIQUE, senha_hash TEXT)''')
    
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO usuarios (login, senha_hash) VALUES (?, ?)", ("admin", gerar_hash_senha("admin")))
    
    conn.commit()
    conn.close()

# --- 3. JANELAS DE ACESSO (LOGIN E CADASTRO USUÁRIO) ---

class JanelaCadastro(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Novo Login")
        self.geometry("350x350")
        aplicar_icone(self)
        self.attributes("-topmost", True)
        self.grab_set()
        self.configure(fg_color="#FFFFFF")

        ctk.CTkLabel(self, text="🛡️ Novo Acesso", font=("Segoe UI", 20, "bold"), text_color="#2D5A27").pack(pady=25)
        
        self.new_user = ctk.CTkEntry(self, placeholder_text="Login", width=220, height=40, corner_radius=10)
        self.new_user.pack(pady=10)
        
        self.new_pass = ctk.CTkEntry(self, placeholder_text="Senha", show="*", width=220, height=40, corner_radius=10)
        self.new_pass.pack(pady=10)
        
        ctk.CTkButton(self, text="Criar Conta", fg_color="#2D5A27", hover_color="#1E3D1A", 
                      width=220, height=40, corner_radius=10, command=self.salvar_usuario).pack(pady=25)

    def salvar_usuario(self):
        user, pwd = self.new_user.get().strip(), self.new_pass.get().strip()
        if not user or not pwd: return messagebox.showwarning("Aviso", "Preencha tudo!")
        try:
            conn = sqlite3.connect(obter_caminho_dados())
            conn.execute("INSERT INTO usuarios (login, senha_hash) VALUES (?, ?)", (user, gerar_hash_senha(pwd)))
            conn.commit(); conn.close()
            messagebox.showinfo("Sucesso", "Usuário cadastrado!")
            self.destroy()
        except sqlite3.IntegrityError: messagebox.showerror("Erro", "Usuário já existe!")

class JanelaLogin(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Acesso - Cantinho Animal")
        self.geometry("400x500")
        self.protocol("WM_DELETE_WINDOW", self.parent.quit)
        aplicar_icone(self)
        self.attributes("-topmost", True)
        self.grab_set()
        self.configure(fg_color="#FFFFFF")
        
        ctk.CTkLabel(self, text="🐾", font=("Segoe UI", 50)).pack(pady=(40, 0))
        ctk.CTkLabel(self, text="Cantinho Animal", text_color="#2D5A27", font=("Segoe UI", 26, "bold")).pack(pady=5)
        ctk.CTkLabel(self, text="Controle Veterinário", font=("Segoe UI", 14), text_color="#7F8C8D").pack(pady=(0, 30))
        
        self.entry_user = ctk.CTkEntry(self, placeholder_text="Usuário", width=280, height=45, corner_radius=10)
        self.entry_user.pack(pady=10)
        self.entry_senha = ctk.CTkEntry(self, placeholder_text="Senha", width=280, height=45, corner_radius=10, show="*")
        self.entry_senha.pack(pady=10)
        
        ctk.CTkButton(self, text="Entrar no Sistema", fg_color="#2D5A27", hover_color="#1E3D1A", 
                      width=280, height=45, corner_radius=10, font=("Segoe UI", 14, "bold"), command=self.validar_acesso).pack(pady=20)
        
        ctk.CTkButton(self, text="Novo Login", fg_color="transparent", text_color="#2D5A27",
                      border_width=1, border_color="#2D5A27", command=lambda: JanelaCadastro(self)).pack()

    def validar_acesso(self):
        user, pwd = self.entry_user.get(), self.entry_senha.get()
        conn = sqlite3.connect(obter_caminho_dados())
        res = conn.execute("SELECT * FROM usuarios WHERE login=? AND senha_hash=?", (user, gerar_hash_senha(pwd))).fetchone()
        conn.close()
        if res: self.parent.deiconify(); self.destroy(); self.parent.after(500, self.parent.verificar_vencimentos)
        else: messagebox.showerror("Erro", "Login ou senha inválidos.")

# --- 4. CLASSE PRINCIPAL ---

class AppVete(ctk.CTk):
    def __init__(self):
        super().__init__()
        inicializar_banco()
        self.caminho_db = obter_caminho_dados()
        self.withdraw()
        self.title("Cantinho Animal - Gestão")
        self.geometry("1200x800")
        ctk.set_appearance_mode("light")
        self.configure(fg_color="#F0F2F5")
        aplicar_icone(self)
        self.configurar_estilo_tabela()

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Sidebar (Cadastro) ---
        self.frame_cadastro = ctk.CTkFrame(self, width=350, corner_radius=20, fg_color="#FFFFFF", border_width=1, border_color="#E0E0E0")
        self.frame_cadastro.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        
        ctk.CTkLabel(self.frame_cadastro, text="📋 Ficha do Pet", font=("Segoe UI", 20, "bold"), text_color="#2D5A27").pack(pady=20)
        
        self.entry_cliente = self.criar_campo("Dono do Animal", "Nome do Cliente")
        self.entry_sobrenome = self.criar_campo("Sobrenome", "Sobrenome do Cliente")
        self.entry_pet = self.criar_campo("Nome do Pet", "Ex: Rex, Luna...")
        self.entry_tel = self.criar_campo("WhatsApp (DDD + Número)", "11999998888")
        self.entry_vacina = self.criar_campo("Vacina Aplicada", "Ex: V10, Raiva")
        
        ctk.CTkLabel(self.frame_cadastro, text="Vencimento", font=("Segoe UI", 12, "bold"), text_color="#555555").pack(anchor="w", padx=35)
        self.entry_data = ctk.CTkEntry(self.frame_cadastro, placeholder_text="DD/MM/AAAA", width=280, height=40, corner_radius=10)
        self.entry_data.pack(pady=(2, 15)); self.entry_data.bind("<KeyRelease>", self.formatar_data)

        # Botões da Sidebar
        self.btn_salvar = self.criar_botao("💾 Salvar Registro", "#2D5A27", "#1E3D1A", self.salvar_dados)
        self.btn_wpp = self.criar_botao("💬 Enviar WhatsApp", "#25D366", "#1DA851", self.enviar_whatsapp)
        self.btn_update = self.criar_botao("🔄 Atualizar Dados", "#E67E22", "#D35400", self.atualizar_dados_pet)
        self.btn_limpar = self.criar_botao("🧹 Limpar Campos", "transparent", "#EEEEEE", self.limpar_campos, text_color="#7F8C8D", border=True)
        self.btn_del = self.criar_botao("🗑️ Excluir Pet", "#FF4444", "#CC0000", self.apagar_registro)

        # --- Main Area (Tabelas) ---
        self.frame_main = ctk.CTkFrame(self, corner_radius=20, fg_color="#FFFFFF", border_width=1, border_color="#E0E0E0")
        self.frame_main.grid(row=0, column=1, padx=(0, 20), pady=20, sticky="nsew")

        self.entry_pesquisa = ctk.CTkEntry(self.frame_main, placeholder_text="🔍 Pesquisar por Dono ou Pet...", height=45, corner_radius=15)
        self.entry_pesquisa.pack(fill="x", padx=20, pady=20); self.entry_pesquisa.bind("<KeyRelease>", self.pesquisar_pets)

        # Tabela Pets
        self.tabela_pets = ttk.Treeview(self.frame_main, columns=("ID", "Dono", "Sobrenome", "Pet", "Telefone"), show="headings")
        for col in ("ID", "Dono", "Sobrenome", "Pet", "Telefone"): 
            self.tabela_pets.heading(col, text=col)
            self.tabela_pets.column(col, anchor="center")
        self.tabela_pets.column("ID", width=50)
        self.tabela_pets.pack(expand=True, fill="both", padx=20, pady=5)
        self.tabela_pets.bind("<<TreeviewSelect>>", self.ao_selecionar_pet)

        # Tabela Vacinas (Histórico)
        ctk.CTkLabel(self.frame_main, text="💉 Histórico de Vacinas", font=("Segoe UI", 16, "bold"), text_color="#2D5A27").pack(pady=(15, 5))
        self.tabela_vacinas = ttk.Treeview(self.frame_main, columns=("Vacina", "Vencimento"), show="headings", height=5)
        self.tabela_vacinas.heading("Vacina", text="Vacina"); self.tabela_vacinas.heading("Vencimento", text="Data de Vencimento")
        self.tabela_vacinas.pack(fill="x", padx=20, pady=(0, 20))

        # Barra de Status
        self.status = ctk.CTkLabel(self, text="✓ Banco de Dados Conectado | v1.0", font=("Segoe UI", 11), text_color="#999999")
        self.status.grid(row=1, column=0, columnspan=2, pady=5)

        self.atualizar_tabela_pets()
        self.abrir_login()

    # --- FUNÇÕES DE INTERFACE ---
    
    def configurar_estilo_tabela(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#FFFFFF", foreground="#333333", rowheight=35, fieldbackground="#FFFFFF", borderwidth=0, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", background="#F2F2F2", foreground="#2D5A27", font=("Segoe UI", 10, "bold"), borderwidth=0)
        style.map("Treeview", background=[('selected', '#2D5A27')], foreground=[('selected', '#FFFFFF')])

    def criar_campo(self, label, placeholder):
        lbl = ctk.CTkLabel(self.frame_cadastro, text=label, font=("Segoe UI", 12, "bold"), text_color="#555555")
        lbl.pack(anchor="w", padx=35, pady=(5, 0))
        entry = ctk.CTkEntry(self.frame_cadastro, placeholder_text=placeholder, width=280, height=40, corner_radius=10, border_color="#D1D1D1", fg_color="#F9F9F9")
        entry.pack(pady=(2, 8)); return entry

    def criar_botao(self, text, color, hover, cmd, text_color="#FFFFFF", border=False):
        btn = ctk.CTkButton(self.frame_cadastro, text=text, fg_color=color, hover_color=hover, text_color=text_color,
                            height=40, corner_radius=10, font=("Segoe UI", 13, "bold"), command=cmd)
        if border: btn.configure(border_width=2, border_color="#7F8C8D")
        btn.pack(pady=5, padx=35, fill="x"); return btn

    # --- LÓGICA DE DADOS ---

    def limpar_campos(self):
        if self.tabela_pets.selection(): self.tabela_pets.selection_remove(self.tabela_pets.selection())
        for e in [self.entry_cliente, self.entry_sobrenome, self.entry_pet, self.entry_tel, self.entry_vacina, self.entry_data]: e.delete(0, 'end')
        for r in self.tabela_vacinas.get_children(): self.tabela_vacinas.delete(r)

    def salvar_dados(self):
        c, s, p, t, v, d = self.entry_cliente.get().strip(), self.entry_sobrenome.get().strip(), self.entry_pet.get().strip(), self.entry_tel.get().strip(), self.entry_vacina.get().strip(), self.entry_data.get().strip()
        if not all([c, p, v, d]): return messagebox.showwarning("Campos Vazios", "Preencha os campos obrigatórios!")
        conn = sqlite3.connect(self.caminho_db)
        cursor = conn.cursor()
        res = cursor.execute("SELECT id FROM pets WHERE cliente=? AND pet=?", (c, p)).fetchone()
        id_p = res[0] if res else cursor.execute("INSERT INTO pets (cliente, sobrenome, pet, telefone) VALUES (?,?,?,?)", (c,s,p,t)).lastrowid
        cursor.execute("INSERT INTO vacinas (id_pet, nome_vacina, vencimento) VALUES (?,?,?)", (id_p, v, d))
        conn.commit(); conn.close(); self.atualizar_tabela_pets(); self.limpar_campos()
        messagebox.showinfo("Sucesso", "Dados registrados com sucesso!")

    def ao_selecionar_pet(self, event):
        sel = self.tabela_pets.selection()
        if not sel: return
        val = self.tabela_pets.item(sel)['values']
        for i, e in enumerate([None, self.entry_cliente, self.entry_sobrenome, self.entry_pet, self.entry_tel]):
            if e: e.delete(0, 'end'); e.insert(0, val[i])
        for r in self.tabela_vacinas.get_children(): self.tabela_vacinas.delete(r)
        conn = sqlite3.connect(self.caminho_db)
        for vac in conn.execute("SELECT nome_vacina, vencimento FROM vacinas WHERE id_pet=?", (val[0],)).fetchall():
            self.tabela_vacinas.insert("", "end", values=vac)
        conn.close()

    def atualizar_tabela_pets(self, busca=""):
        for r in self.tabela_pets.get_children(): self.tabela_pets.delete(r)
        conn = sqlite3.connect(self.caminho_db)
        linhas = conn.execute("SELECT id, cliente, sobrenome, pet, telefone FROM pets WHERE cliente LIKE ? OR pet LIKE ?", (f"%{busca}%", f"%{busca}%")).fetchall()
        for l in linhas: self.tabela_pets.insert("", "end", values=l)
        conn.close()

    def pesquisar_pets(self, event): self.atualizar_tabela_pets(self.entry_pesquisa.get())

    def atualizar_dados_pet(self):
        sel = self.tabela_pets.selection()
        if not sel: return messagebox.showwarning("Aviso", "Selecione um pet na tabela.")
        id_p = self.tabela_pets.item(sel)['values'][0]
        conn = sqlite3.connect(self.caminho_db)
        conn.execute("UPDATE pets SET cliente=?, sobrenome=?, pet=?, telefone=? WHERE id=?", (self.entry_cliente.get(), self.entry_sobrenome.get(), self.entry_pet.get(), self.entry_tel.get(), id_p))
        conn.commit(); conn.close(); self.atualizar_tabela_pets(); messagebox.showinfo("OK", "Dados atualizados!")

    def verificar_vencimentos(self):
        conn = sqlite3.connect(self.caminho_db)
        hoje = datetime.now()
        alertas = []
        
        # Buscamos os dados
        dados = conn.execute("""
            SELECT pets.pet, vacinas.nome_vacina, vacinas.vencimento 
            FROM vacinas 
            JOIN pets ON vacinas.id_pet = pets.id
        """).fetchall()
        
        for pet, vacina, data_v in dados:
            try:
                dt = datetime.strptime(data_v, "%d/%m/%Y")
                # Se vence em até 7 dias
                if hoje <= dt <= (hoje + timedelta(days=7)):
                    alertas.append(f"• A vacina {vacina} do(a) {pet} vencerá em breve ({data_v}).")
                # Se já venceu
                elif dt < hoje:
                    alertas.append(f"• Atenção: A vacina {vacina} do(a) {pet} está vencida desde {data_v}!")
            except:
                continue
        conn.close()

        if alertas:
            # Criamos uma mensagem com um cabeçalho educado
            mensagem_final = "Olá! Identificamos as seguintes vacinas para atenção:\n\n" + "\n".join(alertas)
            messagebox.showwarning("Lembrete de Vacinação", mensagem_final)

    def formatar_data(self, event):
        if event.keysym in ['BackSpace', 'Delete']: return
        t = "".join(filter(str.isdigit, self.entry_data.get()))
        if len(t) >= 2: t = t[:2] + "/" + t[2:]
        if len(t) >= 5: t = t[:5] + "/" + t[5:9]
        self.entry_data.delete(0, 'end'); self.entry_data.insert(0, t[:10])

    def apagar_registro(self):
        sel = self.tabela_pets.selection()
        if sel and messagebox.askyesno("Confirmar", "Apagar permanentemente este pet?"):
            conn = sqlite3.connect(self.caminho_db)
            conn.execute("DELETE FROM pets WHERE id=?", (self.tabela_pets.item(sel)['values'][0],))
            conn.commit(); conn.close(); self.limpar_campos(); self.atualizar_tabela_pets()

    def enviar_whatsapp(self):
        sel = self.tabela_pets.selection()
        if not sel: return
        d = self.tabela_pets.item(sel)['values']
        msg = urllib.parse.quote(f"Olá {d[1]}! 🐾 Lembrete do Cantinho Animal: A vacina do(a) {d[3]} está próxima do vencimento. Vamos agendar?")
        webbrowser.open(f"https://web.whatsapp.com/send?phone=55{d[4]}&text={msg}")

    def fechar_com_backup(self):
        try:
            backup_dir = os.path.join(os.path.dirname(self.caminho_db), "Backups")
            if not os.path.exists(backup_dir): os.makedirs(backup_dir)
            shutil.copy2(self.caminho_db, os.path.join(backup_dir, f"Bkp_{datetime.now().strftime('%Y%m%d')}.db"))
        except: pass
        self.destroy()

    def abrir_login(self): JanelaLogin(self)

if __name__ == "__main__":
    try: ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("vete.app.1")
    except: pass
    app = AppVete()
    app.protocol("WM_DELETE_WINDOW", app.fechar_com_backup)
    app.mainloop()