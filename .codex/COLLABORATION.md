# Colaboração com três IAs do Codex

Este padrão vale para o trabalho neste repositório. Preserve as instruções específicas do projeto.

- Reserve uma branch para cada tarefa. Há três branches iniciais: `codex/ia-1`, `codex/ia-2` e `codex/ia-3`. Cada uma pode ter somente uma tarefa ativa.
- Quando o usuário indicar IA 1, 2 ou 3, use a branch correspondente. Para outra tarefa simultânea da mesma IA, use `codex/ia-N-descricao-unica`. Sem número indicado, crie uma branch exclusiva `codex/tarefa-descricao-id`; não é necessário perguntar.
- Antes de começar, descubra a branch padrão do remoto (não suponha main/master), faça fetch quando disponível e incorpore a versão atual dela à branch de trabalho. Nunca reinicie ou sobrescreva uma branch existente. Se houver trabalho pendente de outra tarefa, crie uma branch exclusiva a partir da base atual.
- Trabalhe em um checkout isolado. No Cloud, cada tarefa tem seu workspace; no PC, use um worktree quando houver tarefas concorrentes. Não troque a branch de um diretório usado por outra IA.
- Divida o escopo por tarefa e evite editar os mesmos arquivos em paralelo. Branches isolam as alterações, mas não impedem conflitos.
- Faça commits somente da tarefa, execute as verificações apropriadas e entregue um pull request para a branch padrão, com resumo e validação. Não force push, descarte trabalho de terceiros nem inclua segredos.
- A integração deve acontecer em sequência, incorporando a base atual e resolvendo conflitos antes de cada merge. Integre ou publique quando o usuário solicitar; não faça deploy automático das branches de trabalho.
- Após um merge, incorpore a branch padrão atualizada antes de reutilizar a branch da IA. Um merge no GitHub não atualiza automaticamente o PC nem a VPS.
- Ao concluir, informe repositório, branch, commit, verificações e link do PR quando disponível. Se o Cloud não permitir push/PR, entregue o diff e indique essa limitação.
