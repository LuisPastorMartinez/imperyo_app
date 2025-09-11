# pages/pedido/__init__.py
from .crear_pedido import show_create
from .consultar_pedidos import show_consult
from .modificar_pedido import show_modify
from .eliminar_pedido import show_delete

__all__ = ["show_create", "show_consult", "show_modify", "show_delete"]
