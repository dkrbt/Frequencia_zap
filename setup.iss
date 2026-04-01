; ======================================================
; SCRIPT DO INSTALADOR - MAMÃE CORUJA
; Configurado por: dkrbt (DevOps Specialist)
; Version: 1.4 (ENTRY POINT REFACTOR)
; ======================================================

[Setup]
AppId={{D8C8E19B-9F5E-4B7C-A5D8-E29B6C2D6D2E}
AppName=Mamãe Coruja
AppVersion=1.4
AppPublisher=dkrbt
DefaultDirName={autopf}\MamaeCoruja
DefaultGroupName=Mamãe Coruja
AllowNoIcons=yes
OutputDir=dist_installer
OutputBaseFilename=MamaeCoruja_Setup_v1.4_Final
SetupIconFile=c:\projeto\Frequencia_zap\icon\mamae_coruja.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Arquivos Críticos de Execução e Configuração (Inclusão Explícita)
Source: "c:\projeto\Frequencia_zap\iniciar.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "c:\projeto\Frequencia_zap\instalar.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "c:\projeto\Frequencia_zap\requirements.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "c:\projeto\Frequencia_zap\docker-compose.yml"; DestDir: "{app}"; Flags: ignoreversion

; Inclui o resto do projeto (exclui pastas de dados e temporários)
Source: "c:\projeto\Frequencia_zap\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: ".venv\*, .git\*, *.db, *.log, __pycache__\*, .idea\*, .env, .env.example, *.iss, dist_installer\*, evolution_db_data\*, evolution_instances\*, evolution_store\*, logs\*, debug_html\*, FrequenciaZap_Launcher.exe, FrequenciaZap_Launcher.spec, database\*, iniciar.bat, instalar.bat, requirements.txt, docker-compose.yml"

[Icons]
Name: "{group}\Mamãe Coruja"; Filename: "{app}\iniciar.bat"; IconFilename: "{app}\icon\mamae_coruja.ico"
Name: "{autodesktop}\Mamãe Coruja"; Filename: "{app}\iniciar.bat"; IconFilename: "{app}\icon\mamae_coruja.ico"; Tasks: desktopicon

[Run]
; Novo Ponto de Entrada: O Iniciar.bat agora gerencia a instalacao e execucao
Filename: "{app}\iniciar.bat"; Description: "Iniciar Mamãe Coruja"; Flags: postinstall nowait skipifsilent

[Code]
var
  ConfigPage: TInputQueryWizardPage;

procedure InitializeWizard;
begin
  // Criação da página de configuração customizada
  ConfigPage := CreateInputQueryPage(wpSelectDir,
    'Configurações de Segurança e Sistema', 
    'Por favor, defina as as senhas do seu sistema.',
    'Estas informações são fundamentais para o funcionamento do Mamãe Coruja.');

  ConfigPage.Add('Senha do Painel (Admin/Postgres):', True); // Oculta senha
  ConfigPage.Add('URL da Evolution API (Recomendado: http://localhost:8081):', False);
  ConfigPage.Add('Nome da Instância (Ex: mamae_coruja):', False);

  // Valores padrão recomendados
  ConfigPage.Values[1] := 'http://localhost:8081';
  ConfigPage.Values[2] := 'mamae_coruja';
end;

function GenerateAPIKey(Len: Integer): String;
var
  Characters: String;
  I: Integer;
begin
  Characters := 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
  Result := '';
  for I := 1 to Len do
    Result := Result + Characters[Random(Length(Characters)) + 1];
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  // Validação simples para evitar campos vazios
  if CurPageID = ConfigPage.ID then
  begin
    if (Trim(ConfigPage.Values[0]) = '') or (Trim(ConfigPage.Values[2]) = '') then
    begin
      MsgBox('Preencha as senhas obrigatórias para continuar.', mbError, MB_OK);
      Result := False;
    end;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  EnvLines: TArrayOfString;
  GeneratedKey: String;
begin
  // Gravação do arquivo .env após a cópia dos arquivos
  if CurStep = ssPostInstall then
  begin
    GeneratedKey := GenerateAPIKey(32);
    SetArrayLength(EnvLines, 30);
    EnvLines[0] := '# --- CONFIGURACOES MAE CORUJA ---';
    EnvLines[1] := 'ADMIN_PASSWORD=' + Trim(ConfigPage.Values[0]);
    EnvLines[2] := 'POSTGRES_PASSWORD=' + Trim(ConfigPage.Values[0]);
    EnvLines[3] := 'EVOLUTION_API_URL=' + Trim(ConfigPage.Values[1]);
    EnvLines[4] := 'EVOLUTION_API_TOKEN=' + GeneratedKey;
    EnvLines[5] := 'EVOLUTION_INSTANCE=' + Trim(ConfigPage.Values[2]);
    EnvLines[6] := '';
    EnvLines[7] := '# --- CONFIGURACOES STREAMLIT ---';
    EnvLines[8] := 'STREAMLIT_SERVER_PORT=8501';
    EnvLines[9] := 'STREAMLIT_SERVER_HEADLESS=true';
    EnvLines[10] := 'STREAMLIT_THEME_BASE=dark';
    EnvLines[11] := '';
    EnvLines[12] := '# Banco de Dados e Logs';
    EnvLines[13] := 'DB_PATH=database/escola.db';
    EnvLines[14] := 'LOG_LEVEL=INFO';
    EnvLines[15] := 'LOG_FILE=logs/app.log';
    EnvLines[16] := '';
    EnvLines[17] := '# --- CONFIGURACOES API ESCOLA (OPCIONAL) ---';
    EnvLines[18] := 'SCHOOL_API_URL=';
    EnvLines[19] := 'SCHOOL_API_TOKEN=';
    EnvLines[20] := '';
    EnvLines[21] := 'AUTHENTICATION_API_KEY=' + GeneratedKey;
    EnvLines[22] := '';
    EnvLines[23] := 'COORD_PHONE_NUMBER=55'; // Placeholder
    EnvLines[24] := '';
    EnvLines[25] := '';

    SaveStringsToFile(ExpandConstant('{app}\.env'), EnvLines, False);
  end;
end;
