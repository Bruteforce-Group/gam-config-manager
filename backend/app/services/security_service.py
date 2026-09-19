"""Security analysis service"""
from typing import Dict, Any, List
from app.db.models import SeverityLevel, ConfigType


class SecurityRule:
    """Base class for security rules"""
    
    def __init__(self, severity: SeverityLevel, category: str):
        self.severity = severity
        self.category = category
    
    def analyze(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze configuration and return findings"""
        raise NotImplementedError


class TwoFactorAuthRule(SecurityRule):
    """Check for 2FA enforcement"""
    
    def __init__(self):
        super().__init__(SeverityLevel.HIGH, "Authentication")
    
    def analyze(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        findings = []
        
        # Check if config contains user data
        if "user" in config or "users" in config:
            users_data = config.get("users", [config.get("user")])
            
            for user in users_data:
                if isinstance(user, dict):
                    if not user.get("isEnforcedIn2Sv", False):
                        user_email = user.get('primaryEmail', 'unknown')
                        findings.append({
                            "title": "Two-Factor Authentication Not Enforced",
                            "description": f"User {user_email} does not have 2FA enforced",
                            "recommendation": "Enable 2FA enforcement for all users to improve account security",
                            "affected_settings": {"user": user_email},
                            "remediation_steps": [
                                "Go to Admin Console > Security > 2-Step Verification",
                                "Select 'Enforce 2-Step Verification'",
                                "Set appropriate enforcement date"
                            ],
                            "remediation_actions": [
                                {
                                    "action_id": "enforce_2fa",
                                    "label": "Enforce 2FA for this user",
                                    "description": f"Run GAM command to enforce 2FA for {user_email}",
                                    "gam_command": ["update", "user", user_email, "enforcein2sv", "true"],
                                    "requires_confirmation": True,
                                    "parameters": {"user_email": user_email}
                                }
                            ]
                        })
        
        return findings


class PasswordPolicyRule(SecurityRule):
    """Check password policy settings"""
    
    def __init__(self):
        super().__init__(SeverityLevel.MEDIUM, "Authentication")
    
    def analyze(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        findings = []
        
        # Check password length
        min_length = config.get("passwordLengthMin", 8)
        if min_length < 12:
            findings.append({
                "title": "Weak Password Length Requirement",
                "description": f"Minimum password length is set to {min_length} characters",
                "recommendation": "Set minimum password length to at least 12 characters",
                "affected_settings": {"passwordLengthMin": min_length},
                "remediation_steps": [
                    "Go to Admin Console > Security > Password management",
                    "Set minimum password length to 12 or more characters"
                ]
            })
        
        # Check password expiration
        if config.get("passwordExpiration", 0) == 0:
            findings.append({
                "title": "No Password Expiration Policy",
                "description": "Passwords are set to never expire",
                "recommendation": "Consider implementing password expiration (e.g., 90 days) or use strong alternative controls",
                "affected_settings": {"passwordExpiration": 0},
                "remediation_steps": [
                    "Go to Admin Console > Security > Password management",
                    "Set password expiration policy (recommended: 90 days)",
                    "Alternatively, ensure strong 2FA enforcement is in place"
                ]
            })
        
        return findings


class ExternalSharingRule(SecurityRule):
    """Check external sharing settings"""
    
    def __init__(self):
        super().__init__(SeverityLevel.HIGH, "Data Protection")
    
    def analyze(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        findings = []
        
        # Check Drive sharing settings
        if "drive" in config:
            drive_config = config["drive"]
            
            if drive_config.get("externalSharingEnabled", True):
                findings.append({
                    "title": "External Sharing Enabled",
                    "description": "Drive allows sharing files with external users",
                    "recommendation": "Review and restrict external sharing permissions if not required",
                    "affected_settings": {"externalSharingEnabled": True},
                    "remediation_steps": [
                        "Go to Admin Console > Apps > Google Workspace > Drive and Docs",
                        "Review sharing settings",
                        "Restrict external sharing if not needed for business operations"
                    ]
                })
        
        return findings


class AdminRoleRule(SecurityRule):
    """Check for excessive admin privileges"""
    
    def __init__(self):
        super().__init__(SeverityLevel.CRITICAL, "Access Control")
    
    def analyze(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        findings = []
        
        # Check for super admin assignments
        if "users" in config:
            super_admins = [
                user for user in config["users"]
                if isinstance(user, dict) and user.get("isAdmin", False)
            ]
            
            if len(super_admins) > 3:
                findings.append({
                    "title": "Excessive Super Admin Assignments",
                    "description": f"Found {len(super_admins)} super admin accounts",
                    "recommendation": "Limit super admin access to minimum necessary personnel",
                    "affected_settings": {"superAdminCount": len(super_admins)},
                    "remediation_steps": [
                        "Review all super admin accounts",
                        "Remove unnecessary super admin privileges",
                        "Use delegated admin roles where possible"
                    ]
                })
        
        return findings


class MobileDeviceSecurityRule(SecurityRule):
    """Check mobile device security settings"""
    
    def __init__(self):
        super().__init__(SeverityLevel.HIGH, "Mobile Security")
    
    def analyze(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        findings = []
        
        # Check if config contains mobile device data
        devices_data = config.get("mobile", [])
        if not isinstance(devices_data, list):
            return findings
        
        for device in devices_data:
            if not isinstance(device, dict):
                continue
            
            device_id = device.get("deviceId", "Unknown")
            user_email = device.get("email", "Unknown")
            
            # Check for unencrypted devices
            if device.get("encryptionStatus") != "On":
                findings.append({
                    "title": "Unencrypted Mobile Device Detected",
                    "description": f"Device {device_id} for user {user_email} is not encrypted",
                    "recommendation": "Require device encryption for all mobile devices accessing corporate data",
                    "affected_settings": {"device": device_id, "user": user_email},
                    "remediation_steps": [
                        "Contact user to enable device encryption",
                        "Enforce encryption policy in Mobile Device Management",
                        "Consider blocking unencrypted devices"
                    ]
                })
            
            # Check for compromised devices
            if device.get("deviceCompromisedStatus") not in ["Undetected", "No compromise detected", ""]:
                findings.append({
                    "title": "Compromised Mobile Device Detected",
                    "description": f"Device {device_id} for user {user_email} shows signs of compromise",
                    "recommendation": "Immediately investigate and potentially wipe the device",
                    "affected_settings": {"device": device_id, "user": user_email, "status": device.get("deviceCompromisedStatus")},
                    "remediation_steps": [
                        "Immediately contact the user",
                        "Revoke device access",
                        "Perform security assessment",
                        "Remote wipe if necessary"
                    ]
                })
            
            # Check for devices without passwords
            if device.get("devicePasswordStatus") != "On":
                findings.append({
                    "title": "Mobile Device Without Password",
                    "description": f"Device {device_id} for user {user_email} does not have a password set",
                    "recommendation": "Require device passwords/PINs for all mobile devices",
                    "affected_settings": {"device": device_id, "user": user_email},
                    "remediation_steps": [
                        "Enable password policy in Mobile Device Management",
                        "Require minimum password complexity",
                        "Set password expiration if needed"
                    ]
                })
        
        return findings


class OAuthTokenSecurityRule(SecurityRule):
    """Check OAuth token security"""
    
    def __init__(self):
        super().__init__(SeverityLevel.CRITICAL, "Third-Party Access")
    
    def analyze(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        findings = []
        
        # Check if config contains OAuth token data
        tokens_data = config.get("oauth_tokens", [])
        if not isinstance(tokens_data, list):
            return findings
        
        # High-risk scopes to watch for
        high_risk_scopes = [
            "https://www.googleapis.com/auth/drive",
            "https://mail.google.com/",
            "https://www.googleapis.com/auth/admin.directory",
            "https://www.googleapis.com/auth/gmail.modify"
        ]
        
        for token in tokens_data:
            if not isinstance(token, dict):
                continue
            
            display_text = token.get("displayText", "Unknown App")
            client_id = token.get("clientId", "Unknown")
            scopes = token.get("scopes", "")
            user_key = token.get("userKey", "Unknown")
            
            # Check for high-risk scopes
            has_high_risk = any(risk_scope in scopes for risk_scope in high_risk_scopes)
            
            if has_high_risk:
                findings.append({
                    "title": "Third-Party App with Sensitive Permissions",
                    "description": f"App '{display_text}' has access to sensitive data for user {user_key}",
                    "recommendation": "Review and revoke access for unnecessary third-party applications",
                    "affected_settings": {"app": display_text, "user": user_key, "client_id": client_id},
                    "remediation_steps": [
                        "Review the app's necessity",
                        "Check if app is from trusted vendor",
                        "Revoke if not needed: Go to Admin Console > Security > API controls",
                        "Consider using approved apps list"
                    ],
                    "remediation_actions": [
                        {
                            "action_id": "revoke_oauth_token",
                            "label": "Revoke Access for this App",
                            "description": f"Revoke OAuth access for '{display_text}' from user {user_key}",
                            "gam_command": ["user", user_key, "revoke", "token", client_id],
                            "requires_confirmation": True,
                            "parameters": {"user": user_key, "client_id": client_id, "app_name": display_text}
                        }
                    ]
                })
        
        # Warn if too many apps have access
        if len(tokens_data) > 10:
            findings.append({
                "title": "Excessive Third-Party App Access",
                "description": f"Found {len(tokens_data)} third-party apps with OAuth access",
                "recommendation": "Audit and limit third-party app access to necessary applications only",
                "affected_settings": {"total_apps": len(tokens_data)},
                "remediation_steps": [
                    "Review all authorized applications",
                    "Revoke unused or unnecessary apps",
                    "Implement app approval workflow",
                    "Enable API access controls"
                ]
            })
        
        return findings


class AdminRoleAssignmentRule(SecurityRule):
    """Check admin role assignments for security issues"""
    
    def __init__(self):
        super().__init__(SeverityLevel.HIGH, "Access Control")
    
    def analyze(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        findings = []
        
        # Check if config contains admin role data
        roles_data = config.get("admin_roles", [])
        if not isinstance(roles_data, list):
            return findings
        
        # Count custom roles vs system roles
        custom_roles = [r for r in roles_data if isinstance(r, dict) and r.get("isSuperAdminRole") == "False"]
        
        # Check for overly broad custom roles
        for role in roles_data:
            if not isinstance(role, dict):
                continue
            
            role_name = role.get("roleName", "Unknown")
            privileges = role.get("rolePrivileges", "")
            
            # Check if role has too many privileges (basic heuristic)
            if isinstance(privileges, str) and len(privileges) > 1000:
                findings.append({
                    "title": "Overly Broad Admin Role",
                    "description": f"Admin role '{role_name}' has extensive privileges",
                    "recommendation": "Follow least privilege principle - limit admin role permissions to only what's necessary",
                    "affected_settings": {"role": role_name},
                    "remediation_steps": [
                        "Review the role's privileges",
                        "Remove unnecessary permissions",
                        "Split into multiple focused roles if needed",
                        "Audit who has this role assigned"
                    ]
                })
        
        return findings


class SecurityService:
    """Service for analyzing security configurations"""
    
    def __init__(self):
        self.rules = [
            TwoFactorAuthRule(),
            PasswordPolicyRule(),
            ExternalSharingRule(),
            AdminRoleRule(),
            MobileDeviceSecurityRule(),
            OAuthTokenSecurityRule(),
            AdminRoleAssignmentRule(),
        ]
    
    def analyze_configuration(
        self,
        config_data: Dict[str, Any],
        config_type: ConfigType
    ) -> List[Dict[str, Any]]:
        """Analyze configuration and return security findings"""
        all_findings = []
        
        for rule in self.rules:
            try:
                findings = rule.analyze(config_data)
                for finding in findings:
                    finding["severity"] = rule.severity
                    finding["category"] = rule.category
                all_findings.extend(findings)
            except Exception as e:
                # Log error but continue with other rules
                print(f"Error in rule {rule.__class__.__name__}: {str(e)}")
        
        return all_findings
    
    def get_security_score(self, findings: List[Dict[str, Any]]) -> int:
        """Calculate a security score (0-100) based on findings"""
        if not findings:
            return 100
        
        # Deduct points based on severity
        deductions = {
            SeverityLevel.CRITICAL: 25,
            SeverityLevel.HIGH: 15,
            SeverityLevel.MEDIUM: 10,
            SeverityLevel.LOW: 5,
            SeverityLevel.INFO: 2,
        }
        
        total_deduction = sum(
            deductions.get(finding.get("severity", SeverityLevel.INFO), 0)
            for finding in findings
        )
        
        score = max(0, 100 - total_deduction)
        return score

