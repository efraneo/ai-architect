"""
=========================================================
Health Monitor

Qué está en pie y qué no.
=========================================================

Estaba huérfano, y mientras tanto ``architect doctor`` —el comando que el
README manda ejecutar primero— devolvía esto:

    {"success": True, "python": ..., "platform": ..., "status": "healthy"}

Respondía ``"healthy"`` **siempre**, sin comprobar nada: sin una sola clave
de proveedor configurada, sin git instalado, con lo que fuera. Un chequeo
que no puede dar mal no es un chequeo.

Los componentes ya sabían responder —``ProviderManager.health()`` informa
``not_configured``, ``AgentManager.health()`` cuenta los agentes—; lo que
faltaba era alguien que los juntara.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol, runtime_checkable

# Estados que un componente puede reportar y que NO son estar bien. Se
# comparan en minúsculas: cada componente los escribe a su manera.
ESTADOS_MALOS = {"error", "failed", "not_configured", "unavailable", "down"}


@runtime_checkable
class Componente(Protocol):
    """Lo que hace falta para poder preguntarle a algo por su salud.

    Es la misma forma que declara ``core/contracts.Component``: un nombre y
    un ``health()``. ``ProviderManager`` y ``AgentManager`` ya la cumplen.
    """

    def health(self) -> dict[str, Any]: ...


class Health:
    def __init__(self) -> None:
        self.components: dict[str, Any] = {}

        self.started = datetime.utcnow()

    def register(
        self,
        component: Any,
        name: str | None = None,
    ) -> None:
        """Añade un componente al informe.

        El nombre se puede dar aparte: ``AgentManager`` no tiene atributo
        ``name``, y antes eso hacía reventar el registro con ``AttributeError``
        antes siquiera de llegar al informe.
        """
        clave = name or str(getattr(component, "name", type(component).__name__))

        self.components[clave] = component

    def check(
        self,
        name: str,
        ok: bool,
        detail: str = "",
    ) -> None:
        """Añade una comprobación suelta, sin componente detrás.

        Para lo que no es un objeto del proyecto: si git está instalado, si
        se puede escribir donde van los parches.
        """
        self.components[name] = _Comprobacion(ok, detail)

    def report(self) -> dict[str, Any]:
        resultado: dict[str, Any] = {}

        sanos = True

        for nombre, component in self.components.items():
            try:
                info = component.health()

            except Exception as exc:  # noqa: BLE001 - uno no tumba al informe
                info = {"status": "ERROR", "error": str(exc)}

            if not isinstance(info, dict):
                info = {"status": "OK", "value": info}

            if self._esta_mal(info):
                sanos = False

            resultado[nombre] = info

        return {
            "started": self.started.isoformat(),
            "healthy": sanos,
            "components": resultado,
        }

    @staticmethod
    def _esta_mal(info: dict[str, Any]) -> bool:
        """Un componente que dice ``not_configured`` no está sano.

        Antes solo contaba como fallo que ``health()`` lanzara. Un proveedor
        sin clave respondía educadamente y el informe seguía diciendo que
        todo iba bien.
        """
        return str(info.get("status", "OK")).strip().lower() in ESTADOS_MALOS


class _Comprobacion:
    """Envuelve un sí/no para que quepa en el mismo informe."""

    def __init__(self, ok: bool, detail: str = "") -> None:
        self.ok = ok
        self.detail = detail

    def health(self) -> dict[str, Any]:
        informe: dict[str, Any] = {"status": "OK" if self.ok else "unavailable"}

        if self.detail:
            informe["detail"] = self.detail

        return informe
