"""
Salesforce CRM Integration for CEP Machine
Production-ready Salesforce integration with lead and opportunity management
"""

import os
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class SalesforceIntegration:
    """
    Salesforce CRM integration for managing leads, contacts, and opportunities.
    Supports both sync and async operations.
    """
    
    def __init__(self):
        self.username = os.getenv('SALESFORCE_USERNAME', '')
        self.password = os.getenv('SALESFORCE_PASSWORD', '')
        self.security_token = os.getenv('SALESFORCE_SECURITY_TOKEN', '')
        self.domain = os.getenv('SALESFORCE_DOMAIN', 'login')
        self._sf = None
        self._connected = False
    
    def _connect(self):
        """Establish connection to Salesforce"""
        if self._connected and self._sf:
            return
        
        if not all([self.username, self.password, self.security_token]):
            logger.warning("Salesforce credentials not configured. Using mock mode.")
            self._connected = False
            return
        
        try:
            from simple_salesforce import Salesforce
            self._sf = Salesforce(
                username=self.username,
                password=self.password,
                security_token=self.security_token,
                domain=self.domain
            )
            self._connected = True
            logger.info("Connected to Salesforce successfully")
        except ImportError:
            logger.warning("simple-salesforce not installed. Using mock mode.")
            self._connected = False
        except Exception as e:
            logger.error(f"Failed to connect to Salesforce: {str(e)}")
            self._connected = False
    
    @property
    def is_connected(self) -> bool:
        return self._connected
    
    async def create_lead(self, prospect_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new lead in Salesforce"""
        self._connect()
        
        lead_data = {
            'FirstName': prospect_data.get('first_name', ''),
            'LastName': prospect_data.get('last_name', 'Unknown'),
            'Company': prospect_data.get('company', prospect_data.get('name', 'Unknown')),
            'Email': prospect_data.get('email', ''),
            'Phone': prospect_data.get('phone', ''),
            'LeadSource': prospect_data.get('source', 'CEP Machine'),
            'Industry': prospect_data.get('industry', ''),
            'Description': prospect_data.get('description', ''),
            'Street': prospect_data.get('address', ''),
            'City': prospect_data.get('city', ''),
            'State': prospect_data.get('state', ''),
            'PostalCode': prospect_data.get('postal_code', ''),
            'Country': prospect_data.get('country', ''),
            'Website': prospect_data.get('website', ''),
            'Status': 'New'
        }
        
        # Remove empty fields
        lead_data = {k: v for k, v in lead_data.items() if v}
        
        if not self._connected:
            # Mock response for development/testing
            mock_id = f"00Q{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            logger.info(f"Mock: Created lead {mock_id}")
            return {
                "success": True,
                "lead_id": mock_id,
                "message": "Lead created successfully (mock mode)",
                "data": lead_data
            }
        
        try:
            result = self._sf.Lead.create(lead_data)
            logger.info(f"Created Salesforce lead: {result['id']}")
            return {
                "success": True,
                "lead_id": result['id'],
                "message": "Lead created successfully",
                "data": lead_data
            }
        except Exception as e:
            logger.error(f"Failed to create lead: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "data": lead_data
            }
    
    async def update_lead(self, lead_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing lead"""
        self._connect()
        
        if not self._connected:
            logger.info(f"Mock: Updated lead {lead_id}")
            return {
                "success": True,
                "message": "Lead updated successfully (mock mode)",
                "lead_id": lead_id
            }
        
        try:
            self._sf.Lead.update(lead_id, update_data)
            logger.info(f"Updated Salesforce lead: {lead_id}")
            return {
                "success": True,
                "message": "Lead updated successfully",
                "lead_id": lead_id
            }
        except Exception as e:
            logger.error(f"Failed to update lead {lead_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "lead_id": lead_id
            }
    
    async def get_lead(self, lead_id: str) -> Dict[str, Any]:
        """Get a lead by ID"""
        self._connect()
        
        if not self._connected:
            return {
                "success": True,
                "lead": {
                    "Id": lead_id,
                    "FirstName": "Mock",
                    "LastName": "Lead",
                    "Company": "Mock Company",
                    "Status": "New"
                },
                "message": "Lead retrieved (mock mode)"
            }
        
        try:
            lead = self._sf.Lead.get(lead_id)
            return {
                "success": True,
                "lead": lead,
                "message": "Lead retrieved successfully"
            }
        except Exception as e:
            logger.error(f"Failed to get lead {lead_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "lead_id": lead_id
            }
    
    async def create_opportunity(self, opportunity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new opportunity"""
        self._connect()
        
        opp_data = {
            'Name': opportunity_data.get('name', 'New Opportunity'),
            'StageName': opportunity_data.get('stage', 'Prospecting'),
            'CloseDate': opportunity_data.get('close_date', datetime.utcnow().strftime('%Y-%m-%d')),
            'Amount': opportunity_data.get('amount', 0),
            'Description': opportunity_data.get('description', ''),
            'LeadSource': opportunity_data.get('source', 'CEP Machine'),
            'Type': opportunity_data.get('type', 'New Business'),
            'AccountId': opportunity_data.get('account_id'),
            'ContactId': opportunity_data.get('contact_id')
        }
        
        # Remove None values
        opp_data = {k: v for k, v in opp_data.items() if v is not None}
        
        if not self._connected:
            mock_id = f"006{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            logger.info(f"Mock: Created opportunity {mock_id}")
            return {
                "success": True,
                "opportunity_id": mock_id,
                "message": "Opportunity created successfully (mock mode)",
                "data": opp_data
            }
        
        try:
            result = self._sf.Opportunity.create(opp_data)
            logger.info(f"Created Salesforce opportunity: {result['id']}")
            return {
                "success": True,
                "opportunity_id": result['id'],
                "message": "Opportunity created successfully",
                "data": opp_data
            }
        except Exception as e:
            logger.error(f"Failed to create opportunity: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "data": opp_data
            }
    
    async def update_opportunity(self, opportunity_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing opportunity"""
        self._connect()
        
        if not self._connected:
            logger.info(f"Mock: Updated opportunity {opportunity_id}")
            return {
                "success": True,
                "message": "Opportunity updated successfully (mock mode)",
                "opportunity_id": opportunity_id
            }
        
        try:
            self._sf.Opportunity.update(opportunity_id, update_data)
            logger.info(f"Updated Salesforce opportunity: {opportunity_id}")
            return {
                "success": True,
                "message": "Opportunity updated successfully",
                "opportunity_id": opportunity_id
            }
        except Exception as e:
            logger.error(f"Failed to update opportunity {opportunity_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "opportunity_id": opportunity_id
            }
    
    async def query(self, soql_query: str) -> Dict[str, Any]:
        """Execute a SOQL query"""
        self._connect()
        
        if not self._connected:
            logger.info(f"Mock: Executed query")
            return {
                "success": True,
                "records": [],
                "total_size": 0,
                "message": "Query executed (mock mode)"
            }
        
        try:
            result = self._sf.query_all(soql_query)
            return {
                "success": True,
                "records": result['records'],
                "total_size": result['totalSize'],
                "message": "Query executed successfully"
            }
        except Exception as e:
            logger.error(f"Failed to execute query: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "query": soql_query
            }
    
    async def search_leads(
        self,
        company: Optional[str] = None,
        email: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Search for leads with filters"""
        conditions = []
        
        if company:
            conditions.append(f"Company LIKE '%{company}%'")
        if email:
            conditions.append(f"Email LIKE '%{email}%'")
        if status:
            conditions.append(f"Status = '{status}'")
        
        where_clause = " AND ".join(conditions) if conditions else "Id != null"
        
        query = f"""
            SELECT Id, FirstName, LastName, Company, Email, Phone, Status, LeadSource, CreatedDate
            FROM Lead
            WHERE {where_clause}
            ORDER BY CreatedDate DESC
            LIMIT {limit}
        """
        
        return await self.query(query)
    
    async def search_opportunities(
        self,
        stage: Optional[str] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Search for opportunities with filters"""
        conditions = []
        
        if stage:
            conditions.append(f"StageName = '{stage}'")
        if min_amount is not None:
            conditions.append(f"Amount >= {min_amount}")
        if max_amount is not None:
            conditions.append(f"Amount <= {max_amount}")
        
        where_clause = " AND ".join(conditions) if conditions else "Id != null"
        
        query = f"""
            SELECT Id, Name, StageName, Amount, CloseDate, LeadSource, CreatedDate
            FROM Opportunity
            WHERE {where_clause}
            ORDER BY CreatedDate DESC
            LIMIT {limit}
        """
        
        return await self.query(query)
    
    async def convert_lead_to_opportunity(
        self,
        lead_id: str,
        opportunity_name: Optional[str] = None,
        close_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Convert a lead to an opportunity"""
        self._connect()
        
        # Get lead data first
        lead_result = await self.get_lead(lead_id)
        
        if not lead_result.get("success"):
            return lead_result
        
        lead = lead_result.get("lead", {})
        
        # Create opportunity from lead
        opp_data = {
            "name": opportunity_name or f"Opportunity - {lead.get('Company', 'Unknown')}",
            "stage": "Qualification",
            "close_date": close_date or datetime.utcnow().strftime('%Y-%m-%d'),
            "source": lead.get("LeadSource", "CEP Machine"),
            "description": f"Converted from Lead: {lead_id}"
        }
        
        opp_result = await self.create_opportunity(opp_data)
        
        if opp_result.get("success"):
            # Update lead status
            await self.update_lead(lead_id, {"Status": "Converted"})
        
        return {
            "success": opp_result.get("success"),
            "lead_id": lead_id,
            "opportunity_id": opp_result.get("opportunity_id"),
            "message": "Lead converted to opportunity" if opp_result.get("success") else opp_result.get("error")
        }
    
    async def get_pipeline_summary(self) -> Dict[str, Any]:
        """Get a summary of the sales pipeline"""
        self._connect()
        
        if not self._connected:
            return {
                "success": True,
                "pipeline": {
                    "total_opportunities": 0,
                    "total_value": 0,
                    "stages": {},
                    "avg_deal_size": 0
                },
                "message": "Pipeline summary (mock mode)"
            }
        
        try:
            # Get opportunities by stage
            query = """
                SELECT StageName, COUNT(Id) count, SUM(Amount) total
                FROM Opportunity
                WHERE IsClosed = false
                GROUP BY StageName
            """
            result = await self.query(query)
            
            stages = {}
            total_value = 0
            total_count = 0
            
            for record in result.get("records", []):
                stage = record.get("StageName")
                count = record.get("count", 0)
                total = record.get("total", 0) or 0
                
                stages[stage] = {
                    "count": count,
                    "value": total
                }
                total_count += count
                total_value += total
            
            return {
                "success": True,
                "pipeline": {
                    "total_opportunities": total_count,
                    "total_value": total_value,
                    "stages": stages,
                    "avg_deal_size": total_value / total_count if total_count > 0 else 0
                },
                "message": "Pipeline summary retrieved successfully"
            }
        except Exception as e:
            logger.error(f"Failed to get pipeline summary: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Salesforce connection health"""
        self._connect()
        
        if not self._connected:
            return {
                "status": "disconnected",
                "message": "Not connected to Salesforce (credentials not configured or connection failed)"
            }
        
        try:
            # Try a simple query
            result = self._sf.query("SELECT Id FROM User LIMIT 1")
            return {
                "status": "healthy",
                "message": "Connected to Salesforce",
                "org_id": self._sf.sf_instance
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

# Global instance
salesforce_integration = SalesforceIntegration()
