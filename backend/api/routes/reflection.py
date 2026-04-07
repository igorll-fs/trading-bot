"""
Rotas de Reflexão e Auto-Aperfeiçoamento

Self-reflection endpoints para monitorar e controlar o loop de aprendizado.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Callable

from motor.motor_asyncio import AsyncIOMotorDatabase


def create_reflection_router(db: AsyncIOMotorDatabase, reflection_service) -> APIRouter:
    """Cria router de reflexão."""

    router = APIRouter(prefix="/reflection", tags=["Reflection"])

    @router.get("/status")
    async def get_reflection_status() -> Dict:
        """
        Retorna status do serviço de auto-reflexão.

        Returns:
            Estatísticas do serviço
        """
        try:
            status = await reflection_service.get_status()
            return {"success": True, "data": status}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/trigger")
    async def trigger_reflection() -> Dict:
        """
        Força reflexão imediata (sem esperar intervalo).

        Returns:
            Learnings da reflexão
        """
        try:
            learnings = await reflection_service.reflect()

            return {"success": True, "message": "Reflexão completada", "data": learnings}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/history")
    async def get_reflection_history(limit: int = 10) -> Dict:
        """
        Retorna histórico de reflexões.

        Args:
            limit: Número de reflexões a retornar

        Returns:
            Lista de reflexões anteriores
        """
        try:
            reflections = await db.reflections.find(
                {}, sort=[("timestamp", -1)], limit=limit
            ).to_list(length=limit)

            # Convert ObjectId to string
            for ref in reflections:
                ref["_id"] = str(ref["_id"])
                if "timestamp" in ref:
                    ref["timestamp"] = ref["timestamp"].isoformat()

            return {"success": True, "count": len(reflections), "data": reflections}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    return router
