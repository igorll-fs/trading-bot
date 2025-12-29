# Igor Sentinel VS Code Extension

Extensão auxiliar que entrega alertas estruturados do bot diretamente no VS Code. Ela lê o arquivo `logs/last_error_report.md` gerado pelo watcher PowerShell/Python ou recebe um payload JSON e apresenta a mensagem com atalhos rápidos para abrir o relatório completo ou copiar o comando sugerido de correção.

## Estrutura
- `src/extension.ts`: registra o comando `igorSentinel.pushError`.
- `logs/last_error_report.md`: fonte padrão quando nenhum payload é fornecido.
- `docs/error_actions.json`: catálogo de assinaturas usado pelo watcher para gerar ações.

## Como usar
1. Instale dependências e compile:
   ```bash
   cd extensions/igor-sentinel
   npm install
   npm run compile
   ```
2. No VS Code, execute `Debug: Start Debugging` (F5) para rodar a extensão no modo Extension Development Host.
3. Execute o comando `Igor Sentinel: Push Error Report` pelo Command Palette:
   - Sem argumentos: a extensão abrirá `logs/last_error_report.md` e exibirá um resumo.
   - Com JSON: rode `code --command igorSentinel.pushError '{"summary":"Falha", "command":"pytest"}'` para enviar um payload personalizado.

## Integração com o watcher
O script `scripts/watch_errors.ps1` pode invocar o comando assim que gerar um relatório:
```powershell
code --command igorSentinel.pushError "{`"summary`":`"APIError -2015 detectado`",`"command`":`"python backend/test_binance_connection.py`"}"
```

## Próximos passos
- Integrar com Copilot Chat ou outros agentes, reutilizando o mesmo payload.
- Persistir histórico e permitir autoexecução de comandos marcados como seguros.
- Adicionar testes automatizados (vitest ou @vscode/test-electron) para validar fluxos críticos.
