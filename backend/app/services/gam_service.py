"""GAM integration service"""
import subprocess
import json
import asyncio
from typing import Dict, Any, List, Optional
from app.core.config import settings
from app.db.models import ConfigType


class GAMService:
    """Service for interacting with GAM"""
    
    def __init__(self):
        self.gam_path = settings.GAM_PATH
        self.config_dir = settings.GAM_CONFIG_DIR
        self.domain = settings.GAM_DOMAIN
    
    async def _run_gam_command(self, args: List[str]) -> Dict[str, Any]:
        """Run a GAM command and return the result"""
        cmd = [self.gam_path]
        
        if self.config_dir:
            cmd.extend(["config", self.config_dir])
        
        cmd.extend(args)
        
        try:
            # Run command asynchronously
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown error"
                return {
                    "success": False,
                    "error": error_msg,
                    "data": None
                }
            
            # Try to parse JSON output
            try:
                data = json.loads(stdout.decode())
            except json.JSONDecodeError:
                # If not JSON, return as text
                data = stdout.decode()
            
            return {
                "success": True,
                "error": None,
                "data": data
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "data": None
            }
    
    async def extract_users(self) -> Dict[str, Any]:
        """Extract all user configurations"""
        result = await self._run_gam_command([
            "print", "users",
            "allfields",
            "formatjson"
        ])
        return result
    
    async def extract_groups(self) -> Dict[str, Any]:
        """Extract all group configurations"""
        result = await self._run_gam_command([
            "print", "groups",
            "settings",
            "formatjson"
        ])
        return result
    
    async def extract_org_units(self) -> Dict[str, Any]:
        """Extract organizational units"""
        result = await self._run_gam_command([
            "print", "orgs"
        ])
        
        # GAM returns CSV for orgs, not JSON
        if result["success"] and isinstance(result["data"], str):
            # Parse CSV to list of dicts
            import csv
            import io
            
            csv_data = result["data"]
            reader = csv.DictReader(io.StringIO(csv_data))
            orgs = list(reader)
            
            return {
                "success": True,
                "error": None,
                "data": orgs
            }
        
        return result
    
    async def extract_domain_settings(self) -> Dict[str, Any]:
        """Extract domain settings"""
        result = await self._run_gam_command([
            "info", "domain"
        ])
        
        # GAM returns text format for domain info
        if result["success"] and isinstance(result["data"], str):
            # Parse the text output into a dictionary
            lines = result["data"].strip().split('\n')
            domain_info = {}
            
            for line in lines:
                if ': ' in line:
                    key, value = line.split(': ', 1)
                    domain_info[key.strip()] = value.strip()
            
            return {
                "success": True,
                "error": None,
                "data": domain_info
            }
        
        return result
    
    async def extract_calendar_settings(self) -> Dict[str, Any]:
        """Extract calendar resource settings"""
        result = await self._run_gam_command([
            "print", "resources"
        ])
        
        # GAM returns CSV for resources
        if result["success"] and isinstance(result["data"], str):
            import csv
            import io
            
            csv_data = result["data"]
            reader = csv.DictReader(io.StringIO(csv_data))
            resources = list(reader)
            
            return {
                "success": True,
                "error": None,
                "data": resources
            }
        
        return result
    
    async def extract_gmail_settings(self, user_email: str) -> Dict[str, Any]:
        """Extract Gmail settings for a user"""
        result = await self._run_gam_command([
            "user", user_email,
            "show", "imap",
            "formatjson"
        ])
        return result
    
    async def extract_security_settings(self) -> Dict[str, Any]:
        """Extract security settings"""
        # This would extract various security-related settings
        # Including 2FA enforcement, password policies, etc.
        results = {}
        
        # Get 2FA enforcement
        twofa_result = await self._run_gam_command([
            "print", "users",
            "fields", "isEnforcedIn2Sv,isEnrolledIn2Sv",
            "formatjson"
        ])
        results["two_factor_auth"] = twofa_result
        
        return {
            "success": True,
            "error": None,
            "data": results
        }
    
    async def extract_all_configs(
        self,
        config_types: Optional[List[ConfigType]] = None
    ) -> Dict[str, Any]:
        """Extract all requested configuration types"""
        if not config_types:
            config_types = [
                ConfigType.USER,
                ConfigType.GROUP,
                ConfigType.OU,
                ConfigType.DOMAIN
            ]
        
        results = {}
        errors = []
        
        for config_type in config_types:
            try:
                if config_type == ConfigType.USER:
                    result = await self.extract_users()
                elif config_type == ConfigType.GROUP:
                    result = await self.extract_groups()
                elif config_type == ConfigType.OU:
                    result = await self.extract_org_units()
                elif config_type == ConfigType.DOMAIN:
                    result = await self.extract_domain_settings()
                elif config_type == ConfigType.CALENDAR:
                    result = await self.extract_calendar_settings()
                elif config_type == ConfigType.SECURITY:
                    result = await self.extract_security_settings()
                else:
                    continue
                
                if result["success"]:
                    results[config_type.value] = result["data"]
                else:
                    errors.append(f"{config_type.value}: {result['error']}")
            
            except Exception as e:
                errors.append(f"{config_type.value}: {str(e)}")
        
        return {
            "success": len(errors) == 0,
            "data": results,
            "errors": errors if errors else None
        }

