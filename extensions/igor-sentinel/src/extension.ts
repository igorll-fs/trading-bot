import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';

interface ErrorPayload {
    source?: string;
    summary?: string;
    command?: string;
    notes?: string[];
    reportPath?: string;
    raw?: string;
}

const DEFAULT_REPORT_RELATIVE = path.join('logs', 'last_error_report.md');

export function activate(context: vscode.ExtensionContext) {
    const disposable = vscode.commands.registerCommand('igorSentinel.pushError', async (payload?: string | ErrorPayload) => {
        try {
            const resolved = await resolvePayload(payload);
            await surfaceError(resolved);
        } catch (error) {
            const message = error instanceof Error ? error.message : String(error);
            vscode.window.showErrorMessage(`Igor Sentinel falhou: ${message}`);
        }
    });

    context.subscriptions.push(disposable);
}

export function deactivate() {
    // nothing to cleanup
}

async function resolvePayload(payload?: string | ErrorPayload): Promise<Required<ErrorPayload>> {
    if (payload && typeof payload === 'string') {
        const parsed = tryParseJson(payload);
        if (parsed) {
            return normalizePayload(parsed);
        }
        return normalizePayload({ raw: payload, summary: payload });
    }

    if (payload && typeof payload === 'object') {
        return normalizePayload(payload);
    }

    const reportPath = await resolveReportPath();
    const raw = await fs.promises.readFile(reportPath, { encoding: 'utf-8' });
    return normalizePayload({
        reportPath,
        raw,
        summary: extractSummary(raw),
    });
}

function tryParseJson(text: string): ErrorPayload | undefined {
    try {
        const parsed = JSON.parse(text);
        return parsed;
    } catch (error) {
        return undefined;
    }
}

function extractSummary(markdown: string): string {
    const firstLine = markdown.split(/\r?\n/).find((line) => line.trim().length > 0);
    return firstLine ?? 'Erro detectado';
}

async function resolveReportPath(): Promise<string> {
    const workspace = vscode.workspace.workspaceFolders?.[0];
    if (!workspace) {
        throw new Error('Nenhum workspace aberto. Abra o diretório raiz do bot para usar o Sentinel.');
    }
    const candidate = path.join(workspace.uri.fsPath, DEFAULT_REPORT_RELATIVE);
    const exists = await fileExists(candidate);
    if (!exists) {
        throw new Error(`Relatório ${DEFAULT_REPORT_RELATIVE} não encontrado.`);
    }
    return candidate;
}

async function fileExists(target: string): Promise<boolean> {
    try {
        await fs.promises.access(target, fs.constants.F_OK);
        return true;
    } catch (error) {
        return false;
    }
}

function normalizePayload(payload: ErrorPayload): Required<ErrorPayload> {
    return {
        source: payload.source ?? 'desconhecido',
        summary: payload.summary ?? payload.raw ?? 'Erro sem descrição',
        command: payload.command ?? '',
        notes: payload.notes ?? [],
        reportPath: payload.reportPath ?? DEFAULT_REPORT_RELATIVE,
        raw: payload.raw ?? '',
    };
}

async function surfaceError(payload: Required<ErrorPayload>) {
    const workspace = vscode.workspace.workspaceFolders?.[0];
    const fullReportPath = workspace ? path.join(workspace.uri.fsPath, payload.reportPath) : payload.reportPath;
    const actions = buildActions(payload.command, fullReportPath);

    const selection = await vscode.window.showInformationMessage(
        `${payload.summary} (fonte: ${payload.source})`,
        ...actions
    );

    if (!selection) {
        return;
    }

    switch (selection) {
        case 'Abrir relatório':
            await openReport(fullReportPath);
            break;
        case 'Copiar comando':
            if (payload.command) {
                await vscode.env.clipboard.writeText(payload.command);
                vscode.window.showInformationMessage('Comando copiado para a área de transferência.');
            }
            break;
        default:
            break;
    }
}

function buildActions(command: string, reportPath: string): string[] {
    const actions = ['Abrir relatório'];
    if (command) {
        actions.push('Copiar comando');
    }
    return actions;
}

async function openReport(reportPath: string) {
    try {
        const doc = await vscode.workspace.openTextDocument(reportPath);
        await vscode.window.showTextDocument(doc, { preview: false });
    } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        vscode.window.showErrorMessage(`Não foi possível abrir o relatório: ${message}`);
    }
}
