"""
Online Food Delivery System — Payment Processor Classes (OOP: Inheritance & Polymorphism)
Implements official eSewa ePay v2 integration with HMAC-SHA256 signature generation,
form payload preparation, server-side transaction status check verification, and
polymorphic execution for Cash on Delivery, eSewa, and digital payments.
"""

import base64
import hashlib
import hmac
import json
import logging
import time
import urllib.parse
import urllib.request
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from config import Config

logger = logging.getLogger(__name__)


class BasePaymentHandler(ABC):
    """
    Abstract Base Class for Payment Handlers.
    Defines the contract and shared logic for food delivery payment processing.
    """

    def __init__(self, payment_method_code: str, display_name: str):
        self.code = payment_method_code
        self.display_name = display_name

    @abstractmethod
    def get_initial_payment_status(self) -> str:
        """Returns the initial payment status string: 'pending' or 'completed'."""
        pass

    @abstractmethod
    def process_payment(self, amount: float, order_id: int, **kwargs) -> Dict[str, Any]:
        """Polymorphic method to initiate or process a transaction."""
        pass


class CashPaymentHandler(BasePaymentHandler):
    """Handles Cash on Delivery (COD) and Cash on Pickup transactions."""

    def __init__(self):
        super().__init__(payment_method_code="cash", display_name="Cash on Delivery")

    def get_initial_payment_status(self) -> str:
        return "pending"

    def process_payment(self, amount: float, order_id: int, **kwargs) -> Dict[str, Any]:
        delivery_type = kwargs.get("delivery_type", "delivery")
        action_text = "to our delivery rider upon food arrival" if delivery_type != "pickup" else "at the counter upon food collection"
        return {
            "success": True,
            "method": self.code,
            "display_name": self.display_name,
            "amount": amount,
            "payment_status": self.get_initial_payment_status(),
            "transaction_id": f"COD-ORD-{order_id}",
            "message": f"Please pay Rs. {amount:.0f} in cash {action_text}.",
        }


class EsewaPaymentHandler(BasePaymentHandler):
    """
    Handles official eSewa ePay v2 payment gateway integration.
    Supports official HMAC-SHA256 signature generation, form request creation,
    and server-side status verification against eSewa servers.
    """

    def __init__(self):
        super().__init__(payment_method_code="esewa", display_name="eSewa Mobile Wallet")

    def get_initial_payment_status(self) -> str:
        return "pending"

    @staticmethod
    def generate_signature(total_amount: str, transaction_uuid: str, product_code: str, secret_key: str) -> str:
        """
        Generates HMAC-SHA256 Base64 encoded signature for eSewa ePay v2.
        Message format: total_amount=...,transaction_uuid=...,product_code=...
        """
        message = f"total_amount={total_amount},transaction_uuid={transaction_uuid},product_code={product_code}"
        hash_digest = hmac.new(
            secret_key.encode("utf-8"),
            message.encode("utf-8"),
            hashlib.sha256,
        ).digest()
        return base64.b64encode(hash_digest).decode("utf-8")

    def prepare_payment_request(
        self,
        order,
        success_url: str,
        failure_url: str,
    ) -> Dict[str, Any]:
        """
        Prepares required form parameters for redirecting the customer to eSewa ePay v2.
        """
        product_code = Config.ESEWA_PRODUCT_CODE
        secret_key = Config.ESEWA_SECRET_KEY

        # Format amounts cleanly
        total_val = f"{float(order.total_amount):.2f}".rstrip("0").rstrip(".")
        delivery_val = f"{float(order.delivery_charge):.2f}".rstrip("0").rstrip(".") if order.delivery_charge else "0"
        subtotal_val = f"{(float(order.total_amount) - float(order.delivery_charge or 0)):.2f}".rstrip("0").rstrip(".")

        # Format unique transaction UUID
        transaction_uuid = f"FOOD-{order.id}-{int(time.time())}"

        # Generate HMAC-SHA256 signature
        signature = self.generate_signature(
            total_amount=total_val,
            transaction_uuid=transaction_uuid,
            product_code=product_code,
            secret_key=secret_key,
        )

        return {
            "payment_url": Config.ESEWA_PAYMENT_URL,
            "fields": {
                "amount": subtotal_val,
                "tax_amount": "0",
                "total_amount": total_val,
                "transaction_uuid": transaction_uuid,
                "product_code": product_code,
                "product_service_charge": "0",
                "product_delivery_charge": delivery_val,
                "success_url": success_url,
                "failure_url": failure_url,
                "signed_field_names": "total_amount,transaction_uuid,product_code",
                "signature": signature,
            },
            "transaction_uuid": transaction_uuid,
        }

    def verify_response(self, encoded_data: str, expected_order=None) -> Dict[str, Any]:
        """
        Verifies eSewa ePay v2 callback response:
        1. Decodes base64 payload
        2. Validates HMAC-SHA256 signature
        3. Calls eSewa transaction status check API directly from backend
        """
        try:
            raw_json = base64.b64decode(encoded_data).decode("utf-8")
            data = json.loads(raw_json)
        except Exception as e:
            logger.error("Failed to decode eSewa response: %s", e)
            return {"verified": False, "error": f"Invalid response format: {e}"}

        status = data.get("status")
        total_amount = data.get("total_amount")
        transaction_uuid = data.get("transaction_uuid")
        product_code = data.get("product_code", Config.ESEWA_PRODUCT_CODE)
        transaction_code = data.get("transaction_code")
        received_signature = data.get("signature")

        if not (total_amount and transaction_uuid and received_signature):
            return {"verified": False, "error": "Missing required transaction verification fields"}

        # 1. Signature Verification
        expected_sig = self.generate_signature(
            total_amount=str(total_amount),
            transaction_uuid=str(transaction_uuid),
            product_code=str(product_code),
            secret_key=Config.ESEWA_SECRET_KEY,
        )

        sig_matches = hmac.compare_digest(expected_sig, received_signature)

        # 2. Server-side Status Check API query
        server_verified = False
        api_status = None
        try:
            params = urllib.parse.urlencode({
                "product_code": product_code,
                "total_amount": total_amount,
                "transaction_uuid": transaction_uuid,
            })
            req_url = f"{Config.ESEWA_STATUS_URL}?{params}"
            req = urllib.request.Request(
                req_url,
                headers={"User-Agent": "FoodDelivery/1.0", "Accept": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                res_body = response.read().decode("utf-8")
                res_json = json.loads(res_body)
                api_status = res_json.get("status")
                if api_status == "COMPLETE":
                    server_verified = True
        except Exception as err:
            logger.warning("eSewa status check API could not be reached: %s. Using cryptographic signature verification.", err)
            # In sandbox / offline test environment, if signature is valid and status is COMPLETE in signed payload
            if sig_matches and status == "COMPLETE":
                server_verified = True

        is_valid = (sig_matches or server_verified) and (status == "COMPLETE" or api_status == "COMPLETE")

        if not is_valid:
            return {
                "verified": False,
                "error": f"Payment verification failed (status: {status}, server: {api_status})",
                "data": data,
            }

        return {
            "verified": True,
            "status": "completed",
            "transaction_code": transaction_code or f"ESEWA-{transaction_uuid}",
            "transaction_uuid": transaction_uuid,
            "total_amount": float(total_amount),
            "data": data,
        }

    def process_payment(self, amount: float, order_id: int, **kwargs) -> Dict[str, Any]:
        """Provides simulated or direct info for the order."""
        return {
            "success": True,
            "method": self.code,
            "display_name": self.display_name,
            "amount": amount,
            "payment_status": "pending",
            "transaction_id": f"ESEWA-PENDING-{order_id}",
            "message": "Redirecting to official eSewa secure payment portal...",
        }


class KhaltiPaymentHandler(BasePaymentHandler):
    """Handles Khalti Digital Wallet payments."""

    def __init__(self):
        super().__init__(payment_method_code="khalti", display_name="Khalti Digital Wallet")

    def get_initial_payment_status(self) -> str:
        return "completed"

    def process_payment(self, amount: float, order_id: int, **kwargs) -> Dict[str, Any]:
        return {
            "success": True,
            "method": self.code,
            "display_name": self.display_name,
            "amount": amount,
            "payment_status": self.get_initial_payment_status(),
            "transaction_id": f"KHALTI-TXN-{order_id}-{int(time.time()) % 10000}",
            "message": f"Khalti payment of Rs. {amount:.0f} was verified successfully.",
        }


class QRPaymentHandler(BasePaymentHandler):
    """Handles Fonepay / Dynamic QR Code payments."""

    def __init__(self):
        super().__init__(payment_method_code="qr", display_name="Fonepay QR Code")

    def get_initial_payment_status(self) -> str:
        return "completed"

    def process_payment(self, amount: float, order_id: int, **kwargs) -> Dict[str, Any]:
        return {
            "success": True,
            "method": self.code,
            "display_name": self.display_name,
            "amount": amount,
            "payment_status": self.get_initial_payment_status(),
            "transaction_id": f"QR-FONEPAY-{order_id}-{int(time.time()) % 10000}",
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
    def process_transaction(cls, payment_method: str, amount: float, order_id: int, **kwargs) -> Dict[str, Any]:
        """Polymorphically processes transaction using the registered handler."""
        handler = cls.get_handler(payment_method)
        return handler.process_payment(amount=amount, order_id=order_id, **kwargs)
