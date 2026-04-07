"""
Self-Reflection Service - Auto-aperfeiçoamento contínuo do bot.

Inspirado pela skill self-reflection do ClawdHub.
Loop de feedback a cada 60 minutos para aprender com trades recentes.
"""

import asyncio
from datetime import datetime, timedelta, time
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import json
import os

from motor.motor_asyncio import AsyncIOMotorDatabase


class ReflectionService:
    """Auto-aperfeiçoamento contínuo do bot através de reflexão periódica."""

    def __init__(
        self,
        db: AsyncIOMotorDatabase,
        interval_minutes: int = 60,
        memory_path: str = "memory/episodic",
        state_file: str = ".reflection_state.json",
        active_hours_start: int = 0,  # 🧠 LEARNING: Pattern from self-reflection skill
        active_hours_end: int = 24,
    ):
        """
        Inicializa serviço de reflexão.

        Args:
            db: Database MongoDB
            interval_minutes: Intervalo entre reflexões (padrão: 60min)
            memory_path: Caminho para salvar learnings
            state_file: Arquivo JSON para persistir estado entre restarts
            active_hours_start: Hora de início (UTC, 0-23). Pattern from self-reflection skill
            active_hours_end: Hora de fim (UTC, 0-24)
        """
        self.db = db
        self.interval = timedelta(minutes=interval_minutes)
        self.last_reflection: Optional[datetime] = None
        self.memory_path = Path(memory_path)
        self.memory_path.mkdir(parents=True, exist_ok=True)
        self.state_file = Path(state_file)

        # 🧠 LEARNING: Active hours config para economizar recursos (pattern from self-reflection)
        self.active_hours = (active_hours_start, active_hours_end)

        # Métricas acumuladas
        self.total_reflections = 0
        self.critical_alerts = 0

        # 🧠 LEARNING: State persistence pattern from self-reflection skill
        self._load_state()

    async def heartbeat(self) -> None:
        """Loop principal - executa a cada intervalo configurado."""
        print(f"[REFLECTION] Heartbeat iniciado (intervalo: {self.interval})")

        while True:
            try:
                await asyncio.sleep(self.interval.total_seconds())

                if self._should_reflect():
                    await self.reflect()

            except asyncio.CancelledError:
                print("[REFLECTION] Heartbeat cancelado.")
                break
            except Exception as e:
                print(f"[REFLECTION] ⚠️ Erro no heartbeat: {e}")
                await asyncio.sleep(300)  # Wait 5min antes de retry

    def _should_reflect(self) -> bool:
        """
        Determina se é hora de refletir.

        🧠 LEARNING: Verifica active hours para economizar recursos (pattern from self-reflection).
        """
        # Check 1: Primeira reflexão sempre executa
        if self.last_reflection is None:
            return True

        # Check 2: Intervalo mínimo atingido
        elapsed = datetime.utcnow() - self.last_reflection
        if elapsed < self.interval:
            return False

        # Check 3: Dentro do horário ativo (se configurado)
        if not self._is_within_active_hours():
            print(
                f"[REFLECTION] ⏸️ Fora do horário ativo ({self.active_hours[0]}h-{self.active_hours[1]}h UTC)"
            )
            return False

        return True

    def _is_within_active_hours(self) -> bool:
        """
        Verifica se o momento atual está dentro do horário ativo.
        Pattern aprendido da skill self-reflection.

        Returns:
            True se dentro do horário ativo (ou se não há restrição)
        """
        start_hour, end_hour = self.active_hours

        # Se não há restrição (0-24), sempre ativo
        if start_hour == 0 and end_hour == 24:
            return True

        current_hour = datetime.utcnow().hour

        # Caso simples: start < end (ex: 8h-18h)
        if start_hour < end_hour:
            return start_hour <= current_hour < end_hour

        # Caso overnight: start > end (ex: 22h-6h)
        return current_hour >= start_hour or current_hour < end_hour

    async def reflect(self) -> Dict:
        """
        Processo principal de reflexão.

        Returns:
            Dict com learnings da reflexão
        """
        print("[REFLECTION] 🪞 Iniciando auto-análise...")

        try:
            # 1. Coletar dados recentes
            recent_trades = await self._get_recent_trades(limit=50)
            recent_errors = await self._get_recent_errors()

            # 2. Análise de padrões
            learnings = self._analyze_patterns(recent_trades, recent_errors)

            # 3. Documentar aprendizados
            await self._log_learnings(learnings)

            # 4. Aplicar correções seguras (se necessário)
            actions_taken = await self._apply_safe_corrections(learnings)
            learnings["actions_taken"] = actions_taken

            # 5. Atualizar métricas
            self.last_reflection = datetime.utcnow()
            self.total_reflections += 1

            if learnings.get("critical_issues"):
                self.critical_alerts += 1
            # 🧠 LEARNING: Persistir estado após cada reflexão (pattern from self-reflection skill)
            self._save_state()
            print(f"[REFLECTION] ✅ Completa. Próxima em {self.interval}.")
            print(
                f"[REFLECTION] Win rate: {learnings['win_rate']:.1%} | "
                f"Avg profit: ${learnings['avg_profit']:.2f}"
            )

            return learnings

        except Exception as e:
            print(f"[REFLECTION] ❌ Erro durante reflexão: {e}")
            return {"error": str(e), "timestamp": datetime.utcnow().isoformat()}

    async def _get_recent_trades(self, limit: int = 50) -> List[Dict]:
        """
        Busca trades recentes.

        Args:
            limit: Número de trades a buscar

        Returns:
            Lista de trades
        """
        try:
            trades = await self.db.trades.find({}, sort=[("timestamp", -1)], limit=limit).to_list(
                length=limit
            )

            return trades

        except Exception as e:
            print(f"[REFLECTION] Erro ao buscar trades: {e}")
            return []

    async def _get_recent_errors(self) -> List[Dict]:
        """
        Busca erros recentes dos logs.

        Returns:
            Lista de erros (se houver collection de errors)
        """
        try:
            # Se tivermos collection de errors
            if "errors" in await self.db.list_collection_names():
                errors = await self.db.errors.find({}, sort=[("timestamp", -1)], limit=20).to_list(
                    length=20
                )
                return errors

            return []

        except Exception as e:
            print(f"[REFLECTION] Erro ao buscar errors: {e}")
            return []

    def _analyze_patterns(self, trades: List[Dict], errors: List[Dict]) -> Dict:
        """
        Analisa padrões em trades e erros para gerar learnings.

        Args:
            trades: Lista de trades recentes
            errors: Lista de erros recentes

        Returns:
            Dict com análise e sugestões
        """
        learnings = {
            "timestamp": datetime.utcnow().isoformat(),
            "total_trades": len(trades),
            "wins": 0,
            "losses": 0,
            "win_rate": 0.0,
            "avg_profit": 0.0,
            "total_profit": 0.0,
            "common_mistakes": [],
            "suggestions": [],
            "critical_issues": [],
            "positive_patterns": [],
        }

        if not trades:
            learnings["common_mistakes"].append("Sem trades recentes - bot pode estar parado")
            learnings["suggestions"].append("Verificar se bot está ativo e condições de entrada")
            return learnings

        # Análise de performance
        profits = []
        for trade in trades:
            profit = trade.get("profit", 0) or trade.get("pnl", 0)
            profits.append(profit)

            if profit > 0:
                learnings["wins"] += 1
            elif profit < 0:
                learnings["losses"] += 1

        # Métricas
        if trades:
            learnings["win_rate"] = learnings["wins"] / len(trades)
            learnings["avg_profit"] = sum(profits) / len(profits) if profits else 0
            learnings["total_profit"] = sum(profits)

        # Identificar problemas
        if learnings["win_rate"] < 0.30:
            learnings["critical_issues"].append(
                f"⚠️ CRÍTICO: Win rate de {learnings['win_rate']:.1%} - abaixo do mínimo (30%)"
            )
            learnings["suggestions"].append(
                "AÇÃO: Reduzir tamanho de posição em 75% até win rate estabilizar"
            )

        elif learnings["win_rate"] < 0.40:
            learnings["common_mistakes"].append(
                f"Win rate de {learnings['win_rate']:.1%} - abaixo do target (45%)"
            )
            learnings["suggestions"].append(
                "Revisar sinais de entrada - possível excesso de trades"
            )

        if learnings["avg_profit"] < 0:
            learnings["critical_issues"].append(
                f"⚠️ CRÍTICO: Lucro médio negativo (${learnings['avg_profit']:.2f})"
            )
            learnings["suggestions"].append(
                "AÇÃO: Ajustar stop-loss ou revisar estratégia completamente"
            )

        # Padrões positivos
        if learnings["win_rate"] >= 0.50:
            learnings["positive_patterns"].append(
                f"✅ Win rate saudável ({learnings['win_rate']:.1%})"
            )

        if learnings["avg_profit"] > 0.01:  # >1% avg profit
            learnings["positive_patterns"].append(
                f"✅ Lucro médio positivo (${learnings['avg_profit']:.2f})"
            )

        # Análise de loss streaks
        current_streak = 0
        max_loss_streak = 0

        for profit in reversed(profits):  # Mais recente primeiro
            if profit < 0:
                current_streak += 1
                max_loss_streak = max(max_loss_streak, current_streak)
            else:
                current_streak = 0

        if max_loss_streak >= 5:
            learnings["common_mistakes"].append(
                f"Loss streak de {max_loss_streak} trades detectado"
            )
            learnings["suggestions"].append(
                "Considerar pause temporário para revisão de estratégia"
            )

        # Análise de erros
        if errors:
            learnings["recent_errors"] = len(errors)
            learnings["suggestions"].append(f"Revisar {len(errors)} erros recentes nos logs")

        return learnings

    async def _log_learnings(self, learnings: Dict) -> None:
        """
        Salva reflexão em memória episódica.

        Args:
            learnings: Dict com análise e learnings
        """
        timestamp = datetime.utcnow().strftime("%Y-%m-%d_%H%M")
        filename = self.memory_path / f"{timestamp}_reflection.md"

        # Gerar conteúdo markdown
        content = self._generate_markdown_report(learnings)

        # Salvar arquivo
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)

            print(f"[REFLECTION] 📝 Log salvo: {filename}")

            # Também salvar no MongoDB para histórico
            await self.db.reflections.insert_one(
                {
                    **learnings,
                    "timestamp": datetime.utcnow(),
                    "reflection_number": self.total_reflections,
                }
            )

        except Exception as e:
            print(f"[REFLECTION] ⚠️ Erro ao salvar log: {e}")

    def _generate_markdown_report(self, learnings: Dict) -> str:
        """Gera relatório markdown da reflexão."""
        timestamp = learnings["timestamp"]

        content = f"""# 🪞 Auto-Reflexão: {timestamp}

**Reflexão #{self.total_reflections + 1}**

## 📊 Métricas ({learnings['total_trades']} trades analisados)

- **Wins:** {learnings['wins']}
- **Losses:** {learnings['losses']}
- **Win Rate:** {learnings['win_rate']:.2%}
- **Lucro Médio:** ${learnings['avg_profit']:.4f}
- **Lucro Total:** ${learnings['total_profit']:.4f}

"""

        # Issues críticos
        if learnings.get("critical_issues"):
            content += "## 🚨 ISSUES CRÍTICOS\n\n"
            for issue in learnings["critical_issues"]:
                content += f"- {issue}\n"
            content += "\n"

        # Erros comuns
        if learnings.get("common_mistakes"):
            content += "## ⚠️ Pontos de Atenção\n\n"
            for mistake in learnings["common_mistakes"]:
                content += f"- {mistake}\n"
            content += "\n"

        # Padrões positivos
        if learnings.get("positive_patterns"):
            content += "## ✅ Padrões Positivos\n\n"
            for pattern in learnings["positive_patterns"]:
                content += f"- {pattern}\n"
            content += "\n"

        # Sugestões
        if learnings.get("suggestions"):
            content += "## 💡 Ações Sugeridas\n\n"
            for suggestion in learnings["suggestions"]:
                content += f"- {suggestion}\n"
            content += "\n"

        # Ações tomadas
        if learnings.get("actions_taken"):
            content += "## 🔧 Ações Tomadas Automaticamente\n\n"
            for action in learnings["actions_taken"]:
                content += f"- {action}\n"
            content += "\n"

        content += """---
*Auto-gerado por Self-Reflection Service*
*quant-sentinel-e7450*
"""

        return content

    async def _apply_safe_corrections(self, learnings: Dict) -> List[str]:
        """
        Aplica correções automáticas SEGURAS baseado em learnings.

        RULE: Só aplicar correções que NÃO envolvem risco financeiro direto.

        Args:
            learnings: Dict com análise

        Returns:
            Lista de ações tomadas
        """
        actions = []

        # Circuit breaker: Win rate crítico
        if learnings["win_rate"] < 0.30 and learnings["total_trades"] >= 10:
            try:
                # Pausar bot (sem deletar ordens existentes)
                await self.db.config.update_one(
                    {},
                    {
                        "$set": {
                            "bot_paused": True,
                            "pause_reason": "win_rate_critical",
                            "pause_timestamp": datetime.utcnow(),
                        }
                    },
                    upsert=True,
                )

                actions.append(
                    "⚠️ BOT PAUSADO: Win rate crítico (<30%). "
                    "Requer análise humana antes de reativar."
                )

                self.critical_alerts += 1

            except Exception as e:
                print(f"[REFLECTION] Erro ao pausar bot: {e}")

        # Nota: Mais correções podem ser adicionadas aqui
        # Mas sempre seguir regra: SAFE ONLY (sem risco financeiro)

        return actions

    async def get_status(self) -> Dict:
        """
        Retorna status do serviço de reflexão.

        Returns:
            Dict com estatísticas
        """
        return {
            "last_reflection": self.last_reflection.isoformat() if self.last_reflection else None,
            "next_reflection": (
                (self.last_reflection + self.interval).isoformat()
                if self.last_reflection
                else "soon"
            ),
            "total_reflections": self.total_reflections,
            "critical_alerts": self.critical_alerts,
            "interval_minutes": self.interval.total_seconds() / 60,
        }

    def _save_state(self) -> None:
        """
        💾 Persistir estado atual para sobreviver restarts.
        Pattern aprendido da skill self-reflection (ClawdHub).
        """
        try:
            state = {
                "last_reflection_timestamp": (
                    self.last_reflection.isoformat() if self.last_reflection else None
                ),
                "total_reflections": self.total_reflections,
                "critical_alerts": self.critical_alerts,
                "interval_minutes": int(self.interval.total_seconds() / 60),
                "saved_at": datetime.utcnow().isoformat(),
            }

            self.state_file.write_text(json.dumps(state, indent=2))
            print(f"[REFLECTION] 💾 Estado salvo: {self.total_reflections} reflexões")

        except Exception as e:
            print(f"[REFLECTION] ⚠️ Erro ao salvar estado: {e}")

    def _load_state(self) -> None:
        """
        📂 Carregar estado persistido de execução anterior.
        Pattern aprendido da skill self-reflection (ClawdHub).
        """
        try:
            if not self.state_file.exists():
                print("[REFLECTION] 🆕 Primeira execução - sem estado anterior")
                return

            state = json.loads(self.state_file.read_text())

            if state.get("last_reflection_timestamp"):
                self.last_reflection = datetime.fromisoformat(state["last_reflection_timestamp"])

            self.total_reflections = state.get("total_reflections", 0)
            self.critical_alerts = state.get("critical_alerts", 0)

            print(
                f"[REFLECTION] 📂 Estado carregado: {self.total_reflections} reflexões anteriores"
            )

            if self.last_reflection:
                elapsed = datetime.utcnow() - self.last_reflection
                print(f"[REFLECTION] ⏱️ Última reflexão: {elapsed} atrás")

        except Exception as e:
            print(f"[REFLECTION] ⚠️ Erro ao carregar estado: {e} - iniciando do zero")
            self.total_reflections = 0
            self.critical_alerts = 0
            self.last_reflection = None
