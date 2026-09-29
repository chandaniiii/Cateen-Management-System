"""
Campus Canteen Management System — Payment Processor Classes (OOP: Inheritance & Polymorphism)
Demonstrates abstract base class inheritance, polymorphic method execution,
and factory pattern instantiation for canteen payment workflows.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class BasePaymentHandler(ABC):
    """
    Abstract Base Class for Payment Handlers.
    Defines the contract and shared logic for payment processing.
    """

    def __init__(self, payment_method_code: str, display_name: str):
        self.code = payment_method_code
        self.display_name = display_name

    @abstractmethod
    def process_payment(self, amount: float, order_id: int) -> Dict[str, Any]:
        """
        Polymorphic method to process a transaction.
        Must be implemented by all concrete payment handler subclasses.
        """
        pass

    @abstractmethod
    def get_initial_payment_status(self) -> str:
        """Returns the initial payment status string: 'pending' or 'completed'."""
        pass


class CashPaymentHandler(BasePaymentHandler):
    """Handles Cash on Pickup transactions."""

    def __init__(self):
        super().__init__(payment_method_code="cash", display_name="Cash on Pickup")

    def get_initial_payment_status(self) -> str:
        # Cash is paid in person when picking up food
        return "pending"

    def process_payment(self, amount: float, order_id: int) -> Dict[str, Any]:
        return {
            "success": True,
            "method": self.code,
            "display_name": self.display_name,
            "amount": amount,
            "payment_status": self.get_initial_payment_status(),
            "transaction_id": f"CASH-ORD-{order_id}",
            "message": f"Please pay Rs. {amount:.0f} in cash at the counter upon food collection.",
        }


class EsewaPaymentHandler(BasePaymentHandler):
    """Handles eSewa Digital Wallet transactions (Simulated sandbox)."""

    def __init__(self):
        super().__init__(payment_method_code="esewa", display_name="eSewa Digital Wallet")

    def get_initial_payment_status(self) -> str:
        # Digital wallet payments are immediately completed in demo mode
        return "completed"

    def process_payment(self, amount: float, order_id: int) -> Dict[str, Any]:
        return {
            "success": True,
            "method": self.code,
            "display_name": self.display_name,
            "amount": amount,
            "payment_status": self.get_initial_payment_status(),
            "transaction_id": f"ESEWA-TXN-{order_id}-9841",
            "message": f"eSewa payment of Rs. {amount:.0f} was verified successfully.",
        }


class KhaltiPaymentHandler(BasePaymentHandler):
    """Handles Khalti Digital Wallet transactions (Simulated sandbox)."""

    def __init__(self):
        super().__init__(payment_method_code="khalti", display_name="Khalti Digital Wallet")

    def get_initial_payment_status(self) -> str:
        return "completed"

    def process_payment(self, amount: float, order_id: int) -> Dict[str, Any]:
        return {
            "success": True,
            "method": self.code,
            "display_name": self.display_name,
            "amount": amount,
            "payment_status": self.get_initial_payment_status(),
            "transaction_id": f"KHALTI-TXN-{order_id}-7712",
            "message": f"Khalti payment of Rs. {amount:.0f} was verified successfully.",
        }


class QRPaymentHandler(BasePaymentHandler):
    """Handles Fonepay / Dynamic QR Code transactions (Simulated sandbox)."""

    def __init__(self):
        super().__init__(payment_method_code="qr", display_name="Fonepay QR Code")

    def get_initial_payment_status(self) -> str:
        return "completed"

    def process_payment(self, amount: float, order_id: int) -> Dict[str, Any]:
        return {
            "success": True,
            "method": self.code,
            "display_name": self.display_name,
            "amount": amount,
            "payment_status": self.get_initial_payment_status(),
            "transaction_id": f"QR-FONEPAY-{order_id}-3301",
            "message": f"Fonepay QR payment of Rs. {amount:.0f} was verified successfully.",
        }


class PaymentProcessor:
    """
    Factory & Manager class for payment operations.
    Demonstrates OOP Factory Pattern and polymorphic execution.
    """

    _HANDLERS: Dict[str, BasePaymentHandler] = {
        "cash": CashPaymentHandler(),
        "esewa": EsewaPaymentHandler(),
        "khalti": KhaltiPaymentHandler(),
        "qr": QRPaymentHandler(),
    }

    @classmethod
    def get_handler(cls, payment_method: str) -> BasePaymentHandler:
        """Returns the appropriate polymorphic payment handler instance."""
        method_key = (payment_method or "").strip().lower()
        handler = cls._HANDLERS.get(method_key)
        if not handler:
            raise ValueError(
                f"Unsupported payment method '{payment_method}'. Allowed: {', '.join(cls._HANDLERS.keys())}"
            )
        return handler

    @classmethod
    def process_transaction(cls, payment_method: str, amount: float, order_id: int) -> Dict[str, Any]:
        """Polymorphically processes transaction using the registered handler."""
        handler = cls.get_handler(payment_method)
        return handler.process_payment(amount=amount, order_id=order_id)
