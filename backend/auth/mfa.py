"""
Multi-Factor Authentication (MFA) for CEP Machine
Production-ready TOTP-based MFA with backup codes
"""

import pyotp
import qrcode
import qrcode.image.svg
from io import BytesIO
import base64
import secrets
import hashlib
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class MFAService:
    """Multi-Factor Authentication service using TOTP"""
    
    def __init__(self):
        self.issuer = "CEP Machine"
        self.digits = 6
        self.interval = 30  # seconds
        self.valid_window = 1  # Allow 1 interval before/after
    
    def generate_secret(self) -> str:
        """Generate a new TOTP secret"""
        return pyotp.random_base32()
    
    def generate_totp_uri(self, user_email: str, secret: str) -> str:
        """Generate TOTP provisioning URI"""
        totp = pyotp.TOTP(secret, digits=self.digits, interval=self.interval)
        return totp.provisioning_uri(
            name=user_email,
            issuer_name=self.issuer
        )
    
    def generate_qr_code(self, user_email: str, secret: str, format: str = "png") -> bytes:
        """Generate QR code for TOTP setup"""
        totp_uri = self.generate_totp_uri(user_email, secret)
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4
        )
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        if format == "svg":
            img = qr.make_image(image_factory=qrcode.image.svg.SvgImage)
        else:
            img = qr.make_image(fill_color="black", back_color="white")
        
        buffer = BytesIO()
        img.save(buffer)
        return buffer.getvalue()
    
    def generate_qr_code_base64(self, user_email: str, secret: str) -> str:
        """Generate QR code as base64 string for embedding in HTML"""
        qr_bytes = self.generate_qr_code(user_email, secret, format="png")
        return base64.b64encode(qr_bytes).decode('utf-8')
    
    def verify_token(self, secret: str, token: str) -> bool:
        """Verify a TOTP token"""
        if not secret or not token:
            return False
        
        try:
            # Clean token (remove spaces)
            token = token.replace(" ", "").replace("-", "")
            
            if len(token) != self.digits:
                return False
            
            totp = pyotp.TOTP(secret, digits=self.digits, interval=self.interval)
            return totp.verify(token, valid_window=self.valid_window)
        except Exception as e:
            logger.error(f"MFA verification error: {str(e)}")
            return False
    
    def get_current_token(self, secret: str) -> str:
        """Get current TOTP token (for testing purposes)"""
        totp = pyotp.TOTP(secret, digits=self.digits, interval=self.interval)
        return totp.now()
    
    def generate_backup_codes(self, count: int = 8) -> List[str]:
        """Generate backup codes for account recovery"""
        codes = []
        for _ in range(count):
            # Generate 8-character alphanumeric codes
            code = secrets.token_hex(4).upper()
            # Format as XXXX-XXXX
            formatted_code = f"{code[:4]}-{code[4:]}"
            codes.append(formatted_code)
        return codes
    
    def hash_backup_code(self, code: str) -> str:
        """Hash a backup code for storage"""
        # Normalize code (remove dashes, uppercase)
        normalized = code.replace("-", "").upper()
        return hashlib.sha256(normalized.encode()).hexdigest()
    
    def verify_backup_code(self, code: str, hashed_codes: List[str]) -> Optional[str]:
        """Verify a backup code against stored hashes, return the matched hash if valid"""
        hashed_input = self.hash_backup_code(code)
        
        for stored_hash in hashed_codes:
            if secrets.compare_digest(hashed_input, stored_hash):
                return stored_hash
        
        return None
    
    def setup_mfa(self, user_email: str) -> Dict[str, Any]:
        """Set up MFA for a user"""
        secret = self.generate_secret()
        backup_codes = self.generate_backup_codes()
        hashed_backup_codes = [self.hash_backup_code(code) for code in backup_codes]
        qr_code_base64 = self.generate_qr_code_base64(user_email, secret)
        
        return {
            "secret": secret,
            "backup_codes": backup_codes,
            "hashed_backup_codes": hashed_backup_codes,
            "qr_code_base64": qr_code_base64,
            "totp_uri": self.generate_totp_uri(user_email, secret),
            "setup_at": datetime.utcnow().isoformat()
        }
    
    def verify_mfa(
        self, 
        secret: str, 
        token: str, 
        hashed_backup_codes: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Verify MFA token or backup code"""
        # First try TOTP
        if self.verify_token(secret, token):
            return {
                "valid": True,
                "method": "totp",
                "used_backup_code": None
            }
        
        # Try backup codes if provided
        if hashed_backup_codes:
            matched_hash = self.verify_backup_code(token, hashed_backup_codes)
            if matched_hash:
                return {
                    "valid": True,
                    "method": "backup_code",
                    "used_backup_code": matched_hash
                }
        
        return {
            "valid": False,
            "method": None,
            "used_backup_code": None
        }

class MFAManager:
    """Manager for MFA operations with user storage"""
    
    def __init__(self):
        self.mfa_service = MFAService()
        # In production, this would be database-backed
        self._user_mfa_data: Dict[str, Dict[str, Any]] = {}
    
    async def enable_mfa(self, user_id: str, user_email: str) -> Dict[str, Any]:
        """Enable MFA for a user"""
        setup_data = self.mfa_service.setup_mfa(user_email)
        
        # Store MFA data (in production, save to database)
        self._user_mfa_data[user_id] = {
            "secret": setup_data["secret"],
            "hashed_backup_codes": setup_data["hashed_backup_codes"],
            "enabled": False,  # Not enabled until verified
            "setup_at": setup_data["setup_at"]
        }
        
        # Return setup info (don't include secret in response for security)
        return {
            "qr_code_base64": setup_data["qr_code_base64"],
            "backup_codes": setup_data["backup_codes"],
            "message": "Scan the QR code with your authenticator app, then verify with a code"
        }
    
    async def verify_and_enable_mfa(self, user_id: str, token: str) -> Dict[str, Any]:
        """Verify MFA setup and enable it"""
        if user_id not in self._user_mfa_data:
            return {"success": False, "error": "MFA not set up for this user"}
        
        mfa_data = self._user_mfa_data[user_id]
        
        if self.mfa_service.verify_token(mfa_data["secret"], token):
            mfa_data["enabled"] = True
            mfa_data["enabled_at"] = datetime.utcnow().isoformat()
            return {"success": True, "message": "MFA enabled successfully"}
        
        return {"success": False, "error": "Invalid verification code"}
    
    async def verify_mfa(self, user_id: str, token: str) -> Dict[str, Any]:
        """Verify MFA for login"""
        if user_id not in self._user_mfa_data:
            return {"valid": False, "error": "MFA not enabled for this user"}
        
        mfa_data = self._user_mfa_data[user_id]
        
        if not mfa_data.get("enabled"):
            return {"valid": False, "error": "MFA not enabled for this user"}
        
        result = self.mfa_service.verify_mfa(
            mfa_data["secret"],
            token,
            mfa_data.get("hashed_backup_codes")
        )
        
        # If backup code was used, remove it
        if result["valid"] and result["used_backup_code"]:
            mfa_data["hashed_backup_codes"].remove(result["used_backup_code"])
            logger.info(f"Backup code used for user {user_id}")
        
        return result
    
    async def disable_mfa(self, user_id: str, token: str) -> Dict[str, Any]:
        """Disable MFA for a user (requires valid token)"""
        if user_id not in self._user_mfa_data:
            return {"success": False, "error": "MFA not enabled for this user"}
        
        mfa_data = self._user_mfa_data[user_id]
        
        # Verify token before disabling
        if not self.mfa_service.verify_token(mfa_data["secret"], token):
            return {"success": False, "error": "Invalid verification code"}
        
        del self._user_mfa_data[user_id]
        logger.info(f"MFA disabled for user {user_id}")
        
        return {"success": True, "message": "MFA disabled successfully"}
    
    async def regenerate_backup_codes(self, user_id: str, token: str) -> Dict[str, Any]:
        """Regenerate backup codes (requires valid token)"""
        if user_id not in self._user_mfa_data:
            return {"success": False, "error": "MFA not enabled for this user"}
        
        mfa_data = self._user_mfa_data[user_id]
        
        # Verify token before regenerating
        if not self.mfa_service.verify_token(mfa_data["secret"], token):
            return {"success": False, "error": "Invalid verification code"}
        
        new_codes = self.mfa_service.generate_backup_codes()
        mfa_data["hashed_backup_codes"] = [
            self.mfa_service.hash_backup_code(code) for code in new_codes
        ]
        
        return {
            "success": True,
            "backup_codes": new_codes,
            "message": "New backup codes generated. Store them securely."
        }
    
    def is_mfa_enabled(self, user_id: str) -> bool:
        """Check if MFA is enabled for a user"""
        if user_id not in self._user_mfa_data:
            return False
        return self._user_mfa_data[user_id].get("enabled", False)

# Global instances
mfa_service = MFAService()
mfa_manager = MFAManager()
