"""
Unit tests for DAG Maintenance Agent
"""

import pytest

from enhanced_adk.governance_agents.dag_maintenance_agent import (
    DAGMaintenanceAgent,
    DependencyNode,
)


class TestDAGMaintenanceAgent:
    """Test suite for DAG Maintenance Agent"""
    
    @pytest.mark.asyncio
    async def test_scan_workspace_success(self, dag_maintenance_agent, mock_filesystem_scan_result):
        """Test successful workspace scanning"""
        # Mock MCP client response
        dag_maintenance_agent.mcp_client.call_tool.return_value = mock_filesystem_scan_result
        
        # Scan workspace
        nodes = await dag_maintenance_agent.scan_workspace("/workspace")
        
        # Verify
        assert len(nodes) == 3
        assert nodes[0].name == "agent.yaml"
        assert nodes[1].name == "bad.yaml"
        
        # Verify MCP client was called
        dag_maintenance_agent.mcp_client.call_tool.assert_called_once_with(
            server="filesystem-mcp",
            tool="scan_directory",
            params={
                "path": "/workspace",
                "pattern": "*.yaml",
                "recursive": True
            }
        )
        
        # Verify metrics
        dag_maintenance_agent.scan_counter.labels.assert_called_with(status='success')
    
    @pytest.mark.asyncio
    async def test_scan_workspace_error(self, dag_maintenance_agent):
        """Test workspace scanning with error"""
        # Mock MCP client to raise error
        dag_maintenance_agent.mcp_client.call_tool.side_effect = Exception("Scan failed")
        
        # Scan workspace should raise error
        with pytest.raises(Exception, match="Scan failed"):
            await dag_maintenance_agent.scan_workspace("/workspace")
        
        # Verify error metric
        dag_maintenance_agent.scan_counter.labels.assert_called_with(status='error')
    
    @pytest.mark.asyncio
    async def test_validate_taxonomy_compliant(self, dag_maintenance_agent, sample_dependency_nodes):
        """Test taxonomy validation with compliant nodes"""
        # Mock taxonomy validation
        dag_maintenance_agent.taxonomy.validate_agent_name.return_value = {
            "valid": True,
            "violations": []
        }
        
        # Validate
        result = await dag_maintenance_agent.validate_taxonomy(sample_dependency_nodes)
        
        # Verify
        assert result.valid is True
        assert len(result.violations) == 0
        
        # Verify taxonomy was called for each node
        assert dag_maintenance_agent.taxonomy.validate_agent_name.call_count == 2
    
    @pytest.mark.asyncio
    async def test_validate_taxonomy_violations(self, dag_maintenance_agent, sample_dependency_nodes):
        """Test taxonomy validation with violations"""
        # Mock taxonomy validation
        dag_maintenance_agent.taxonomy.validate_agent_name.side_effect = [
            {"valid": True, "violations": []},
            {"valid": False, "violations": ["Name must be kebab-case"]}
        ]
        
        # Validate
        result = await dag_maintenance_agent.validate_taxonomy(sample_dependency_nodes)
        
        # Verify
        assert result.valid is False
        assert len(result.violations) == 1
        assert "InvalidName" in result.violations[0]
    
    @pytest.mark.asyncio
    async def test_detect_conflicts_duplicates(self, dag_maintenance_agent):
        """Test conflict detection for duplicate names"""
        nodes = [
            DependencyNode(
                id="node1",
                name="platform-agent-service-v1",
                type="service",
                dependencies=[],
                file_path="/workspace/1.yaml",
                metadata={}
            ),
            DependencyNode(
                id="node2",
                name="platform-agent-service-v1",
                type="service",
                dependencies=[],
                file_path="/workspace/2.yaml",
                metadata={}
            )
        ]
        
        # Detect conflicts
        conflicts = await dag_maintenance_agent.detect_conflicts(nodes)
        
        # Verify
        assert len(conflicts) == 1
        assert conflicts[0].type == "duplicate_name"
        assert conflicts[0].severity == "error"
        assert len(conflicts[0].nodes) == 2
    
    @pytest.mark.asyncio
    async def test_detect_conflicts_taxonomy_drift(self, dag_maintenance_agent):
        """Test conflict detection for taxonomy drift"""
        # Mock taxonomy validation
        dag_maintenance_agent.taxonomy.validate_and_fix.return_value = {
            "fixed": "platform-correct-name-v1",
            "changes": ["Converted to kebab-case"]
        }
        
        nodes = [
            DependencyNode(
                id="node1",
                name="WrongName",
                type="service",
                dependencies=[],
                file_path="/workspace/1.yaml",
                metadata={}
            )
        ]
        
        # Detect conflicts
        conflicts = await dag_maintenance_agent.detect_conflicts(nodes)
        
        # Verify
        assert len(conflicts) == 1
        assert conflicts[0].type == "taxonomy_drift"
        assert conflicts[0].severity == "warning"
    
    @pytest.mark.asyncio
    async def test_auto_repair_success(self, dag_maintenance_agent):
        """Test successful auto-repair"""
        violations = [
            "WrongName: Name must be kebab-case",
            "AnotherBadName: Invalid characters"
        ]
        
        # Mock taxonomy validation
        dag_maintenance_agent.taxonomy.validate_and_fix.side_effect = [
            {"fixed": "correct-name-v1", "changes": ["Converted to kebab-case"]},
            {"fixed": "another-correct-name-v1", "changes": ["Removed invalid characters"]}
        ]
        
        # Repair
        result = await dag_maintenance_agent.auto_repair(violations)
        
        # Verify
        assert result.success is True
        assert len(result.repairs_applied) == 2
        assert len(result.failures) == 0
        assert "correct-name-v1" in result.repairs_applied[0]
    
    @pytest.mark.asyncio
    async def test_auto_repair_failure(self, dag_maintenance_agent):
        """Test auto-repair with failures"""
        violations = [
            "BadName: Cannot be fixed"
        ]
        
        # Mock taxonomy validation to return same name (no fix possible)
        dag_maintenance_agent.taxonomy.validate_and_fix.return_value = {
            "fixed": "BadName",
            "changes": []
        }
        
        # Repair
        result = await dag_maintenance_agent.auto_repair(violations)
        
        # Verify
        assert result.success is False
        assert len(result.repairs_applied) == 0
        assert len(result.failures) == 1
    
    @pytest.mark.asyncio
    async def test_create_repair_pr(self, dag_maintenance_agent):
        """Test creating repair PR"""
        repairs = ["Fixed name1", "Fixed name2"]
        
        # Mock GitHub MCP
        dag_maintenance_agent.mcp_client.call_tool.return_value = {
            "url": "https://github.com/test/pr/42",
            "number": 42
        }
        
        # Create PR
        result = await dag_maintenance_agent.create_repair_pr(repairs, "auto-repair-20240109")
        
        # Verify
        assert result["url"] == "https://github.com/test/pr/42"
        assert result["number"] == 42
        
        # Verify GitHub MCP was called
        dag_maintenance_agent.mcp_client.call_tool.assert_called_once()
        call_args = dag_maintenance_agent.mcp_client.call_tool.call_args
        assert call_args[1]["server"] == "github-mcp"
        assert call_args[1]["tool"] == "create_pr"
        assert call_args[1]["params"]["title"] == "Auto-repair: Taxonomy compliance fixes"
        assert call_args[1]["params"]["branch"] == "auto-repair-20240109"
    
    @pytest.mark.asyncio
    async def test_run_maintenance_cycle_compliant(self, dag_maintenance_agent):
        """Test complete maintenance cycle with no violations"""
        # Mock scan
        dag_maintenance_agent.mcp_client.call_tool.return_value = {"files": []}
        
        # Mock validation
        dag_maintenance_agent.taxonomy.validate_agent_name.return_value = {
            "valid": True,
            "violations": []
        }
        
        # Run cycle
        await dag_maintenance_agent.run_maintenance_cycle()
        
        # Verify
        dag_maintenance_agent.mcp_client.call_tool.assert_called_once()
        # No PR should be created since no violations
    
    @pytest.mark.asyncio
    async def test_run_maintenance_cycle_with_violations(self, dag_maintenance_agent):
        """Test complete maintenance cycle with violations"""
        # Mock scan
        dag_maintenance_agent.mcp_client.call_tool.return_value = {
            "files": ["/workspace/test.yaml"]
        }
        
        # Mock validation with violations
        dag_maintenance_agent.taxonomy.validate_agent_name.return_value = {
            "valid": False,
            "violations": ["Test violation"]
        }
        
        # Mock repair
        dag_maintenance_agent.taxonomy.validate_and_fix.return_value = {
            "fixed": "fixed-name-v1",
            "changes": ["Fixed"]
        }
        
        # Mock PR creation
        dag_maintenance_agent.mcp_client.call_tool.return_value = {
            "url": "https://github.com/test/pr/42",
            "number": 42
        }
        
        # Run cycle
        await dag_maintenance_agent.run_maintenance_cycle()
        
        # Verify multiple MCP calls
        assert dag_maintenance_agent.mcp_client.call_tool.call_count >= 2
    
    def test_generate_repair_report(self, dag_maintenance_agent):
        """Test repair report generation"""
        repairs = ["Fixed name1", "Fixed name2"]
        failures = ["Failed to fix name3"]
        
        report = dag_maintenance_agent._generate_repair_report(repairs, failures)
        
        # Verify
        assert "Auto-Repair Report" in report
        assert "Fixed name1" in report
        assert "Fixed name2" in report
        assert "Failed to fix name3" in report
        assert "2 repairs applied" in report
        assert "1 failures" in report
    
    def test_parse_dependency_file(self, dag_maintenance_agent):
        """Test dependency file parsing"""
        # Mock file read
        dag_maintenance_agent.mcp_client.call_tool.return_value = {
            "content": "test content"
        }
        
        # Parse file
        node = dag_maintenance_agent._parse_dependency_file("/workspace/test.yaml")
        
        # Verify
        assert node is not None
        assert node.id == "test"
        assert node.name == "test"
        assert node.file_path == "/workspace/test.yaml"


class TestDAGMaintenanceAgentFactory:
    """Test factory function for DAG maintenance agent"""
    
    @pytest.mark.asyncio
    async def test_create_dag_maintenance_agent(self, agent_components):
        """Test agent factory function"""
        from enhanced_adk.governance_agents.dag_maintenance_agent import create_dag_maintenance_agent
        
        agent = await create_dag_maintenance_agent(**agent_components)
        
        # Verify
        assert isinstance(agent, DAGMaintenanceAgent)
        assert agent.agent_name == "platform-dag-maintainer-agent-v1"
        assert agent.autonomy_threshold == 0.8